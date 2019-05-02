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
import pkgutil
import yaml
from fsoi import log


class Downloader(Thread):
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
        super(Downloader, self).__init__()
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
                log.error('Website responded with %d' % response.status)
                log.error('URL: %s' % self.url)
                log.error(response.data.decode())
                return

            # write the data to S3
            s3_response = Downloader.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=self.s3_key,
                Body=response.data
            )

            # check for an error in the response
            if s3_response['ResponseMetadata']['HTTPStatusCode'] != 200:
                log.error('Error uploading data to S3')
                log.error('URL: %s' % self.url)
                log.error('S3 URL: s3://%s/%s' % (self.s3_bucket, self.s3_key))
                return

            # happy
            log.debug('Done: %s' % self.s3_key)
            self.download_size = len(response.data)
            self.success = True

        except RuntimeError as exception:
            log.error(exception)
            self.success = False

    def get_s3_url(self):
        """
        Return the target S3 url for this object
        :return: {str} S3 target url
        """
        return 's3://%s/%s' % (self.s3_bucket, self.s3_key)


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
        log.error('Website responded with %d' % response.status)
        log.error('URL: %s' % url)
        log.error(response.data.decode())
        return None

    # parse the file names from the data
    data = response.data.decode()
    files = re.findall('GEOS.*?.ods', data, re.MULTILINE)
    return list(set(files))


def download_gmao(lag, https_host, remote_path, bucket, cycle_hour):
    """
    The main lambda entry point, or main function if called stand-alone
    :param lag: {int} Number of days to look back for data
    :param https_host: {str} The host with https protocol
    :param remote_path: {str} The path on the server to find files
    :param bucket: {str} The bucket to which raw data will be uploaded
    :param cycle_hour: {int} The cycle hour (As of 2019-Apr, only 00Z is available)
    :return: {list} A list of S3 URLs to the files that were downloaded from GMAO
    """
    status = {'ok': False, 'runtime': int(time.time()), 'size': -1, 'file_count': 0, 'name': 'n/a'}

    try:

        # compute the base url with the date
        date = datetime.datetime.utcfromtimestamp(time.time() - lag * 86400)
        remote_path = remote_path % (date.year, date.month, date.day, cycle_hour)
        base_url = 'https://%s/%s' % (https_host, remote_path)
        files = get_list_of_files_from_url(base_url)

        # start all data transfer threads
        threads = []
        s3_key_template = 'Y%04d/M%02d/D%02d/H%02d/%s'
        for remote_file in files:
            log.debug('Transferring %s' % remote_file)
            key = s3_key_template % (date.year, date.month, date.day, cycle_hour, remote_file)
            url = '%s/%s' % (base_url, remote_file)
            thread = Downloader(url, bucket, key)
            thread.start()
            threads.append(thread)

        # wait for all threads to finish and collect results
        urls = []
        for thread in threads:
            thread.join()
            if thread.success:
                urls.append(thread.get_s3_url())
                status['file_count'] += 1
                status['size'] += thread.download_size
                status['ok'] = True

        # print the log info for CloudWatch
        print(json.dumps(status))

        # return the list of S3 urls for data files
        return urls

    except RuntimeError as exception:
        log.error(exception)
        log.error(json.dumps(status))


def download_gmao_from_lambda(event, context):
    """
    Entry point to ingest GMAO data from AWS Lambda
    :param event: Not used
    :param context: Not used
    :return: None
    """
    # get environment variables
    lag = int(os.environ['LAG_IN_DAYS'])
    https_host = os.environ['HTTPS_HOST']
    remote_path = os.environ['REMOTE_PATH']
    bucket = os.environ['BUCKET_NAME']
    cycle_hour = 0

    download_gmao(lag, https_host, remote_path, bucket, cycle_hour)


def main():
    """
    Entry point for command line
    :return: None
    """
    from argparse import ArgumentParser
    from argparse import ArgumentDefaultsHelpFormatter as HelpFormatter

    # get the default values from the config file
    config = yaml.full_load(pkgutil.get_data('fsoi', 'resources/fsoi/ingest/gmao/gmao_ingest.yaml'))
    https_host = config['https_host']
    remote_path = config['remote_path']
    bucket = config['raw_data_bucket']

    # parse the command line parameters
    parser = ArgumentParser(description='Download GMAO data', formatter_class=HelpFormatter)
    parser.add_argument('--lag', help='download data from N days ago', type=int, required=True)
    parser.add_argument('--host', help='portal.nccs.nasa.gov', type=str, default=https_host)
    parser.add_argument('--remote-path', help='Remote path template', default=remote_path)
    parser.add_argument('--bucket-name', help='S3 bucket name', default=bucket)
    parser.add_argument('--cycle-hour', help='Forecast cycle hour', type=int, default=0,
                        choices=[0, 6, 12, 18])
    args = parser.parse_args()

    # run the download function
    urls = download_gmao(args.lag, args.host, args.remote_path, args.bucket_name, args.cycle_hour)

    # print the new s3 urls
    log.info('Data copied to:')
    for url in urls:
        log.info(url)


if __name__ == '__main__':
    main()
