"""
This script will download a file from NRL's anonymous FTP site, upload it to an S3 bucket
and submit a batch job to convert the file to HDF5 format that can be used by the IOS webapp.
This script is intended to be called once per day by CloudWatch Events.
"""

import os
import time
import datetime
import pkgutil
import json
import boto3
import yaml
from ftplib import FTP
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter as HelpFormatter
from fsoi import log


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
    log.info('attempting to download ftp://%s/%s' % (host, remote_file))

    # download the remote file
    ftp.cwd(remote_dir)
    out = open(local_file, 'wb')
    ftp.retrbinary('RETR ' + remote_file_only, out.write)

    return local_file


def download_nrl(lag, ftp_host, remote_file_template, bucket_name):
    """
    A function to download a file from NRL and upload it to S3
    :param lag: {int} Look for the file N days ago
    :param ftp_host: {str} The FTP host name (FQDN)
    :param remote_file_template: {str} The template to create the remote file name
    :param bucket_name: {str} The bucket name where the file should be uploaded
    :return: {str} S3 URL to the new file, or None
    """
    status = {'ok': False, 'runtime': int(time.time()), 'size': -1, 'name': 'n/a'}

    try:
        # compute the date and remote file name
        date = datetime.datetime.utcfromtimestamp(time.time() - lag * 86400)
        date_str = '%04d%02d%02d' % (date.year, date.month, date.day)
        remote_file = remote_file_template.replace('DATE', date_str)

        # download the file from the FTP site
        local_file = ftp_download_file(ftp_host, remote_file)

        # create the S3 object key
        key = local_file[local_file.rfind('/') + 1:]

        # update the CloudWatch information
        status['name'] = key
        status['size'] = os.path.getsize(local_file)

        # log info
        log.info('attempting to upload data to s3://%s/%s' % (bucket_name, key))

        # copy the file to an S3 object
        s3 = boto3.client('s3')
        s3.upload_file(Filename=local_file, Bucket=bucket_name, Key=key)

        # check the response and print our CloudWatch information
        status['ok'] = True
        print(json.dumps(status))

        # return the S3 url
        return 's3://%s/%s' % (bucket_name, key)

    except Exception as e:
        log.error(e)
        log.error(json.dumps(status))
        return None


def main():
    """
    Entry point for command line
    :return: None
    """
    # load default values from the resource file
    config = yaml.full_load(pkgutil.get_data('fsoi', 'resources/fsoi/ingest/nrl/nrl_ingest.yaml'))
    bucket = config['raw_data_bucket']
    ftp_host = config['ftp_host']
    lag_in_days = config['lag_in_days']
    file = config['remote_path']

    # setup the arg parser
    parser = ArgumentParser(description='Download GMAO data', formatter_class=HelpFormatter)
    parser.add_argument('--lag', help='time lag in days', type=int, default=lag_in_days)
    parser.add_argument('--host', help='ftp-ex.nrlmry.navy.mil', type=str, default=ftp_host)
    parser.add_argument('--remote-path', help='Remote path template', default=file)
    parser.add_argument('--s3-bucket', help='Store in this bucket', default=bucket)
    args = parser.parse_args()

    s3_url = download_nrl(args.lag, args.host, args.remote_path, args.s3_bucket)

    if s3_url is not None:
        log.info('File saved at %s' % s3_url)


if __name__ == '__main__':
    main()
