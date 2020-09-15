"""
FSOI Ingest MET
"""
__all__ = ['process_met', 'download_met', 'download_and_process_met']


import yaml
import pkgutil
from datetime import datetime
import tempfile
import pytz
import json
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter as HelpFormatter
from fsoi import log
from fsoi.fsoilog import enable_cloudwatch_logs
from fsoi.ingest import compute_date_from_lag
from fsoi.ingest.met.download_met import download_met
from fsoi.ingest.met.process_met import process_met
from fsoi.data.s3_datastore import S3DataStore


def download_and_process_met_cli():
    """
    Download and process met data CLI entry point
    :return: None
    """
    try:
        # enable cloudwatch logging
        enable_cloudwatch_logs(True, 'ingest_met')
        log.debug('Starting MET download and process')

        # read default parameter values from MET config file
        config = yaml.full_load(pkgutil.get_data('fsoi', 'ingest/met/met_ingest.yaml'))
        lag = config['lag_in_days']
        ftp_host = config['ftp_host']
        remote_path = config['remote_path']
        bucket = config['raw_data_bucket']

        # parse the command line parameters
        parser = ArgumentParser(description='Download and process UK Met Office data', formatter_class=HelpFormatter)
        parser.add_argument('--lag', help='download data from N days ago', type=int, default=lag)
        parser.add_argument('--host', help='portal.nccs.nasa.gov', type=str, default=ftp_host)
        parser.add_argument('--remote-path', help='Remote path template', default=remote_path)
        parser.add_argument('--bucket-name', help='S3 bucket name', default=bucket)
        parser.add_argument('--norm', help='Norm', default='moist', type=str, choices=['dry', 'moist'])
        args = parser.parse_args()

        # get the values from the command line parameters
        lag = args.lag
        ftp_host = args.host
        remote_path = args.remote_path
        bucket = args.bucket_name
        date_str = compute_date_from_lag(lag)

        download_and_process_met(date_str, ftp_host, remote_path, bucket, lag)

    except Exception as e:
        ok = False
        log.error('MET ingest failed')
        log.error(e)
        log.info(json.dumps({'met_ok': ok, 'met_files_processed': 0}))


def download_and_process_met(date_str, ftp_host, remote_path, bucket, lag):
    """
    Perform the download and processing
    :param date_str:
    :param ftp_host:
    :param remote_path:
    :param bucket:
    :param lag:
    :return:
    """
    # download the met files
    datastore = S3DataStore()
    s3urls = download_met(date_str, ftp_host, remote_path, bucket)

    # process the met files -- expecting 4 files: there should be one file for each cycle time in the day (0, 6, 12, 18)
    for s3url in s3urls:
        # download the file object from S3
        descriptor = datastore.url_to_descriptor(s3url)
        local_file = tempfile.mktemp()
        if not datastore.load_to_local_file(descriptor, local_file):
            log.warning('Failed to get data for descriptor: %s/%s' % (descriptor['bucket'], descriptor['key']))
            continue

        # process the data files
        output_dir = tempfile.mkdtemp()
        date = pytz.utc.localize(datetime.utcfromtimestamp(datetime.now() - lag * 86400))
        processed_files = process_met(local_file, output_dir, date, date_str)

        # check the number of successfully processed files and log for CloudWatch monitoring
        file_count = len(processed_files)
        ok = file_count > 0
        log.info(json.dumps({'met_ok': ok, 'met_files_processed': file_count}))


def ingest_met_for_last_month():
    """
    Ingest all met data from the previous month
    :return: None
    """
    # determine which month was last month
    now = datetime.utcnow()
    last_month = now.month - 1
    while last_month <= 0:
        last_month += 12

    # get the number of days last month
    days = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][last_month]

