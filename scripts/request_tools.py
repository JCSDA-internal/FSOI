"""
This module contains classes and methods to assist with request management
and sending messages back to clients asynchronously through API Gateway websockets.
"""
import sys
import os
import datetime
import hashlib
import hmac
import urllib.parse
import requests
import boto3


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
        return {
            'req_hash': res['Item']['req_hash']['S'],
            'status_id': res['Item']['status_id']['S'],
            'message': res['Item']['message']['S'],
            'progress': res['Item']['progress']['N'],
            'connections': res['Item']['connections']['SS'],
            'req_obj': res['Item']['req_obj']['S']
        }

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
                ':progress': {'N': progress}
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
        endpoint = 'https://' + host
        connection_id = tokens[5]

        # get AWS credentials
        access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        if access_key is None or secret_key is None:
            print('No access key is available.')
            print('  setenv AWS_ACCESS_KEY_ID XXX')
            print('  setenv AWS_SECRET_ACCESS_KEY YYY')
            sys.exit()

        # create a date for headers and the credential string
        timenow = datetime.datetime.utcnow()
        amzdate = timenow.strftime('%Y%m%dT%H%M%SZ')
        datestamp = timenow.strftime('%Y%m%d')

        # create the canonical request
        canonical_uri = '/v2/@connections/' + connection_id
        canonical_headers = 'host:' + host + '\n' + 'x-amz-date:' + amzdate + '\n'
        signed_headers = 'host;x-amz-date'
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

        # send the request
        request_url = endpoint + canonical_uri
        response = requests.post(request_url, headers=headers, data=request_data)

        if response.status_code != 200:
            print('Mission Failed:')
            print('Response code: %d\n' % response.status_code)
            print(response.text)
            print(response.headers)
            return False

        return True


def message_all_clients(req_hash, message):
    """
    Send a message to all clients listening to the request
    :param req_hash: The request hash
    :param message: The message
    :return: Number of clients notified
    """
    req = RequestDao.get_request(req_hash)

    sent = 0

    for url in req['connections']:
        if ApiGatewaySender.send_message_to_ws_client(url, message):
            sent += 1

    return sent
