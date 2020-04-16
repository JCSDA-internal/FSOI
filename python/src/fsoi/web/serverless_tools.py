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
from fsoi import log


def create_error_response_body(req_hash, error_list, warn_list):
    """
    Create a response with errors
    :param req_hash: The request hash
    :param error_list: List of error messages to return to the user
    :param warn_list: List of warning messages to return to the user
    :return: Formatted response body
    """
    return {'req_hash': req_hash, 'errors': error_list, 'warnings': warn_list}


def create_response_body(plot_urls, hash_value, warns, errors):
    """
    Create a response body with URLs to all created images
    :param plot_urls: {list} A list of S3 keys to images
    :param hash_value: {str} Hash value of the request
    :param warns: {list} A list of warnings possibly empty
    :param errors: {list} A list of errors possibly empty
    :return: {str} A JSON string to be used for a response body
    """
    import os
    import json

    # get values from the environment
    bucket = os.environ['CACHE_BUCKET']
    region = os.environ['REGION']

    # create a response stub
    response = {
        'images': [],
        'warnings': warns,
        'errors': errors
    }

    # add each key in the list to the response
    for url in plot_urls:
        if url.endswith('.json'):  # only looking for images here
            continue
        # item = {'center': center, 'type': typ, 'url': url, 'bucket': bucket, 'key': key.replace('.png', '.json')}
        item = {'url': url, 'bucket': bucket, 'key': url.replace('.png', '.json')}
        response['images'].append(item)

    # return the response body as a string
    return json.dumps(response)


def get_json_data(bucket, key):
    """
    Get JSON data from the S3 bucket
    :param bucket: Bucket name
    :param key: Key name
    :return: {bytes} JSON data or None
    """
    from fsoi.data.s3_datastore import S3DataStore
    source = {'bucket': bucket, 'key': key}
    data = S3DataStore().load(source)
    return data
