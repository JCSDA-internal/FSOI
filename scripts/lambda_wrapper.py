"""
This script is an entry point for an AWS Lambda function to download
H5 files from S3 and create plots using existing functions.
"""
import sys
import os
import json
import boto3
from serverless_tools import ApiGatewaySender, RequestDao, get_reference_id, hash_request, \
    create_response_body

# Add various paths for
sys.path.extend(['../lib', 'lib', '.'])


def main(event, context):
    """
    Create a chart as a PNG based on the input parameters
    :param event: Contains the HTTP request
    :param context: Contains details of the lambda function
    :return: None
    """
    # request is all query string parameters
    request = json.loads(event['body'])

    # get the reference ID and put a marker in the CloudWatch Logs
    ref_id = 'RefId: %s' % get_reference_id(request)
    print(ref_id)

    # build the client's connection url
    domain_name = event['requestContext']['domainName']
    stage = event['requestContext']['stage']
    connection_id = event['requestContext']['connectionId']
    client_url = 'https://%s/%s/@connections/%s' % (domain_name, stage, connection_id)
    print(client_url)

    # if this is a request for a cached job, return the cached images
    if 'cache_id' in request:
        send_cached_response(request['cache_id'], client_url)
        return

    # validate the request
    request = validate_request(request)
    if request is None:
        send_response('Request is invalid', client_url)
        return

    # get the request hash value
    hash_value = hash_request(request)

    # get the status of the request
    job = RequestDao.get_request(hash_value)

    # if the job has not previously been requested, or it failed, then submit a new request
    if job is None or 'status_id' not in job or job['status_id'] == 'FAIL':
        submit_request(request, hash_value, client_url, ref_id)

    # if the job is currently running or pending, notify the client and add their URL to the DB
    elif job['status_id'] in ['PENDING', 'RUNNING']:
        send_status_to_client(job, client_url)
        RequestDao.add_client_url(hash_value, client_url)

    # if the job has previously completed successfully, send a cached response
    elif job['status_id'] == 'SUCCESS':
        send_cached_response(job['req_hash'], client_url)

    # if we get here, we've missed some cases and need to fix code
    else:
        send_response({'error': ['Error processing job.', ref_id]}, client_url)


def submit_request(request, hash_value, client_url, ref_id):
    """
    Submit a new request to run in AWS batch
    :param request: All of the request parameters
    :param hash_value: A hash of the request
    :param client_url: A URL to contact the client
    :param ref_id: A text marker in the CloudWatch Logs, user can include as ref for debugging
    :return: None
    """
    # get a batch client
    batch = boto3.client('batch')

    # attempt to submit the batch job
    # TODO: jobQueue and jobDefinition should be environment variables
    res = batch.submit_job(
        jobName=hash_value,
        jobQueue='fsoi_queue',
        jobDefinition='fsoi_job:9',
        parameters={'request': json.dumps(request)}
    )
    submitted = res['ResponseMetadata']['HTTPStatusCode'] == 200

    # if submitted successfully, add the request to the DB and send status to client
    if submitted:
        job = {
            'req_hash': hash_value,
            'status_id': 'PENDING',
            'message': 'Pending',
            'progress': '0',
            'connections': [client_url],
            'req_obj': json.dumps(request)
        }
        RequestDao.add_request(job)
        ApiGatewaySender.send_message_to_ws_client(client_url, json.dumps(job))

    # otherwise, notify the client of an error
    else:
        error_message = 'Error processing request. %s' % ref_id
        ApiGatewaySender.send_message_to_ws_client(client_url, error_message)


def send_status_to_client(job, client_url):
    """
    Send the current status of the job to a client
    :param job: A job status object from the DB
    :param client_url: POST data to this URL
    :return: None
    """
    # remove the client connection URLs from the status
    job.pop('connections')

    # send the message to the client
    ApiGatewaySender.send_message_to_ws_client(client_url, json.dumps(job))


def send_cached_response(req_hash, client_url):
    """
    Send a response with cached data values
    :param req_hash: The request hash
    :param client_url: The URL to contact the client
    :return: None
    """
    key_list = get_cached_object_keys(req_hash)
    response = create_response_body(key_list, req_hash)
    send_response(response, client_url)


def send_response(message, client_url):
    """
    Send a response to the client
    :param message: The response
    :param client_url: The URL to contact the client
    :return: None
    """
    ApiGatewaySender.send_message_to_ws_client(client_url, message)


def validate_request(request):
    """
    Validate and sanitize all of the request parameters
    :param request: The request from the user
    :return: A validated and sanitized request or None
    """
    # TODO: Validate the request

    errors = []

    try:
        if 'cache_id' in request:
            return request

        request['centers'] = request['centers'].split(',')
        cycles = []
        for item in request['cycles'].split(','):
            cycles.append('%02d' % int(item.strip()))
        request['cycles'] = cycles
        request['root_dir'] = os.environ['FSOI_ROOT_DIR']
        return request
    except Exception as e:
        errors.append('Error validating the request')
        print(e)
        return None


def get_cached_object_keys(hash_value):
    """
    Determine if a request's results are available in the S3 cache
    :param hash_value: The hash value of the request
    :return: A list of object keys or None
    """
    # get the name of the s3 bucket used for caching results
    bucket = os.environ['CACHE_BUCKET']

    # get an S3 client
    s3 = boto3.client('s3')

    # get a list of objects
    objects = s3.list_objects_v2(Bucket=bucket, Prefix=hash_value)

    # if there are any objects returned
    if objects['KeyCount'] == 0:
        return None

    # extract a list of object keys
    keys = []
    for item in objects['Contents']:
        keys.append(item['Key'])
    return keys
