"""
This script is an entry point for an AWS Lambda function to download
H5 files from S3 and create plots using existing functions.
"""

import os
import copy
import json
import boto3
from concurrent.futures import ThreadPoolExecutor, Future
from fsoi.web.data import RequestDao, ApiGatewaySender
from fsoi import log
from fsoi.data.datastore import ThreadedDataStore
from fsoi.data.s3_datastore import S3DataStore
from fsoi.plots.managers import SummaryPlotGenerator, ComparisonPlotGenerator


class Handler:
    """
    Base class for a request handler
    """
    def __init__(self):
        self.hash_value = None

    @staticmethod
    def hash_request(request):
        """
        Create a hash of the request data
        :param request: {dict} A validated and sanitized request object
        :return:
        """
        import json
        import base64
        import hashlib

        if 'cache_id' in request:
            return request['cache_id']

        req_str = json.dumps(request)
        hasher = hashlib.sha256()
        hasher.update(req_str.encode('utf-8'))
        return base64.b16encode(hasher.digest()).decode()

    @staticmethod
    def get_reference_id(request):
        """
        Get a reference ID - unique marker can be used in a log
        file and passed to user in case of an error
        :param request: The request value
        :return:
        """
        from datetime import datetime as dt
        import time
        d = dt.utcfromtimestamp(time.time())
        hash_bit = Handler.hash_request(request)[:6]
        date_bit = '%04d-%02d-%02dT%02d:%02d:%02d' % \
                   (d.year, d.month, d.day, d.hour, d.minute, d.second)

        return '%s_%s' % (hash_bit, date_bit)

    def _update_all_clients(self, status_id, message, progress, sync=False):
        """
        Update the DB and send a message to all clients with a new status update
        :param status_id: [PENDING|RUNNING|SUCCESS|FAIL]
        :param message: Free-form text to be displayed to user
        :param progress: Integer value 0-100; representing percent complete
        :param sync: {bool} Set to True to send messages synchronously, sent asynchronously be default
        :return: None
        """
        # update the DB
        RequestDao.update_status(self.hash_value, status_id, message, progress)

        # get the latest from the db
        latest = RequestDao.get_request(self.hash_value)

        # remove the client connection URLs
        if 'connections' in latest:
            latest.pop('connections')

        # send a status message to all clients
        self._message_all_clients(latest, sync)

    def _message_all_clients(self, message, sync=False):
        """
        Send a message to all clients listening to the request
        :param message: The message
        :param sync: {bool} Set to True to send messages synchronously, sent asynchronously be default
        :return: Number of clients we attempted to notify
        """
        # get the latest request from the database
        req = RequestDao.get_request(self.hash_value)

        # make sure the message is a string and not a dictionary
        if isinstance(message, dict):
            message = json.dumps(message)

        # count the number of clients that were sent messages
        sent = 0

        # send all of the clients a message asynchronously
        futures = []
        thread_pool = ThreadPoolExecutor(max_workers=20)
        if 'connections' in req:
            for url in req['connections']:
                future = thread_pool.submit(ApiGatewaySender.send_message_to_ws_client, url, message)
                futures.append(future)
                sent += 1

        # if the caller wants to wait for messages to be sent, then wait for the threads to finish
        if sync:
            for future in futures:
                future.result()

        # return the number of messages sent
        return sent

    def _cache_file_list_in_s3(self, datastore, files, descriptors):
        """
        Save the list of files in S3
        :param datastore: {DataStore} An FSOI data store object
        :param files: {list} List of strings of full file path
        :param descriptors: {list} Append descriptors to this list
        :return: None
        """
        # retrieve relevant environment variables
        bucket = os.environ['CACHE_BUCKET']

        for file in files:
            name = file.split('/')[-1]
            descriptor = {'bucket': bucket, 'prefix': self.hash_value, 'name': name}
            descriptors.append(descriptor)
            datastore.save_from_local_file(file, descriptor)


class FullRequestHandler(Handler):
    """
    A class to handle a full request and/or a partial request for a single center as part of a full request.
    """
    def __init__(self, request, plot_util='bokeh', parallel_type='local', lambda_function_name=None):
        """
        Create the handler with the request
        :param request: {dict} Request object
        :param plot_util: {str} Specify which plotting utility to use for this request: 'bokeh' or 'matplotlib'
        :param parallel_type: {str} May be either 'local' or 'lambda'
        :param lambda_function_name: {str} Name of this lambda function
        """
        # call the super constructor
        super().__init__()

        # copy the request object
        self.request = copy.deepcopy(request)

        # get the name of the current lambda function
        self.lambda_function_name = lambda_function_name

        # compute the hash value and get a reference ID
        self.hash_value = self.hash_request(self.request)
        self.ref_id = self.get_reference_id(self.request)

        # empty arrays to hold warnings and errors
        self.warns = []
        self.errors = []

        # save the plotting utility to use
        if plot_util not in ['bokeh', 'matplotlib']:
            raise ValueError('Invalid value for plot_util must be either bokeh or matplotlib: %s' % plot_util)
        self.plot_util = plot_util

        # validate and store the parallel type value
        if parallel_type not in ['local', 'lambda']:
            raise ValueError('Invalid value for parallel_type must be either local or lambda: %s' % parallel_type)
        self.parallel_type = parallel_type

        # thread pool for lambda invocations
        if self.parallel_type == 'local':
            self.executor = ThreadPoolExecutor(max_workers=1)
        else:
            self.executor = ThreadPoolExecutor(max_workers=10)

        # summary and comparison plot descriptors
        self.plot_descriptors = []
        self.json_descriptors = []

    def __getstate__(self):
        """
        Serialize the object
        :return: {dict} Data representing this object
        """
        return {
            'request': self.request,
            'hash_value': self.hash_value,
            'ref_id': self.ref_id,
            'warns': self.warns,
            'errors': self.errors,
            'plot_util': self.plot_util,
            'parallel_type': self.parallel_type,
            'pickle_descriptors': self.pickle_descriptors
        }

    def __setstate__(self, state):
        """
        Serialize the object
        :param state: {dict} New state to set
        :return: None
        """
        self.request = state['request']
        self.hash_value = state['hash_value']
        self.ref_id = state['ref_id']
        self.warns = state['warns']
        self.errors = state['errors']
        self.plot_util = state['plot_util']
        self.parallel_type = state['parallel_type']
        self.pickle_descriptors = state['pickle_descriptors']

    def run(self):
        """
        Create a chart as a PNG based on the input parameters
        :return: None - result will be sent via API Gateway Websocket Connection URL
        """
        try:
            # process the request
            self._process_request()
        except Exception as e:
            log.error('Failed to process request')
            ref_id = self.get_reference_id(self.request)
            self.errors.append('Request processing failed')
            self.errors.append('Reference ID: %s' % ref_id)
            self._update_all_clients('FAIL', 'Request processing failed', 0)
            raise e

    def _process_request(self):
        """
        Create a chart as a PNG based on the input parameters
        :return: JSON response
        """
        # log the request information
        log.info('Reference ID: %s' % self.ref_id)
        log.info('Request hash: %s' % self.hash_value)
        log.info('Request:\n%s' % json.dumps(self.request))

        try:
            # track the progress percentage
            progress = 0
            self._update_all_clients('RUNNING', 'Starting request processing', progress)

            # create and run all of the partial requests
            part_handlers = self._run_partial_requests()

            # aggregate results from partial requests
            pickle_descriptors = []
            for part_handler in part_handlers:
                pickle_descriptors += part_handler.pickle_descriptors

            # download the pickle files
            pickles = self._download_pickles(pickle_descriptors)

            # create the comparison summary plots
            cpg = ComparisonPlotGenerator(
                self.request['centers'],
                self.request['norm'],
                [int(c) for c in self.request['cycles']],
                self.request['platforms'],
                self.plot_util,
                pickles
            )
            cpg.create_plot_set()
            self._cache_compare_plots_in_s3(cpg)

            # clean up the working directory
            cpg.clean_up()

            # handle success cases
            if not self.errors:
                self._update_all_clients('SUCCESS', 'Done.', 100)
                return

            # handle error cases
            self._update_all_clients('FAIL', 'Failed to process request', progress)
            log.info('Errors:\n%s' % ','.join(self.errors))
            log.info('Warnings:\n%s' % ','.join(self.warns))
            self.errors.append('Reference ID: ' + self.ref_id)

        except Exception as e:
            log.error('Failed to process request: %s' % self.hash_value)
            log.error(e)

    def _download_pickles(self, pickle_descriptors):
        """
        Download pickle files
        :param pickle_descriptors: {list} List of pickle descriptors
        :return: {list} List of local files
        """
        datastore = ThreadedDataStore(S3DataStore(), 20)
        local_dir = self.request['root_dir']
        files = []
        for pickle_descriptor in pickle_descriptors:
            file = '%s/%s' % (local_dir, pickle_descriptor['name'])
            datastore.load_to_local_file(pickle_descriptor, file)
            files.append(file)

        return files

    def _run_partial_requests(self):
        """
        Create and run all of the partial requests
        :return: {list} List of PartialRequestHandlers
        """
        # create and run a partial request for each center
        futures = []
        centers = self.request['centers']
        for center in centers:
            part_req = copy.deepcopy(self.request)
            part_req['centers'] = [center]
            part_req['is_partial'] = True
            part_req['hash_value'] = self.hash_value
            part_req['ref_id'] = self.ref_id
            part_handler = PartialRequestHandler(part_req, plot_util=self.plot_util)
            futures.append(self._submit_partial_request(part_handler))

        # get the completed partial handlers
        part_handlers = []
        for future in futures:
            part_handler = self._get_partial_handler_from_future(future)
            part_handlers.append(part_handler)

        return part_handlers

    def _retrieve_pickles(self, part_handler):
        """
        Download pickles from S3 for a request
        :param part_handler: {PartialRequestHandler} Partial request handler
        :return: {list} A list of pickles
        """
        # pull out the root directory for easy access
        root_dir = self.request['root_dir']

        # list of downloaded pickles
        pickles = []

        # download the pickles needed for the comparison plots
        data_store = S3DataStore()
        for pickle_source in part_handler.pickle_descriptors:
            file = '%s/pickles/%s' % (root_dir, pickle_source['name'])
            data_store.load_to_local_file(pickle_source, file)
            pickles.append(file)

        return pickles

    def _submit_partial_request(self, part_handler):
        """
        Submit a new partial request
        :param part_handler: {fsoi.web.request_handler.Handler} The partial request handler
        :return: {concurrent.futures.Future} A future for the partial request
        """
        if self.parallel_type == 'local':
            return self.executor.submit(part_handler.run)

        if self.parallel_type == 'lambda':
            lbd = boto3.client('lambda')
            req2 = copy.deepcopy(part_handler.request)
            req2['cycles'] = ','.join(req2['cycles'])
            req2['centers'] = ','.join(req2['centers'])
            req_str = json.dumps(req2)
            payload = json.dumps(
                {
                    'body': req_str,
                    'requestContext': {
                        'domainName': '....',
                        'stage': 'v1',
                        'connectionId': 'none'
                    }
                }
            ).encode()
            return self.executor.submit(
                lbd.invoke,
                FunctionName=self.lambda_function_name,
                InvocationType='RequestResponse',
                LogType='None',
                Payload=payload
            )

    @staticmethod
    def _get_partial_handler_from_future(future: Future):
        """
        Get a PartialRequestHandler object from a Future
        :param future: The result of a partial request handler execution
        :return: {PartialRequestHandler} Executed PRH
        """
        dummy = {'centers':[''], 'hash_value': '', 'ref_id': '', 'is_partial': True}
        part_handler = PartialRequestHandler(dummy)
        part_handler.__setstate__(future.result())
        return part_handler

    def _cache_compare_plots_in_s3(self, plot_gen):
        """
        Copy all of the new comparison plots to S3
        :param plot_gen: {ComparisonPlotGenerator} plot generator that has already been executed
        :return: None
        """
        # create the S3 data store
        datastore = ThreadedDataStore(S3DataStore(), 20)

        # store the summary plots, comparison pickles, and maybe json files (if using bokeh)
        self._cache_file_list_in_s3(datastore, plot_gen.plots, self.plot_descriptors)
        if 'bokeh' == self.plot_util:
            self._cache_file_list_in_s3(datastore, plot_gen.json_data, self.json_descriptors)

        # wait for the datastore to finish uploading files
        datastore.join()


class PartialRequestHandler(Handler):
    """
    A class to handle a full request and/or a partial request for a single center as part of a full request.
    """
    def __init__(self, request, plot_util='bokeh'):
        """
        Create the handler with the request
        :param request: {dict} Request object
        :param plot_util: {str} Specify which plotting utility to use for this request: 'bokeh' or 'matplotlib'
        """
        # call the super constructor
        super().__init__()

        # copy the request object
        self.request = copy.deepcopy(request)

        # get the center name for easy access
        self.center = self.request['centers'][0]

        # get the hash value and reference ID from the partial request
        self.hash_value = self.request['hash_value']
        self.ref_id = self.request['ref_id']

        # empty arrays to hold warnings and errors
        self.warns = []
        self.errors = []

        # save the plotting utility to use
        if plot_util not in ['bokeh', 'matplotlib']:
            raise ValueError('Invalid value for plot_util must be either bokeh or matplotlib: %s' % plot_util)
        self.plot_util = plot_util

        # empty list for data descriptors
        self.pickle_descriptors = []
        self.plot_descriptors = []
        self.json_descriptors = []

    def __getstate__(self):
        """
        Serialize the object
        :return: {dict} Data representing this object
        """
        return {
            'center': self.center,
            'request': self.request,
            'hash_value': self.hash_value,
            'ref_id': self.ref_id,
            'warns': self.warns,
            'errors': self.errors,
            'plot_util': self.plot_util,
            'pickle_descriptors': self.pickle_descriptors,
            'plot_descriptors': self.plot_descriptors,
            'json_descriptors': self.json_descriptors
        }

    def __setstate__(self, state):
        """
        Serialize the object
        :param state: {dict} New state to set
        :return: None
        """
        self.center = state['center']
        self.request = state['request']
        self.hash_value = state['hash_value']
        self.ref_id = state['ref_id']
        self.warns = state['warns']
        self.errors = state['errors']
        self.plot_util = state['plot_util']
        self.pickle_descriptors = state['pickle_descriptors']
        self.plot_descriptors = state['plot_descriptors']
        self.json_descriptors = state['json_descriptors']

    def run(self):
        """
        Create a chart as a PNG based on the input parameters
        :return: None - result will be sent via API Gateway Websocket Connection URL
        """
        try:
            # process the request
            self._process_request()

            # return a representation of this object's state
            return self.__getstate__()
        except Exception as e:
            log.error('Failed to process partial request')
            self.errors.append('Failed to create plots for %s' % self.center)
            raise e

    def _process_request(self):
        """
        Create plots for a single center
        :return: {str} JSON response
        """
        # log the request information
        log.info('Reference ID: %s+%s' % (self.ref_id, self.center))
        log.info('Request hash: %s' % self.hash_value)
        log.info('Request:\n%s' % json.dumps(self.request))

        try:
            # create the plots
            plot_gen = SummaryPlotGenerator(
                self.request['start_date'],
                self.request['end_date'],
                self.request['centers'][0],
                self.request['norm'],
                self.request['cycles'],
                self.request['platforms'],
                self.plot_util
            )
            plot_gen.create_plot_set()

            # store the summary plots
            self._cache_data_in_s3(plot_gen)

        except Exception as e:
            log.error('Failed to process partial request: %s' % self.hash_value, e)
            self.errors.append('Failed to process request for %s' % self.center)

        return self

    def _cache_data_in_s3(self, plot_gen):
        """
        Copy all of the new summary plots to S3
        :param plot_gen: {SummaryPlotGenerator} Plot generator that has already been executed
        :return: None
        """
        # create the S3 data store
        datastore = ThreadedDataStore(S3DataStore(), 20)

        # store the summary plots, comparison pickles, and maybe json files (if using bokeh)
        self._cache_file_list_in_s3(datastore, plot_gen.plots, self.plot_descriptors)
        self._cache_file_list_in_s3(datastore, plot_gen.pickles, self.pickle_descriptors)
        if 'bokeh' == self.plot_util:
            self._cache_file_list_in_s3(datastore, plot_gen.json_data, self.json_descriptors)

        # wait for the datastore to finish uploading files
        datastore.join()
