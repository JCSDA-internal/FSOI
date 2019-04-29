"""
These are functions commonly shared between Lambda and Batch processes
"""

import sys
import datetime
import hashlib
import hmac
import urllib.parse
import requests
import boto3


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
    hash_bit = hash_request(request)[:6]
    date_bit = '%04d-%02d-%02dT%02d:%02d:%02d' % \
               (d.year, d.month, d.day, d.hour, d.minute, d.second)

    return '%s_%s' % (hash_bit, date_bit)


def create_error_response_body(req_hash, error_list, warn_list):
    """
    Create a response with errors
    :param req_hash: The request hash
    :param error_list: List of error messages to return to the user
    :param warn_list: List of warning messages to return to the user
    :return: Formatted response body
    """
    return {'req_hash': req_hash, 'errors': error_list, 'warnings': warn_list}


def create_response_body(key_list, hash_value, warns):
    """
    Create a response body with URLs to all created images
    :param key_list: {list} A list of S3 keys to images
    :param hash_value: {str} Hash value of the request
    :param warns: {list} A list of warnings possibly empty
    :return: {str} A JSON string to be used for a response body
    """
    import os
    import json

    # get values from the environment
    bucket = os.environ['CACHE_BUCKET']
    region = os.environ['REGION']

    # create a response stub
    response = RequestDao.get_request(hash_value)
    response['images'] = []
    response['warnings'] = warns

    # add each key in the list to the response
    for key in key_list:
        tokens = key.split('/')[1].split('_')
        center = tokens[0]
        typ = tokens[1]
        if len(tokens) == 4:
            center = tokens[0] + '_' + tokens[1]
            typ = tokens[2]
        url = 'http://%s.s3-website-%s.amazonaws.com/%s' % (bucket, region, key)
        response['images'].append({'center': center, 'type': typ, 'url': url})

    # return the response body as a string
    return json.dumps(response)


class RequestDao:
    """
    A class to handle CRUD for requests
    """

    # The table name to store requests
    REQUEST_TABLE_NAME = 'fsoi_requests'

    @staticmethod
    def add_request(req_data):
        """
        Add a request to the dynamodb table
        :param req_data: Must contain: req_hash, status_id, message, progress, connections, req_obj
        :return:
        """
        dynamo = boto3.client('dynamodb')

        item = {
            'req_hash': {'S': req_data['req_hash']},
            'status_id': {'S': req_data['status_id']},
            'message': {'S': req_data['message']},
            'progress': {'N': req_data['progress']},
            'connections': {'SS': req_data['connections']},
            'req_obj': {'S': req_data['req_obj']}
        }
        dynamo.put_item(TableName=RequestDao.REQUEST_TABLE_NAME, Item=item)

    @staticmethod
    def get_request(req_hash):
        """
        Get request information given a hash value
        :param req_hash: The hash value of the request
        :return: Request information or None
        """
        dynamo = boto3.client('dynamodb')

        key = {'req_hash': {'S': req_hash}}
        res = dynamo.get_item(TableName=RequestDao.REQUEST_TABLE_NAME, Key=key)

        # make sure we got an item back in a response
        if res is None or 'Item' not in res:
            return None

        # return the item

        item = {
            'req_hash': res['Item']['req_hash']['S'],
            'status_id': res['Item']['status_id']['S'],
            'message': res['Item']['message']['S'],
            'progress': res['Item']['progress']['N']
        }
        if 'connections' in res['Item']:
            item['connections'] = res['Item']['connections']['SS']
        if 'req_obj' in res['Item']:
            item['req_obj'] = res['Item']['req_obj']['S']
        return item

    @staticmethod
    def add_client_url(req_hash, client_url):
        """
        Add a client URL to the dynamodb table for this request
        :param req_hash: The request hash to identify a specific request
        :param client_url: Client url to add
        :return: True if successful, False if failed
        """
        dynamo = boto3.client('dynamodb')

        key = {'req_hash': {'S': req_hash}}
        res = dynamo.update_item(
            TableName=RequestDao.REQUEST_TABLE_NAME,
            Key=key,
            UpdateExpression='ADD connections :connections',
            ExpressionAttributeValues={':connections': {'SS': [client_url]}}
        )

        return res['ResponseMetadata']['HTTPStatusCode'] == 200

    @staticmethod
    def remove_client_url(req_hash, client_url):
        """
        Remove a client URL from the dynamodb table for this request
        :param req_hash: The request hash to identify a specific request
        :param client_url: Client url to remove
        :return: True if successful, False if failed
        """
        dynamo = boto3.client('dynamodb')

        key = {'req_hash': {'S': req_hash}}
        res = dynamo.update_item(
            TableName=RequestDao.REQUEST_TABLE_NAME,
            Key=key,
            UpdateExpression='DELETE connections :connections',
            ExpressionAttributeValues={':connections': {'SS': [client_url]}}
        )

        return res['ResponseMetadata']['HTTPStatusCode'] == 200

    @staticmethod
    def update_status(req_hash, status_id, message, progress):
        """
        Update the status information of a request
        :param req_hash: The request hash to identify a specific request
        :param status_id: The status [PENDING|RUNNING|SUCCESS|FAIL]
        :param message: Free-form text to be passed to the user
        :param progress: Integer from 0 to 100 indicating percent complete
        :return: True if successful, False if failed
        """
        dynamo = boto3.client('dynamodb')

        key = {'req_hash': {'S': req_hash}}
        res = dynamo.update_item(
            TableName=RequestDao.REQUEST_TABLE_NAME,
            Key=key,
            UpdateExpression='SET status_id = :status_id, message = :message, progress = :progress',
            ExpressionAttributeValues={
                ':status_id': {'S': status_id},
                ':message': {'S': message},
                ':progress': {'N': str(progress)}
            }
        )

        return res['ResponseMetadata']['HTTPStatusCode'] == 200


class ApiGatewaySender:
    """
    This class will sign and send a message to an API Gateway client.  This code is
    derived from the example at the following URL:
    https://docs.aws.amazon.com/general/latest/gr/sigv4-signed-request-examples.html
    """

    @staticmethod
    def sign(key, msg):
        """
        Ket derivation function
        :param key:
        :param msg:
        :return:
        """
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

    @staticmethod
    def get_signature_key(key, date_stamp, region_name, service_name):
        """
        Create a signature key
        :param key: key
        :param date_stamp: date stamp
        :param region_name: region name
        :param service_name: service name
        :return: signature key
        """
        k_date = ApiGatewaySender.sign(('AWS4' + key).encode('utf-8'), date_stamp)
        k_region = ApiGatewaySender.sign(k_date, region_name)
        k_service = ApiGatewaySender.sign(k_region, service_name)
        k_signing = ApiGatewaySender.sign(k_service, 'aws4_request')
        return k_signing

    @staticmethod
    def send_message_to_ws_client(url, request_data):
        """
        Post data to an API Gateway Websocket URL
        :param url: The full URL to the websocket callback
        :param request_data: The data to send
        :return: {bool} True if successful, otherwise False
        """
        # request values
        tokens = url.split('/')
        method = 'POST'
        service = 'execute-api'
        host = tokens[2]
        region = host.split('.')[2]
        stage = tokens[3]
        endpoint = 'https://' + host
        connection_id = tokens[5]

        # get AWS credentials
        session = boto3.Session()
        credentials = session.get_credentials()
        credentials = credentials.get_frozen_credentials()
        access_key = credentials.access_key
        secret_key = credentials.secret_key
        aws_token = credentials.token
        if access_key is None or secret_key is None:
            print('No credentials are available.')
            sys.exit()

        # create a date for headers and the credential string
        timenow = datetime.datetime.utcnow()
        amzdate = timenow.strftime('%Y%m%dT%H%M%SZ')
        datestamp = timenow.strftime('%Y%m%d')

        # create the canonical request
        canonical_uri = '/%s/@connections/%s' % (stage, connection_id)
        canonical_headers = 'host:' + host + '\n' + 'x-amz-date:' + amzdate + '\n'
        signed_headers = 'host;x-amz-date'
        if aws_token:
            canonical_headers += 'x-amz-security-token:' + aws_token + '\n'
            signed_headers += ';x-amz-security-token'
        payload_hash = hashlib.sha256(request_data.encode('utf-8')).hexdigest()
        canonical_request = method + '\n' + urllib.parse.quote(canonical_uri) + '\n\n' + \
            canonical_headers + '\n' + signed_headers + '\n' + payload_hash

        # create the string to sign
        algorithm = 'AWS4-HMAC-SHA256'
        credential_scope = datestamp + '/' + region + '/' + service + '/' + 'aws4_request'
        string_to_sign = algorithm + '\n' + amzdate + '\n' + credential_scope + '\n' + \
            hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

        # compute and sign the signature
        signing_key = ApiGatewaySender.get_signature_key(secret_key, datestamp, region, service)
        signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256)\
            .hexdigest()

        # add signing information to the request
        authorization_header = algorithm + ' ' + 'Credential=' + access_key + '/' + \
            credential_scope + ', ' + 'SignedHeaders=' + signed_headers + ', ' +\
            'Signature=' + signature
        headers = {'x-amz-date': amzdate, 'Authorization': authorization_header}
        if aws_token:
            headers['X-Amz-Security-Token'] = aws_token

        # send the request
        request_url = endpoint + canonical_uri
        response = requests.post(request_url, headers=headers, data=request_data)

        # remove any URLs that give a 410 response code
        # TODO: Need request hash here to remove the client connection URL

        # check the response
        if response.status_code != 200:
            print('Response code: %d' % response.status_code)
            return False

        return True
