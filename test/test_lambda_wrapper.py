"""
Test the lambda_wrapper function
"""
import sys
import os
import json

sys.path.extend(['lib', 'scripts', 'test'])

os.environ['CACHE_BUCKET'] = 'fsoi-image-cache'
os.environ['OBJECT_PREFIX'] = 'intercomp/hdf5'
os.environ['FSOI_ROOT_DIR'] = '/tmp/pycharm/test/fsoi'
os.environ['DATA_BUCKET'] = 'fsoi'
os.environ['REGION'] = 'us-east-1'


def test_all_requests():
    """
    Use the predefined requests to test the lambda wrapper function
    """
    import time
    import json
    import base64
    from lambda_wrapper import lambda_gen_fsoi_chart

    data = json.loads(open('test_resources/lambda_wrapper_requests.json').read())
    for request in data['requests']:
        request['unique'] = time.time()
        response = lambda_gen_fsoi_chart({'queryStringParameters': request}, None)

        print(json.dumps(response, indent='  '))
        if response['isBase64Encoded']:
            print(base64.b64decode(response['body']).decode())
