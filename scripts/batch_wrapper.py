"""
This script is an entry point for an AWS Lambda function to download
H5 files from S3 and create plots using existing functions.
"""
import sys
import os
import json
import boto3
from serverless_tools import hash_request, get_reference_id, create_response_body, \
    create_error_response_body, RequestDao, ApiGatewaySender

# Add various paths
sys.path.extend(['/'])

# List to hold errors encountered during processing
errors = []


def main(request):
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
        message_all_clients(hash_value, response)
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

    # compute the hash value and get a reference ID
    hash_value = hash_request(validated_request)
    reference_id = get_reference_id(validated_request)

    # print some debug information to the CloudWatch Logs
    print('Reference ID: %s' % reference_id)
    print('Request hash: %s' % hash_value)
    print('Request:\n%s' % json.dumps(validated_request))

    # download data from S3
    update_all_clients(hash_value, 'RUNNING', 'Accessing data objects', 27)
    download_s3_objects(validated_request)

    # iterate over each of the requested centers
    key_list = []
    centers = validated_request['centers']
    for center in centers:
        validated_request['centers'] = [center]
        if not errors:
            prepare_working_dir(validated_request)
        if not errors:
            update_all_clients(hash_value, 'RUNNING', 'Processing bulk stats for %s' % center, 27)
            process_bulk_stats(validated_request)
        if not errors:
            update_all_clients(hash_value, 'RUNNING', 'Processing FSOI summary for %s' % center, 27)
            process_fsoi_summary(validated_request)
        if not errors:
            update_all_clients(hash_value, 'RUNNING', 'Storing images for %s' % center, 27)
            key_list = cache_summary_plots_in_s3(hash_value, validated_request)
    clean_up(validated_request)
    validated_request['centers'] = centers

    # handle success cases
    if not errors:
        update_all_clients(hash_value, 'SUCCESS', 'Done.', 100)
        return create_response_body(key_list, hash_value)

    # handle error cases
    update_all_clients(hash_value, 'FAIL', 'Failed to process request', 27)
    print('Errors:\n%s' % ','.join(errors))
    errors.append('Reference ID: ' + reference_id)

    return create_error_response_body(errors)


def update_all_clients(req_hash, status_id, message, progress):
    """
    Update the DB and send a message to all clients with a new status update
    :param req_hash: The request hash
    :param status_id: [PENDING|RUNNING|SUCCESS|FAIL]
    :param message: Free-form text to be displayed to user
    :param progress: Integer value 0-100; representing percent complete
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


def message_all_clients(req_hash, message):
    """
    Send a message to all clients listening to the request
    :param req_hash: The request hash
    :param message: The message
    :return: Number of clients notified
    """
    req = RequestDao.get_request(req_hash)

    # make sure the message is a string and not a dictionary
    if isinstance(message, dict):
        message = json.dumps(message)

    # count the number of clients that were sent messages
    sent = 0

    # send all of the clients a message
    if 'connections' in req:
        for url in req['connections']:
            if ApiGatewaySender.send_message_to_ws_client(url, message):
                sent += 1

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

        required_dirs = [root_dir, root_dir+'/work', root_dir+'/data', root_dir+'/plots/summary']
        for center in request['centers']:
            required_dirs.append(root_dir + '/plots/summary/' + center)

        for required_dir in required_dirs:
            if not os.path.exists(required_dir):
                os.makedirs(required_dir)
            elif os.path.isfile(required_dir):
                return False

        temp_files = [request['root_dir'] + '/work/EMC/dry/group_stats.pkl']
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)

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
    :return: {bool} True=success; False=failure
    """
    try:
        bucket = os.environ['DATA_BUCKET']
        prefix = os.environ['OBJECT_PREFIX']
        data_dir = request['root_dir'] + '/data'

        s3 = boto3.client('s3')

        objs = get_s3_object_urls(request)
        for obj in objs:
            # create the local file name
            local_dir = data_dir+'/'+obj[:obj.rfind('/')]+'/'
            local_file = obj[obj.rfind('/')+1:]

            # create the local directory if needed
            if not os.path.exists(local_dir):
                os.makedirs(local_dir)

            # check to see if we already have the file
            if os.path.exists(local_dir + local_file):
                continue

            # download the file from S3
            try:
                print('Downloading S3 object: s3://%s/%s/%s' % (bucket, prefix, obj))
                s3.download_file(Bucket=bucket, Key=prefix+'/'+obj, Filename=local_dir+local_file)
                if not os.path.exists(local_dir + local_file):
                    print('Could not download S3 object: s3://%s/%s/%s' % (bucket, prefix, obj))
                    raise Exception('Missing S3 data')
            except Exception as e:
                errors.append('Data missing from S3: s3://%s/%s/%s' % (bucket, prefix, obj))
                print(e)

        return True
    except Exception as e:
        errors.append('Error downloading data object from S3')
        print(e)


def process_bulk_stats(request):
    """
    Run the summary_bulk.py script on the data we have downloaded
    :param request: {dict} A validated and sanitized request object
    :return: None
    """
    from summary_bulk import summary_bulk_main

    try:
        # delete previous work file
        work_file = request['root_dir'] + 'work/' + request['centers'][0] + '/dry/bulk_stats.h5'
        if os.path.exists(work_file):
            os.remove(work_file)

        sys.argv = ['script',
                    '--center',
                    ','.join(request['centers']),
                    '--norm',
                    request['norm'],
                    '--rootdir',
                    request['root_dir'],
                    '--begin_date',
                    request['start_date'] + request['cycles'][0],
                    '--end_date',
                    request['end_date'] + request['cycles'][0],
                    '--interval',
                    '24']

        print('running summary_bulk_main: %s' % ' '.join(sys.argv))
        summary_bulk_main()
    except Exception as e:
        errors.append('Error computing bulk statistics')
        print(e)


def process_fsoi_summary(request):
    """
    Run the fsoi_summary.py script on the bulk statistics
    :param request: {dict} A validated and sanitized request object
    :return: None
    """
    from summary_fsoi import summary_fsoi_main

    try:
        sys.argv = [
            'script',
            '--center',
            request['centers'][0],
            '--norm',
            request['norm'],
            '--rootdir',
            request['root_dir'],
            '--platform',
            request['platforms'],
            '--savefigure',
            '--cycle'
        ]
        for cycle in request['cycles']:
            sys.argv.append(cycle)

        print('running summary_fsoi_main: %s' % ' '.join(sys.argv))
        summary_fsoi_main()
    except Exception as e:
        errors.append('Error computing FSOI summary')
        print(e)


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
    :return: {list} A list of S3 object URLs
    """
    start_date = request['start_date']
    end_date = request['end_date']
    centers = request['centers']
    norm = request['norm']
    cycles = request['cycles']

    s3_objects = []
    for date in dates_in_range(start_date, end_date):
        for center in centers:
            for cycle in cycles:
                s3_objects.append('%s/%s.%s.%s%s.h5' % (center, center, norm, date, cycle))

    return s3_objects


def cache_summary_plots_in_s3(hash_value, request):
    """
    Copy all of the new summary plots to S3
    :param hash_value: {str} The hash value of the request
    :param request: {dict} The full request
    :return: None
    """
    # retrieve relevant environment variables
    bucket = os.environ['CACHE_BUCKET']
    root_dir = os.environ['FSOI_ROOT_DIR']
    img_dir = root_dir + '/plots/summary'

    # list of files to cache
    files = [
        img_dir + '/__CENTER__/__CENTER___ImpPerOb___CYCLE__Z.png',
        img_dir + '/__CENTER__/__CENTER___FracImp___CYCLE__Z.png',
        img_dir + '/__CENTER__/__CENTER___ObCnt___CYCLE__Z.png',
        img_dir + '/__CENTER__/__CENTER___TotImp___CYCLE__Z.png',
        img_dir + '/__CENTER__/__CENTER___FracNeuObs___CYCLE__Z.png',
        img_dir + '/__CENTER__/__CENTER___FracBenObs___CYCLE__Z.png'
    ]

    # create the s3 client
    s3 = boto3.client('s3')

    # loop through all centers and files
    key_list = []
    for center in request['centers']:
        for cycle in request['cycles']:
            for file in files:
                # replace the center in the file name
                filename = file.replace('__CENTER__', center).replace('__CYCLE__', cycle)
                if os.path.exists(filename):
                    print('Uploading %s to S3...' % filename)
                    key = hash_value + '/' + filename[filename.rfind('/') + 1:]
                    s3.upload_file(Filename=filename, Bucket=bucket, Key=key)
                    key_list.append(key)

    if not key_list:
        errors.append('Failed to generate plots')

    return key_list


if __name__ == '__main__':
    print('args:')
    for arg in sys.argv:
        print(arg)
    global_request = json.loads(sys.argv[1])
    main(global_request)
