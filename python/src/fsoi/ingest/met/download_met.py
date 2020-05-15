"""
This script will download a file from MET's password-protected FTP site and upload it to an S3 bucket.
"""

import pkgutil
import yaml
from argparse import ArgumentParser
from fsoi import log
from fsoi.data.s3_datastore import S3DataStore
from fsoi.ingest import compute_date_from_lag
import boto3
import json


def download_met(date_str, ftp_host, remote_file_templates, bucket_name):
    """
    A function to download a file from NRL and upload it to S3
    :param date_str: {datetime} Look for the file for this date
    :param ftp_host: {str} The FTP host name (FQDN)
    :param remote_file_templates: {list} Template list for the remote file name; the 'DATE' substring will be replaced
    :param bucket_name: {str} The bucket name where the file should be uploaded
    :return: {list} List of S3 URLs to the new files, or None
    """
    # create an S3 data store object
    datastore = S3DataStore()

    # get FTP site credentials
    username, password = get_ftp_login_credentials()
    if username is None and password is None:
        return

    # download all files for the given date
    successful = True
    s3_urls = []
    for remote_file_template in remote_file_templates:
        # compute the remote file name
        remote_file = remote_file_template.replace('DATE', date_str)

        # download the file from the FTP site
        url = 'ftp://%s/%s' % (ftp_host, remote_file)
        key = remote_file.split('/')[-1]
        target = {'bucket': bucket_name, 'key': key}
        successful = successful and datastore.save_from_ftp(url, target, username, password)

        # add S3 URL
        if successful:
            s3_urls.append('s3://%s/%s' % (bucket_name, key))
        else:
            log.error('Failed to save data from %s' % url)
            return None

    return s3_urls


def get_ftp_login_credentials(secret_name='ukmet_ftp', secret_region='us-east-1'):
    """
    Get the FTP login credentials
    :param secret_name: {str} Name of the AWS secret
    :param secret_region: {str} Region in which the secret is stored
    :return: {tuple}: (username, password)
    """
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=secret_region)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(get_secret_value_response['SecretString'])
        return secret['username'], secret['password']
    except Exception:
        log.error('Failed to get FTP login credentials')
        log.error('Expecting to find credentials in AWS Secrets Manager: %s' % secret_name)
        return None, None


def main():
    """
    Entry point for command line
    :return: None
    """
    # load default values from the resource file
    config = yaml.full_load(pkgutil.get_data('fsoi', 'ingest/met/met_ingest.yaml'))
    bucket = config['raw_data_bucket']
    ftp_host = config['ftp_host']
    files = config['remote_path']

    # setup the arg parser
    parser = ArgumentParser(description='Download MET data')
    parser.add_argument('--lag', help='time lag in days (not compatible with --date)', type=int)
    parser.add_argument('--date', help='specific date to download YYYYMMDD (not compatible with --lag)')
    parser.add_argument('--host', help='download from specified FTP host', type=str, default=ftp_host)
    parser.add_argument('--remote-path', help='remote path template for FTP server', default=','.join(files))
    parser.add_argument('--s3-bucket', help='store in this bucket', default=bucket)
    args = parser.parse_args()

    # validate that one and only one of the two options was specified
    if args.lag and args.date:
        log.error('Only one of --lag and --date must be provided, but not both')
        return
    if not args.lag and not args.date:
        log.error('One of --lag or --date must be provided')
        return

    # compute or get the date string
    if args.lag:
        date = compute_date_from_lag(args.lag)
    else:
        date = args.date

    # download and save the file
    remote_paths = args.remote_path.split(',')
    s3_urls = download_met(date, args.host, remote_paths, args.s3_bucket)

    if s3_urls is not None:
        log.info('Files saved to:')
        for s3_url in s3_urls:
            log.info('  %s' % s3_url)


if __name__ == '__main__':
    main()
