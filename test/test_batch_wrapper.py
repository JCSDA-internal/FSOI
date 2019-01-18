"""
Test the lambda_wrapper function
"""
import sys
import os
import json

sys.path.extend(['lib', 'scripts', 'test', '.', '../lib', '../scripts'])

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
    import yaml
    import base64
    from batch_wrapper import main
    from serverless_tools import hash_request, RequestDao

    data = yaml.load(open('../test_resources/fsoi_sample_requests.yaml'))

    f = data['requests']['batch']['fail']
    p = data['requests']['batch']['pass']

    # run tests for requests that should fail
    for req in f:
        # add the root_dir to the request, this normally happens when 'validate_request'
        # is called in the lambda function.  batch_wrapper.py assumes this has already been called.
        req['root_dir'] = '/tmp/pycharm/test/fsoi'

        # add an unused request field to generate a unique hash
        req['time'] = time.time()
        req_hash = hash_request(req)

        # run the batch process
        main(req)

        req_status = RequestDao.get_request(req_hash)
        assert req_status['status_id'] == 'FAIL'

    # run tests for requests that should pass
    for req in p:
        # add the root_dir to the request, this normally happens when 'validate_request'
        # is called in the lambda function.  batch_wrapper.py assumes this has already been called.
        req['root_dir'] = '/tmp/pycharm/test/fsoi'

        # add an unused request field to generate a unique hash
        req['time'] = time.time()
        req_hash = hash_request(req)

        # run the batch process
        main(req)

        req_status = RequestDao.get_request(req_hash)
        assert req_status['status_id'] == 'SUCCESS'
