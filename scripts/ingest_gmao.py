"""
This script will download files from NASA's website, upload them to an S3 bucket and submit a
batch job to process the files and save them to HDF5 format that can be used by the IOS webapp.
This script is intended to be called once per day by CloudWatch Events.
"""

import os
import time
import datetime
import re
import json
from threading import Thread
import boto3
import urllib3
import certifi


class Worker(Thread):
    """
    Thread to download file and put data in S3
    """

    # Static S3 client to be used by all threads
    s3_client = boto3.client('s3')

    def __init__(self, url, s3_bucket, s3_key):
        """
        Constructor
        :param url: Source URL
        :param s3_bucket: Target S3 bucket
        :param s3_key: Target S3 key
        """
        super(Worker, self).__init__()
        self.url = url
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.download_size = 0
        self.success = False

    def run(self):
        """
        Download a file from the website
        :return: None
        """
        try:

            # read the data from the URL
            https = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
            response = https.request('GET', self.url)

            # check that the response is OK (200)
            if response.status != 200:
                print('Website responded with %d' % response.status)
                print('URL: %s' % self.url)
                print(response.data.decode())
                return

            # write the data to S3
            s3_response = Worker.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=self.s3_key,
                Body=response.data
            )

            # check for an error in the response
            if s3_response['ResponseMetadata']['HTTPStatusCode'] != 200:
                print('Error uploading data to S3')
                print('URL: %s' % self.url)
                print('S3 URL: s3://%s/%s' % (self.s3_bucket, self.s3_key))
                return

            # happy
            print('Done: %s' % self.s3_key)
            self.download_size = len(response.data)
            self.success = True

        except RuntimeError as exception:
            print(exception)
            self.success = False


def get_list_of_files_from_url(url):
    """
    Retrieve a list of files available at this URL
    :param url: The base URL to the GMAO download portal
    :return: {list} A list of files at this URL (file name only), or None if an error occurred
    """
    # read the data on the website with a GET request
    https = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
    response = https.request('GET', url)
    if response.status != 200:
        print('Website responded with %d' % response.status)
        print('URL: %s' % url)
        print(response.data.decode())
        return None

    # parse the file names from the data
    data = response.data.decode()
    files = re.findall('GEOS.*?.ods', data, re.MULTILINE)
    return list(set(files))


def main(event, context):
    """
    The main lambda entry point, or main function if called stand-alone
    :param event: {NoneType} Not used, but required for Lambda
    :param context: {NoneType} Not used, but required for Lambda
    :return: None
    """
    log = {'ok': False, 'runtime': int(time.time()), 'size': -1, 'file_count': 0, 'name': 'n/a'}

    if event is None and context is None:
        print('No event or context')

    try:

        # get environment variables
        lag = int(os.environ['LAG_IN_DAYS'])
        https_host = os.environ['HTTPS_HOST']
        remote_path = os.environ['REMOTE_PATH']
        bucket = os.environ['BUCKET_NAME']
        cycle_hour = 0

        # compute the base url with the date
        date = datetime.datetime.utcfromtimestamp(time.time() - lag * 86400)
        remote_path = remote_path % (date.year, date.month, date.day, cycle_hour)
        base_url = 'https://%s/%s' % (https_host, remote_path)
        files = get_list_of_files_from_url(base_url)

        # start all data transfer threads
        threads = []
        s3_key_template = 'Y%04d/M%02d/D%02d/H%02d/%s'
        for remote_file in files:
            print('Transferring %s' % remote_file)
            key = s3_key_template % (date.year, date.month, date.day, cycle_hour, remote_file)
            url = '%s/%s' % (base_url, remote_file)
            thread = Worker(url, bucket, key)
            thread.start()
            threads.append(thread)

        # wait for all threads to finish and collect results
        for thread in threads:
            thread.join()
            if thread.success:
                log['file_count'] += 1
                log['size'] += thread.download_size
                log['ok'] = True

        # TODO: submit a Batch job to process the new data
        # submit_batch_job(s3_bucket, s3_key_template, files)

        # print the log info for CloudWatch
        print(json.dumps(log))

    except RuntimeError as exception:
        print(exception)
        print(json.dumps(log))


if __name__ == '__main__':
    from argparse import ArgumentParser
    from argparse import ArgumentDefaultsHelpFormatter as HelpFormatter

    DEFAULT_HOST = 'portal.nccs.nasa.gov'
    DEFAULT_PATH = '/datashare/gmao_ops/pub/f522_fp/.internal/obs/Y%04d/M%02d/D%02d/H%02d'
    DEFAULT_BUCKET = 'fsoi-gmao-ingest'
    PARSER = ArgumentParser(description='Download GMAO data', formatter_class=HelpFormatter)
    PARSER.add_argument('--lag', help='download data from N days ago', type=str, required=True)
    PARSER.add_argument('--host', help='portal.nccs.nasa.gov', type=str, default=DEFAULT_HOST)
    PARSER.add_argument('--remote-path', help='Remote path template', default=DEFAULT_PATH)
    PARSER.add_argument('--bucket-name', help='S3 bucket name', default=DEFAULT_BUCKET)
    ARGS = PARSER.parse_args()

    os.environ['LAG_IN_DAYS'] = ARGS.lag
    os.environ['HTTPS_HOST'] = ARGS.host
    os.environ['REMOTE_PATH'] = ARGS.remote_path
    os.environ['BUCKET_NAME'] = ARGS.bucket_name

    main(None, None)
