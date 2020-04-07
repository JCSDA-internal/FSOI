"""
Test the lambda_wrapper function
"""
import os
import json


os.environ['CACHE_BUCKET'] = 'fsoi-image-cache'
os.environ['OBJECT_PREFIX'] = 'intercomp/hdf5'
os.environ['FSOI_ROOT_DIR'] = '/tmp/pycharm/test/fsoi'
os.environ['DATA_BUCKET'] = 'fsoi-test'
os.environ['REGION'] = 'us-east-1'


def test_pass_requests():
    """
    Use the predefined requests to test the lambda wrapper function
    """
    import time
    import yaml
    from fsoi.web.request_handler import Handler
    from fsoi.web.serverless_tools import hash_request, RequestDao

    data = yaml.full_load(open('../test_resources/fsoi_sample_requests.yaml'))

    p = data['requests']['batch']['pass']

    # run tests for requests that should pass
    for req in p:
        # add the root_dir to the request, this normally happens when 'validate_request'
        # is called in the lambda function.  However, we are skipping the lambda function,
        # so we must do it here before processing the request
        req['root_dir'] = '/tmp/pycharm/test/fsoi'

        # add an unused request field to generate a unique hash
        req['time'] = time.time()
        req_hash = hash_request(req)

        # run the batch process
        job = {
            'req_hash': req_hash,
            'status_id': 'PENDING',
            'message': 'Pending',
            'progress': '0',
            'req_obj': json.dumps(req)
        }
        RequestDao.add_request(job)
        handler = Handler(req)
        handler.run()

        req_status = RequestDao.get_request(req_hash)
        assert req_status['status_id'] == 'SUCCESS'


def test_fail_requests():
    """
    Use the predefined requests to test the lambda wrapper function
    """
    import time
    import yaml
    from fsoi.web.request_handler import Handler
    from fsoi.web.serverless_tools import hash_request, RequestDao

    data = yaml.full_load(open('../test_resources/fsoi_sample_requests.yaml'))

    f = data['requests']['batch']['fail']

    # run tests for requests that should fail
    for (i, req) in enumerate(f):
        # identify which case
        print('running test case %d' % (i+1))

        # add the root_dir to the request, this normally happens when 'validate_request'
        # is called in the lambda function.  However, we are skipping the lambda function,
        # so we must do it here before processing the request
        req['root_dir'] = '/tmp/pycharm/test/fsoi'

        # add an unused request field to generate a unique hash
        req['time'] = time.time()
        req_hash = hash_request(req)

        # run the batch process
        job = {
            'req_hash': req_hash,
            'status_id': 'PENDING',
            'message': 'Pending',
            'progress': '0',
            'req_obj': json.dumps(req)
        }
        RequestDao.add_request(job)
        handler = Handler(req)
        handler.run()

        req_status = RequestDao.get_request(req_hash)
        assert req_status['status_id'] == 'FAIL'


def test_focus_requests():
    """
    Use the predefined requests to test the lambda wrapper function
    """
    import time
    import yaml
    from fsoi.web.request_handler import Handler
    from fsoi.web.serverless_tools import hash_request, RequestDao

    data = yaml.full_load(open('../test_resources/fsoi_sample_requests.yaml'))

    if 'focus' not in data['requests']['batch']:
        return

    f = data['requests']['batch']['focus']

    # run tests to focus on (short cut to a test case while testing)
    if f is not None:
        for req in f:
            # add the root_dir to the request, this normally happens when 'validate_request'
            # is called in the lambda function.  However, we are skipping the lambda function,
            # so we must do it here before processing the request
            req['root_dir'] = '/tmp/pycharm/test/fsoi'

            # add an unused request field to generate a unique hash
            req['time'] = time.time()
            req_hash = hash_request(req)

            if 'cache_id' in req:
                from fsoi.web.lambda_wrapper import get_cached_object_keys, create_response_body
                key_list = get_cached_object_keys(req_hash)
                response = create_response_body(key_list, req_hash, [], [])
                print(json.dumps(response))
            else:
                # run the batch process
                job = {
                    'req_hash': req_hash,
                    'status_id': 'PENDING',
                    'message': 'Pending',
                    'progress': '0',
                    'req_obj': json.dumps(req)
                }
                RequestDao.add_request(job)
                handler = Handler(req)
                handler.run()

            req_status = RequestDao.get_request(req_hash)
            assert req_status['status_id'] == 'SUCCESS'
