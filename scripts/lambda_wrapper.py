"""
This script is an entry point for an AWS Lambda function to download
H5 files from S3 and create plots using existing functions.
"""
import sys
from process_request import process_request

# Add various paths for
sys.path.extend(['../lib', 'lib', '.'])


def lambda_gen_fsoi_chart(event, context):
    """
    Create a chart as a PNG based on the input parameters
    :param event: Contains the HTTP request
    :param context: Contains details of the lambda function
    :return: The HTTP response, including Base64-encoded PNG
    """
    import json

    # request is all query string parameters
    request = event['queryStringParameters']

    # process the request
    response_body = process_request(request)

    # if there are no errors, return a valid response
    if response_body is not None and 'errors' not in response_body:
        response = create_response(response_body)
        print(json.dumps(response))
        return response

    # if there are errors, return an error response
    response = create_error_response(response_body)
    print(json.dumps(response))
    return response


def create_response(body):
    """
    Create a successful response with the given body
    :param body: The body of the response message
    :return: An HTTP response message
    """
    response = dict()
    response['isBase64Encoded'] = False
    response['headers'] = {}
    response['headers']['Content-Type'] = 'text/json'
    response['headers']['Content-Encoding'] = 'utf-8'
    response['headers']['Access-Control-Allow-Origin'] = '*'
    response['headers']['Access-Control-Allow-Credentials'] = True
    response['body'] = body

    return response


def create_error_response(body):
    """
    Create a response with errors
    :param body: {dict} error response body
    :return: List of error messages
    """
    import base64
    import json

    response = dict()
    response['isBase64Encoded'] = True
    response['headers'] = {}
    response['headers']['Content-Type'] = 'text/json'
    response['headers']['Content-Encoding'] = 'utf-8'
    response['headers']['Access-Control-Allow-Origin'] = '*'
    response['headers']['Access-Control-Allow-Credentials'] = True
    response['body'] = base64.b64encode(json.dumps(body).encode('utf-8')).decode('utf-8')

    return response


if __name__ == '__main__':
    import json

    global_event = {
        'queryStringParameters': {
            'start_date': '20150220',
            'end_date': '20150222',
            'centers': 'EMC',
            'norm': 'dry',
            'interval': '24',
            'platforms': 'ASCAT Wind,Satellite Wind,MODIS Wind',
            'cycles': '18'
        }
    }

    global_response = lambda_gen_fsoi_chart(global_event, None)
    print(json.dumps(global_response, indent='  '))
