def ftp_download_file(host, remote_file, local_file=None):
    """
    Download a file from an FTP site anonymously
    :param host: FTP hostname
    :param remote_file: Full path to the remote file
    :param local_file: Full path to the local file
    :return: None
    """
    from ftplib import FTP

    # connect and login
    ftp = FTP(host)
    ftp.login()
    ftp.makepasv()

    # parse file names
    remote_dir = remote_file[0:remote_file.rfind('/')]
    remote_file_only = remote_file[1+remote_file.rfind('/'):]
    if local_file is None:
        local_file = '/tmp/' + remote_file_only

    # log info
    print('attempting to download ftp://%s/%s' % (host, remote_file))

    # download the remote file
    ftp.cwd(remote_dir)
    out = open(local_file, 'wb')
    ftp.retrbinary('RETR ' + remote_file_only, out.write)

    return local_file


def main(event, context):
    import os
    import time
    import datetime
    import json
    import boto3

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

        # check the response and print our CloudWatch information
        log['ok'] = True
        print(json.dumps(log))

    except Exception as e:
        print(e)
        print(json.dumps(log))


if __name__ == '__main__':
    main(None, None)
