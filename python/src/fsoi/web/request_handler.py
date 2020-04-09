"""
This script is an entry point for an AWS Lambda function to download
H5 files from S3 and create plots using existing functions.
"""

import sys
import os
import copy
import json
import pandas as pd
import boto3
import base64
from concurrent.futures import ProcessPoolExecutor, wait, ThreadPoolExecutor
from fsoi.web.serverless_tools import hash_request, get_reference_id, create_response_body, \
    create_error_response_body, RequestDao, ApiGatewaySender
from fsoi.stats import lib_obimpact as loi
from fsoi.stats import lib_utils as lutils
from fsoi import log
from fsoi.data.datastore import ThreadedDataStore
from fsoi.data.s3_datastore import S3DataStore, FsoiS3DataStore
from fsoi.plots.summary_fsoi import bokehsummaryplot, matplotlibsummaryplot


class Handler:
    """
    A class to handle a full request and/or a partial request for a single center as part of a full request.
    """
    def __init__(self, request, plot_util='bokeh', parallel_type='local'):
        """
        Create the handler with the request
        :param request: {dict} Request object
        :param plot_util: {str} Specify which plotting utility to use for this request: 'bokeh' or 'matplotlib'
        """
        # copy the request object
        self.request = copy.deepcopy(request)

        # get the request hash value and the reference ID based on the type of request (partial or full)
        if 'is_partial' not in self.request or not self.request['is_partial']:
            # compute the hash value and get a reference ID
            self.hash_value = hash_request(self.request)
            self.ref_id = get_reference_id(self.request)
        else:
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

        # save the parallel type
        if parallel_type not in ['local', 'lambda']:
            raise ValueError('Invalid value for parallel_type must be either local or lambda: %s' % parallel_type)
        self.parallel_type = parallel_type

        # create the process pool executor
        self.executor = ThreadPoolExecutor(max_workers=1)

        # placeholder for the response
        self.response = {}

        # empty list for pickle descriptors
        self.pickle_descriptors = []

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
            'response': self.response,
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
        self.response = state['response']
        self.pickle_descriptors = state['pickle_descriptors']

    def run(self):
        """
        Create a chart as a PNG based on the input parameters
        :return: None - result will be sent via API Gateway Websocket Connection URL
        """
        try:
            # process the request
            if 'is_partial' in self.request and self.request['is_partial']:
                response = self.process_partial_request()
            else:
                response = self.process_full_request()

            # send the response to all listeners
            log.info(json.dumps(response))
            self._message_all_clients(response, sync=True)

            # return the object state
            return self
        except Exception as e:
            log.error('Failed to process request')
            ref_id = get_reference_id(self.request)
            self.errors.append('Request processing failed')
            self.errors.append('Reference ID: %s' % ref_id)
            self._update_all_clients('FAIL', 'Request processing failed', 0)
            raise e

    def process_full_request(self):
        """
        Create a chart as a PNG based on the input parameters
        :return: JSON response
        """
        # log the request information
        log.info('Reference ID: %s' % self.ref_id)
        log.info('Request hash: %s' % self.hash_value)
        log.info('Request:\n%s' % json.dumps(self.request))

        # track the progress percentage
        progress = 0
        self._update_all_clients('RUNNING', 'Creating plots', progress)

        # create and run a partial request for each center
        futures = []
        part_handlers = []
        centers = self.request['centers']
        for center in centers:
            part_req = copy.deepcopy(self.request)
            part_req['centers'] = [center]
            part_req['is_partial'] = True
            part_req['hash_value'] = self.hash_value
            part_req['ref_id'] = self.ref_id
            part_handler = Handler(part_req)
            part_handlers.append(part_handler)
            futures.append(self._submit_partial_request(part_handler))

        # aggregate results from responses
        key_list = []
        for future in futures:
            part_handler = future.result()
            self.errors += part_handler.errors
            self.warns += part_handler.warns
            part_response = json.loads(part_handler.response)
            key_list += [image['key'] for image in part_response['images']]

            # download the pickles needed for the comparison plots
            data_store = S3DataStore()
            for pickle_source in part_response['pickles']:
                pickle_loaded = data_store.load_to_local_file(pickle_source, pickle_source['file'])
                if not pickle_loaded:
                    log.warn('Failed to load pickle: %s -> %s' %
                             (data_store.descriptor_to_string(pickle_source), pickle_source['file']))

        # create the comparison summary plots
        if not self.errors:
            self._update_all_clients('RUNNING', 'Creating comparison plots', progress)
            self._process_fsoi_compare()
            progress += 3
            self._update_all_clients('RUNNING', 'Storing comparison plots', progress)
            key_list += self._cache_compare_plots_in_s3()
            progress += 1

        # clean up the working directory
        self._clean_up()

        # handle success cases
        if not self.errors:
            self._update_all_clients('SUCCESS', 'Done.', 100)
            return create_response_body(key_list, self.hash_value, self.warns, self.errors)

        # handle error cases
        self._update_all_clients('FAIL', 'Failed to process request', progress)
        print('Errors:\n%s' % ','.join(self.errors))
        print('Warnings:\n%s' % ','.join(self.warns))
        self.errors.append('Reference ID: ' + self.ref_id)

        return create_error_response_body(self.hash_value, self.errors, self.warns)

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
            # ctx = base64.b64encode(json.dumps({'domainName': 'a','stage': 's','connectionId': 'c'}).encode()).decode()
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
                FunctionName='ios_request_handlerbeta',
                InvocationType='RequestResponse',
                # ClientContext=ctx,
                LogType='None',
                Payload=payload
            )

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

    def _clean_up(self):
        """
        Clean up the temporary working directory
        :return: None
        """
        import shutil

        root_dir = self.request['root_dir']

        if root_dir is not None and root_dir != '/':
            try:
                shutil.rmtree(root_dir)
            except FileNotFoundError:
                print('%s not found when cleaning up' % root_dir)

    def _process_fsoi_compare(self):
        """
        Run the compare_fsoi.py script on the final statistics
        :return: None, results are written to a file based on the request
        """
        from fsoi.plots.compare_fsoi import compare_fsoi_main

        try:
            sys.argv = [
                'script',
                '--rootdir',
                self.request['root_dir'],
                '--centers']
            sys.argv += self.request['centers']
            sys.argv += [
                '--norm',
                self.request['norm'],
                '--savefigure',
                '--cycle'
            ]
            sys.argv += self.request['cycles']
            sys.argv += [
                '--platform',
                self.request['platforms']
            ]

            print('running compare_fsoi_main: %s' % ' '.join(sys.argv))
            compare_fsoi_main()
        except Exception as e:
            log.error('Failed to create comparison plots')
            self.warns.append('Error creating FSOI comparison plots')

    def _cache_compare_plots_in_s3(self):
        """
        Copy all of the new comparison plots to S3
        :return: None
        """
        # retrieve relevant environment variables
        bucket = os.environ['CACHE_BUCKET']
        root_dir = self.request['root_dir']
        img_dir = root_dir + '/plots/compare/full'

        # list of files to cache
        files = [
            img_dir + '/ImpPerOb___CYCLE__.__EXT__',
            img_dir + '/FracImp___CYCLE__.__EXT__',
            img_dir + '/ObCnt___CYCLE__.__EXT__',
            img_dir + '/TotImp___CYCLE__.__EXT__',
            img_dir + '/FracNeuObs___CYCLE__.__EXT__',
            img_dir + '/FracBenObs___CYCLE__.__EXT__'
        ]
        exts = ['png', 'json']

        # create the S3 data store
        datastore = ThreadedDataStore(S3DataStore(), 20)

        # create the cycle identifier
        cycle = ''
        for c in self.request['cycles']:
            cycle += '%02dZ' % int(c)

        # loop through all centers and files
        key_list = []
        for file in files:
            for ext in exts:
                # replace the center in the file name
                filename = file.replace('__CYCLE__', cycle).replace('__EXT__', ext)
                if os.path.exists(filename):
                    print('Uploading %s to S3...' % filename)
                    key = self.hash_value + '/comparefull_' + filename[filename.rfind('/') + 1:]
                    datastore.save_from_local_file(filename, {'bucket': bucket, 'key': key})
                    key_list.append(key)

        # wait for the uploads to finish
        datastore.join()

        return key_list

    def _cache_summary_plots_in_s3(self):
        """
        Copy all of the new summary plots to S3
        :return: {list} A list of object keys for images in the S3 cache bucket
        """
        # retrieve relevant environment variables
        bucket = os.environ['CACHE_BUCKET']
        root_dir = self.request['root_dir']
        img_dir = root_dir + '/plots/summary'

        # list of files to cache
        files = [
            img_dir + '/__CENTER__/__CENTER___ImpPerOb___CYCLE__.__EXT__',
            img_dir + '/__CENTER__/__CENTER___FracImp___CYCLE__.__EXT__',
            img_dir + '/__CENTER__/__CENTER___ObCnt___CYCLE__.__EXT__',
            img_dir + '/__CENTER__/__CENTER___TotImp___CYCLE__.__EXT__',
            img_dir + '/__CENTER__/__CENTER___FracNeuObs___CYCLE__.__EXT__',
            img_dir + '/__CENTER__/__CENTER___FracBenObs___CYCLE__.__EXT__'
        ]

        # create the S3 data store
        datastore = ThreadedDataStore(S3DataStore(), 20)

        # create the cycle identifier
        cycle = ''
        for c in self.request['cycles']:
            cycle += '%02dZ' % int(c)

        # loop through all centers and files
        key_list = []
        for center in self.request['centers']:
            for file in files:
                for ext in ['png', 'json']:
                    # replace the center, cycle, and extension in the file name
                    filename = file.replace('__CENTER__', center).replace('__CYCLE__', cycle).replace('__EXT__', ext)
                    if os.path.exists(filename):
                        print('Uploading %s to S3...' % filename)
                        key = self.hash_value + '/' + filename[filename.rfind('/') + 1:]
                        datastore.save_from_local_file(filename, {'bucket': bucket, 'key': key})
                        key_list.append(key)

        # an empty list of S3 keys indicates that no plots were uploaded or generated
        if not key_list:
            # TODO: Remove this once we have conventional platforms available for GMAO, the following
            #  line should be removed.  This is a hack so that we do not error out when all conventional
            #  platforms may have been removed, but there may be valuable plots generated from other
            #  parameters in the request.
            if 'Conventional data plots are temporarily unavailable for GMAO' not in self.warns:
                self.errors.append('Failed to generate plots')

        # wait for the uploads to finish
        datastore.join()

        return key_list


def main():
    """
    Main function from the command line
    :return: None
    """
    print('args:')
    for arg in sys.argv:
        print(arg)
    global_request = json.loads(sys.argv[1])
    handler = Handler(global_request)
    handler.run()


if __name__ == '__main__':
    main()
