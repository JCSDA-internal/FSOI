"""
This script is an entry point for an AWS Lambda function to download
H5 files from S3 and create plots using existing functions.
"""

import sys
import os
import json
import pandas as pd
from fsoi.web.serverless_tools import hash_request, get_reference_id, create_response_body, \
    create_error_response_body, RequestDao, ApiGatewaySender
from fsoi.stats import lib_obimpact as loi
from fsoi.stats import lib_utils as lutils
from fsoi import log
from fsoi.data.datastore import ThreadedDataStore
from fsoi.data.s3_datastore import S3DataStore

# List to hold errors and warnings encountered during processing
errors = []
warns = []


def handler(request):
    """
    Create a chart as a PNG based on the input parameters
    :param request: Contains request details (validated)
    :return: None - result will be sent via API Gateway Websocket Connection URL
    """
    try:
        # get the request hash
        hash_value = hash_request(request)

        # process the request
        response = process_request(request)

        # send the response to all listeners
        print(json.dumps(response))
        message_all_clients(hash_value, response, sync=True)
    except Exception as e:
        print(e)
        ref_id = get_reference_id(request)
        errors.append('Request processing failed')
        errors.append('Reference ID: %s' % ref_id)
        update_all_clients(hash_request(request), 'FAIL', 'Request processing failed', 0)


def process_request(validated_request):
    """
    Create a chart as a PNG based on the input parameters
    :param validated_request: Contains all of the request details
    :return: JSON response
    """
    # empty the list of errors
    del errors[:]
    del warns[:]

    # compute the hash value and get a reference ID
    hash_value = hash_request(validated_request)
    reference_id = get_reference_id(validated_request)

    # print some debug information to the CloudWatch Logs
    print('Reference ID: %s' % reference_id)
    print('Request hash: %s' % hash_value)
    print('Request:\n%s' % json.dumps(validated_request))

    # track the progress percentage
    progress = 0
    progress_step = int(90/len(validated_request['centers'])/2)

    # download data from S3
    update_all_clients(hash_value, 'RUNNING', 'Accessing data objects', progress)
    objects = download_s3_objects(validated_request)
    progress += 5

    # analyze downloaded data to determine if there were any centers with no
    # data, and remove those centers (if any) from the request and add a warning
    center_counts = {}
    for object in objects:
        if object[1] not in center_counts:
            center_counts[object[1]] = 0
        if object[5]:
            center_counts[object[1]] += 1
    for center in center_counts:
        if center_counts[center] == 0:
            warns.append('No data available for %s' % center)
            validated_request['centers'].remove(center)

    # iterate over each of the requested centers and create plots
    key_list = []
    centers = validated_request['centers']
    for center in centers:
        validated_request['centers'] = [center]
        if not errors:
            prepare_working_dir(validated_request)
        if not errors:
            update_all_clients(hash_value, 'RUNNING', 'Creating plots for %s' % center, progress)
            create_plots(validated_request, center, objects)
            progress += progress_step
        if not errors:
            update_all_clients(hash_value, 'RUNNING', 'Storing plots for %s' % center, progress)
            key_list += cache_summary_plots_in_s3(hash_value, validated_request)
            progress += progress_step

    # restore original list of centers
    validated_request['centers'] = centers

    # create the comparison summary plots
    if not errors:
        update_all_clients(hash_value, 'RUNNING', 'Creating comparison plots', progress)
        process_fsoi_compare(validated_request)
        progress += 3
        update_all_clients(hash_value, 'RUNNING', 'Storing comparison plots', progress)
        key_list += cache_compare_plots_in_s3(hash_value, validated_request)
        progress += 1

    # clean up the working directory
    clean_up(validated_request)

    # restore the request to its original value
    validated_request['centers'] = centers

    # handle success cases
    if not errors:
        update_all_clients(hash_value, 'SUCCESS', 'Done.', 100)
        return create_response_body(key_list, hash_value, warns)

    # handle error cases
    update_all_clients(hash_value, 'FAIL', 'Failed to process request', progress)
    print('Errors:\n%s' % ','.join(errors))
    print('Warnings:\n%s' % ','.join(warns))
    errors.append('Reference ID: ' + reference_id)

    return create_error_response_body(hash_value, errors, warns)


def update_all_clients(req_hash, status_id, message, progress, sync=False):
    """
    Update the DB and send a message to all clients with a new status update
    :param req_hash: The request hash
    :param status_id: [PENDING|RUNNING|SUCCESS|FAIL]
    :param message: Free-form text to be displayed to user
    :param progress: Integer value 0-100; representing percent complete
    :param sync: {bool} Set to True to send messages synchronously, sent asynchronously be default
    :return: None
    """
    # update the DB
    RequestDao.update_status(req_hash, status_id, message, progress)

    # get the latest from the db
    latest = RequestDao.get_request(req_hash)

    # remove the client connection URLs
    if 'connections' in latest:
        latest.pop('connections')

    # send a status message to all clients
    message_all_clients(req_hash, latest)


def message_all_clients(req_hash, message, sync=False):
    """
    Send a message to all clients listening to the request
    :param req_hash: The request hash
    :param message: The message
    :return: Number of clients we attempted to notify
    """
    from concurrent.futures import ThreadPoolExecutor

    # get the latest request from the database
    req = RequestDao.get_request(req_hash)

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


def prepare_working_dir(request):
    """
    Create all of the necessary empty directories
    :param request: {dict} A validated and sanitized request object
    :return: {bool} True=success; False=failure
    """
    try:
        root_dir = request['root_dir']

        required_dirs = [root_dir, root_dir+'/work', root_dir+'/data', root_dir+'/plots/summary',
                         root_dir+'/plots/compare/full', root_dir+'/plots/compare/rad',
                         root_dir+'/plots/compare/conv']
        for center in request['centers']:
            required_dirs.append(root_dir + '/plots/summary/' + center)

        for required_dir in required_dirs:
            if not os.path.exists(required_dir):
                os.makedirs(required_dir)
            elif os.path.isfile(required_dir):
                return False

        return True
    except Exception as e:
        errors.append('Error preparing working directory')
        print(e)
        return False


def clean_up(request):
    """
    Clean up the temporary working directory
    :param request: {dict} A validated and sanitized request object
    :return: None
    """
    import shutil

    root_dir = request['root_dir']

    if root_dir is not None and root_dir != '/':
        try:
            shutil.rmtree(root_dir)
        except FileNotFoundError:
            print('%s not found when cleaning up' % root_dir)


def download_s3_objects(request):
    """
    Download all required objects from S3
    :param request: {dict} A validated and sanitized request object
    :return: {list} A list of lists, where each item in the main list is an object that was expected
                    to be downloaded.  The sub lists contain [s3_key, center, norm, date, cycle,
                    downloaded_boolean, local_file]
    """
    bucket = os.environ['DATA_BUCKET']
    prefix = os.environ['OBJECT_PREFIX']
    data_dir = request['root_dir'] + '/data'

    # get a list of required objects
    objs = get_s3_object_urls(request)

    # create the S3 data store
    datastore = ThreadedDataStore(S3DataStore(), 20)

    # download all the objects using multi-threaded class
    for obj in objs:
        # create the source
        key = obj[0]
        source = {'bucket': bucket, 'prefix': prefix, 'name': key}

        # create the local file name
        local_dir = data_dir+'/'+key[:key.rfind('/')]+'/'
        local_file = key[key.rfind('/')+1:]

        # start the download
        datastore.load_to_local_file(source, local_dir + local_file)

    # wait for downloads to finish
    datastore.join()

    # check that files were downloaded and prepare a response message
    s3msgs = []
    all_data_missing = True
    for obj in objs:
        key = obj[0]

        # create the local file name
        local_dir = data_dir + '/' + key[:key.rfind('/')] + '/'
        local_file = key[key.rfind('/')+1:]

        # check that the file was downloaded
        if not os.path.exists(local_dir + local_file):
            log.warn('Could not download S3 object: s3://%s/%s/%s' % (bucket, prefix, key))
            obj.append(False)
            tokens = key.split('.')
            center = tokens[1]
            norm = tokens[2]
            date = tokens[3][0:8]
            cycle = tokens[3][8:]
            s3msgs.append('Missing data: %s %s %s %sZ' % (center, date, norm, cycle))
        else:
            all_data_missing = False
            obj.append(True)
            obj.append('%s%s' % (local_dir, local_file))

    # put the S3 download messages either into errors or warns
    for msg in s3msgs:
        if all_data_missing:
            errors.append(msg)
        else:
            warns.append(msg)

    return objs


def create_plots(request, center, objects):
    """
    Run the fsoi_summary.py script on the bulk statistics
    :param request: {dict} A validated and sanitized request object
    :param center: {str} Name of the center for which plots should be created
    :param objects: {list} A list of lists, where each item in the main list is an object that was expected
                    to be downloaded.  The sub lists contain [s3_key, center, norm, date, cycle,
                    downloaded_boolean, local_file]  (as returned from @download_s3_objects)
    :return: None
    """
    # create a list of downloaded files for this center
    files = []
    for obj in objects:
        if obj[1] == center and obj[5]:
            files.append(obj[6])

    # read all of the files
    ddf = {}
    for (i, file) in enumerate(files):
        ddf[i] = aggregate_by_platform(lutils.readHDF(file, 'df'))

    # concatenate the group bulk data and save to a pickle
    concatenated = pd.concat(ddf, axis=0)
    pickle_dir = '%s/work/%s/%s' % (request['root_dir'], center, request['norm'])
    pickle_file = '%s/group_stats.pkl' % pickle_dir
    os.makedirs(pickle_dir, exist_ok=True)
    if os.path.exists(pickle_file):
        os.remove(pickle_file)
    lutils.pickle(pickle_file, concatenated)

    # time-average the data frames
    df, df_std = loi.tavg(concatenated, 'PLATFORM')
    df = loi.summarymetrics(df)

    # filter out the platforms that were not in the request
    filter_platforms_from_data(df, request['platforms'])

    # do not continue if all platforms have been removed
    if len(df) == 0:
        warns.append('Selected platforms are unavailable for %s' % center)
        return

    # create the cycle identifier
    cycle_id = ''
    cycle_ints = []
    for c in request['cycles']:
        cycle_id += '%02dZ' % int(c)
        cycle_ints.append(int(c))

    # create the plots
    for qty in ['TotImp', 'ImpPerOb', 'FracBenObs', 'FracNeuObs', 'FracImp', 'ObCnt']:
        try:
            plot_options = loi.getPlotOpt(qty, cycle=cycle_ints, center=center,
                                          savefigure=True, platform=loi.Platforms('OnePlatform'), domain='Global')
            plot_options['figname'] = '%s/plots/summary/%s/%s_%s_%s' % \
                                      (request['root_dir'], center, center, qty, cycle_id)
            loi.summaryplot(df, qty=qty, plotOpt=plot_options, std=df_std)
        except Exception as e:
            log.error('Failed to generate plots for %s' % qty, e)


def aggregate_by_platform(df):
    """
    Aggregate all of the data by platform using the unified platform list (e.g. [MODIS_Wind and
    AMV-MODIS] go under a single index called MODIS Wind).
    :param df: The original data frame, which will be deleted upon successful completion
    :return: {pandas.DataFrame} A new data frame with data aggregated by unified platform list
    """
    # turn the unified platform list inside-out for quick look up
    platform_to_aggregate_map = {}
    unified_platforms = loi.Platforms('OnePlatform')
    for common_platform in unified_platforms:
        for specific_platform in unified_platforms[common_platform]:
            platform_to_aggregate_map[specific_platform] = common_platform
        platform_to_aggregate_map[common_platform] = common_platform

    # iterate through the rows of the data frame and make a new data array
    columns = ['TotImp', 'ObCnt', 'ObCntBen', 'ObCntNeu']
    common_row_map = {}
    for index, row in df.iterrows():
        # get the date/time and specific platform from the index
        dt, specific_platform = index

        # get the common platform name for this row
        if specific_platform in platform_to_aggregate_map:
            common_platform = platform_to_aggregate_map[specific_platform]
        else:
            common_platform = 'Unknown'
            log.warn('Unknown platform: %s' % specific_platform)

        # create the common index
        common_index = (dt, common_platform)

        # get (or create a new) data row for the common platform name
        if common_index not in common_row_map:
            common_row_map[common_index] = [dt, common_platform] + [0] * len(columns)
        common_row = common_row_map[common_index]

        # sum the values from the row with the new common row
        for i in range(len(row)):
            common_row[i+2] += row[i]

    # put the new values into a new values array
    common_values = [common_row_map[common_index][2:] for common_index in common_row_map]

    # create the new index for the common data frame
    common_platform_list = [common_index[1] for common_index in common_row_map]
    levels = [[list(common_row_map)[0][0]], common_platform_list]
    codes = [[0] * len(common_platform_list), list(range(len(common_platform_list)))]
    new_index = pd.MultiIndex(levels=levels, codes=codes, names=['DATETIME', 'PLATFORM'])
    common_df = pd.DataFrame(
        common_values,
        index=new_index,
        columns=columns
    )

    return common_df


def filter_platforms_from_data(df, platforms):
    """
    Filter out platforms that were not requested by the user
    :param df: The summary metrics data frame
    :param request: {str} A comma-separated list of platforms that should be included
    :return: None - 'df' object is modified
    """
    # create a list of all upper case platform present in the request
    included_platforms = []
    for platform in platforms.split(','):
        included_platforms.append(platform.upper())

    # create a list of all platforms present in the data frame, but not the request
    excluded_platforms = []
    case_sensitive_included_platforms = []
    for platform in df.index:
        if platform.upper() not in included_platforms:
            excluded_platforms.append(platform)
        else:
            case_sensitive_included_platforms.append(platform)

    # drop platforms from the data frame that were not in the request
    df.drop(excluded_platforms, inplace=True)

    # update the index (i.e., list of platforms) in the data frame
    df.reindex(case_sensitive_included_platforms)


def process_fsoi_compare(request):
    """
    Run the compare_fsoi.py script on the final statistics
    :param request:
    :return:
    """
    from fsoi.plots.compare_fsoi import compare_fsoi_main

    try:
        sys.argv = [
            'script',
            '--rootdir',
            request['root_dir'],
            '--centers']
        sys.argv += request['centers']
        sys.argv += [
            '--norm',
            request['norm'],
            '--savefigure',
            '--cycle'
        ]
        sys.argv += request['cycles']
        sys.argv += [
            '--platform',
            request['platforms']
        ]

        print('running compare_fsoi_main: %s' % ' '.join(sys.argv))
        compare_fsoi_main()
    except Exception as e:
        log.error('Failed to create comparison plots')
        warns.append('Error creating FSOI comparison plots')


def dates_in_range(start_date, end_date):
    """
    Get a list of dates in the range
    :param start_date: {str} yyyyMMdd
    :param end_date:  {str} yyyyMMdd
    :return: {list} List of dates in the given range (inclusive)
    """
    from datetime import datetime as dt

    start_year = int(start_date[0:4])
    start_month = int(start_date[4:6])
    start_day = int(start_date[6:8])
    start = dt(start_year, start_month, start_day)
    s = int(start.timestamp())

    end_year = int(end_date[0:4])
    end_month = int(end_date[4:6])
    end_day = int(end_date[6:8])
    end = dt(end_year, end_month, end_day)
    e = int(end.timestamp())

    dates = []
    for ts in range(s, e + 1, 86400):
        d = dt.utcfromtimestamp(ts)
        dates.append('%04d%02d%02d' % (d.year, d.month, d.day))

    return dates


def get_s3_object_urls(request):
    """
    Get a list of the S3 object URLs required to complete this request
    :param request: {dict} A validated and sanitized request object
    :return: {list} A list of objects expected to be downloaded, where each item in the list is
                    a list containing [s3_key, center, norm, date, cycle].
    """
    start_date = request['start_date']
    end_date = request['end_date']
    centers = request['centers']
    norms = request['norm']
    cycles = request['cycles']

    # create a list of norm values
    norms = ['dry', 'moist'] if norms == 'both' else [norms]

    s3_objects = []
    for date in dates_in_range(start_date, end_date):
        for center in centers:
            for cycle in cycles:
                for norm in norms:
                    s3_objects.append([
                        '%s/groupbulk.%s.%s.%s%02d.h5' % (center, center, norm, date, int(cycle)),
                        center,
                        norm,
                        date,
                        cycle]
                    )

    return s3_objects


def cache_compare_plots_in_s3(hash_value, request):
    """
    Copy all of the new comparison plots to S3
    :param hash_value: {str} The hash value of the request
    :param request: {dict} The full request
    :return: None
    """
    # retrieve relevant environment variables
    bucket = os.environ['CACHE_BUCKET']
    root_dir = request['root_dir']
    img_dir = root_dir + '/plots/compare/full'

    # list of files to cache
    files = [
        img_dir + '/ImpPerOb___CYCLE__.png',
        img_dir + '/FracImp___CYCLE__.png',
        img_dir + '/ObCnt___CYCLE__.png',
        img_dir + '/TotImp___CYCLE__.png',
        img_dir + '/FracNeuObs___CYCLE__.png',
        img_dir + '/FracBenObs___CYCLE__.png'
    ]

    # create the S3 data store
    datastore = ThreadedDataStore(S3DataStore(), 20)

    # create the cycle identifier
    cycle = ''
    for c in request['cycles']:
        cycle += '%02dZ' % int(c)

    # loop through all centers and files
    key_list = []
    for file in files:
        # replace the center in the file name
        filename = file.replace('__CYCLE__', cycle)
        if os.path.exists(filename):
            print('Uploading %s to S3...' % filename)
            key = hash_value + '/comparefull_' + filename[filename.rfind('/') + 1:]
            datastore.save_from_local_file(filename, {'bucket': bucket, 'key': key})
            key_list.append(key)

    # wait for the uploads to finish
    datastore.join()

    return key_list


def cache_summary_plots_in_s3(hash_value, request):
    """
    Copy all of the new summary plots to S3
    :param hash_value: {str} The hash value of the request
    :param request: {dict} The full request
    :return: {list} A list of object keys for images in the S3 cache bucket
    """
    # retrieve relevant environment variables
    bucket = os.environ['CACHE_BUCKET']
    root_dir = request['root_dir']
    img_dir = root_dir + '/plots/summary'

    # list of files to cache
    files = [
        img_dir + '/__CENTER__/__CENTER___ImpPerOb___CYCLE__.png',
        img_dir + '/__CENTER__/__CENTER___FracImp___CYCLE__.png',
        img_dir + '/__CENTER__/__CENTER___ObCnt___CYCLE__.png',
        img_dir + '/__CENTER__/__CENTER___TotImp___CYCLE__.png',
        img_dir + '/__CENTER__/__CENTER___FracNeuObs___CYCLE__.png',
        img_dir + '/__CENTER__/__CENTER___FracBenObs___CYCLE__.png'
    ]

    # create the S3 data store
    datastore = ThreadedDataStore(S3DataStore(), 20)

    # create the cycle identifier
    cycle = ''
    for c in request['cycles']:
        cycle += '%02dZ' % int(c)

    # loop through all centers and files
    key_list = []
    for center in request['centers']:
        for file in files:
            # replace the center in the file name
            filename = file.replace('__CENTER__', center).replace('__CYCLE__', cycle)
            if os.path.exists(filename):
                print('Uploading %s to S3...' % filename)
                key = hash_value + '/' + filename[filename.rfind('/') + 1:]
                datastore.save_from_local_file(filename, {'bucket': bucket, 'key': key})
                key_list.append(key)

    # an empty list of S3 keys indicates that no plots were uploaded or generated
    if not key_list:
        # TODO: Remove this once we have conventional platforms available for GMAO, the following
        #  line should be removed.  This is a hack so that we do not error out when all conventional
        #  platforms may have been removed, but there may be valuable plots generated from other
        #  parameters in the request.
        if 'Conventional data plots are temporarily unavailable for GMAO' not in warns:
            errors.append('Failed to generate plots')

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
    handler(global_request)


if __name__ == '__main__':
    main()
