"""
This script will download a file from NRL's anonymous FTP site, upload it to an S3 bucket
and submit a batch job to convert the file to HDF5 format that can be used by the IOS webapp.
This script is intended to be called once per day by CloudWatch Events.
"""

import os
import time
import datetime
import json
import boto3
from ftplib import FTP


def ftp_download_file(host, remote_file, local_file=None):
    """
    Download a file from an FTP site anonymously
    :param host: FTP hostname
    :param remote_file: Full path to the remote file
    :param local_file: Full path to the local file
    :return: None
    """
    # connect and login
    ftp = FTP(host)
    ftp.login()
    ftp.makepasv()

    # parse file names
    remote_dir = remote_file[0:remote_file.rfind('/')]
    remote_file_only = remote_file[1 + remote_file.rfind('/'):]
    if local_file is None:
        local_file = '/tmp/' + remote_file_only

    # log info
    print('attempting to download ftp://%s/%s' % (host, remote_file))

    # download the remote file
    ftp.cwd(remote_dir)
    out = open(local_file, 'wb')
    ftp.retrbinary('RETR ' + remote_file_only, out.write)

    return local_file


def ingest_navy_aws_lambda(event, context):
    """
    The main lambda entry point, or main function if called stand-alone
    :param event: {NoneType} Not used, but required for Lambda
    :param context: {NoneType} Not used, but required for Lambda
    :return: None
    """
    log = {'ok': False, 'runtime': int(time.time()), 'size': -1, 'name': 'n/a'}

    try:

        lag = int(os.environ['LAG_IN_DAYS'])
        ftp_host = os.environ['FTP_HOST']
        remote_file_template = os.environ['REMOTE_FILE_TEMPLATE']
        bucket_name = os.environ['BUCKET_NAME']

        # compute the date and remote file name
        date = datetime.datetime.utcfromtimestamp(time.time() - lag * 86400)
        date_str = '%04d%02d%02d' % (date.year, date.month, date.day)
        remote_file = remote_file_template.replace('DATE', date_str)

        # download the file from the FTP site
        local_file = ftp_download_file(ftp_host, remote_file)

        # create the S3 object key
        key = local_file[local_file.rfind('/') + 1:]

        # update the CloudWatch information
        log['name'] = key
        log['size'] = os.path.getsize(local_file)

        # log info
        print('attempting to upload data to s3://%s/%s' % (bucket_name, key))

        # copy the file to an S3 object
        s3 = boto3.client('s3')
        s3.upload_file(Filename=local_file, Bucket=bucket_name, Key=key)

        # submit a batch job to convert the file to HDF5 format
        input_url = 's3://%s/%s' % (bucket_name, key)
        output_url = os.environ['OUTPUT_URL_TEMPLATE'].replace('DATE', date_str)
        batch = boto3.client('batch')
        batch.submit_job(
            jobName='NRL-Ingest-%s-00Z' % date_str,
            jobQueue='fsoi_ingest_queue',
            jobDefinition='fsoi_ingest_nrl_job:10',
            parameters={'input_url': input_url, 'output_url': output_url}
        )

        # check the response and print our CloudWatch information
        log['ok'] = True
        print(json.dumps(log))

    except Exception as e:
        print(e)
        print(json.dumps(log))


def main():
    """
    Entry point for command line
    :return: None
    """
    from argparse import ArgumentParser
    from argparse import ArgumentDefaultsHelpFormatter as HelpFormatter

    bucket = 'fsoi-navy-ingest'
    ftp_host = 'ftp-ex.nrlmry.navy.mil'
    lag_in_days = '4'
    file = 'receive/obimpact_gemops_DATE00.bz2'
    output_url_template = 's3://fsoi/intercomp/hdf5/NRL/NRL.dry.DATE00.h5'
    PARSER = ArgumentParser(description='Download GMAO data', formatter_class=HelpFormatter)
    PARSER.add_argument('--lag', help='time lag in days', type=int, default=lag_in_days)
    PARSER.add_argument('--host', help='ftp-ex.nrlmry.navy.mil', type=str, default=ftp_host)
    PARSER.add_argument('--remote-path', help='Remote path template', default=file)
    PARSER.add_argument('--s3-bucket', help='Store in this bucket', default=bucket)
    PARSER.add_argument('--output-url', help='Final processing target', default=output_url_template)
    args = PARSER.parse_args()

    os.environ['BUCKET_NAME'] = args.s3_bucket
    os.environ['FTP_HOST'] = args.host
    os.environ['LAG_IN_DAYS'] = str(args.lag)
    os.environ['REMOTE_FILE_TEMPLATE'] = args.remote_path
    os.environ['OUTPUT_URL_TEMPLATE'] = args.output_url

    ingest_navy_aws_lambda(None, None)


if __name__ == '__main__':
    main()
