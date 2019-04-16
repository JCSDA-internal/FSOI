"""
This script will take input and output locations (both S3 urls) and convert a raw navy FSOI
file to an HDF5 file that can be used by the IOS webapp.  This script is intended to run in
a docker container in AWS Batch.
"""

import os
import sys
import shutil
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter as ArgDefault
import boto3


def parse_args():
    """
    Parse and validate the provided command line parameters
    :return: {argparse.Namespace} The parsed parameters
    """
    # parse the command line parameters
    app_description = 'Convert raw NRL files to HDF5 format'
    parser = ArgumentParser(description=app_description, formatter_class=ArgDefault)
    parser.add_argument('--date', help='yyyyMMddHH', type=str, required=True)
    parser.add_argument('--output', help='S3 url for output data', type=str, required=True)
    args = parser.parse_args()

    # validate the command line parameters
    if not args.output.startswith('s3://'):
        print('output parameter must be an S3 url: ' + args.output)
        exit(-1)
    if len(args.date) != 10:
        print('date parameter must be in the format yyyyMMddHH')
        exit(-1)
    return args


def prepare_workspace():
    """
    Prepare workspace
    :return: {str} Full path to the workspace, or None if could not create
    """
    try:
        work_dir = '/tmp/work'
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)
        os.makedirs(work_dir)
        return work_dir
    except Exception as e:
        print('Failed to create workspace: /tmp/work')
        print(e)
        return None


def download_from_s3(s3url):
    """
    Download all of the S3 objects with the given URL prefix
    :param s3url: {str} The S3 URL prefix
    :return: {list} A list of local files, or None if there was an error
    """
    # create an s3 client
    s3 = boto3.client('s3')

    # parse a few things from the url
    bucket = s3url.split('/')[2]
    prefix = s3url.split(bucket + '/')[1]

    # list the objects in the bucket at the prefix
    response = s3.list_objects(
        Bucket=bucket,
        Prefix=prefix
    )

    # check for an error response
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        print('Error listing objects in bucket: %s' % s3url)
        return None

    # local directory
    local_dir = '/tmp/work/%s' % prefix[0:-4]

    # ensure the local directory exists
    os.makedirs(local_dir, exist_ok=True)

    # download each of the objects to a local file
    files = []
    for object_data in response['Contents']:
        # get the key and local file
        key = object_data['Key']
        local_file = key.split('/')[-1]
        full_local_file_path = '%s/%s' % (local_dir, local_file)

        # download the data object from S3 to a file
        with open(full_local_file_path, 'wb') as file:
            s3.download_fileobj(bucket, key, file)
            file.close()
            files.append(full_local_file_path)

    return files


def upload_to_s3(file, s3url):
    """
    Upload a file to S3
    :param file: Path to the local file
    :param s3url: An S3 URL for the target
    :return: True if successful, otherwise false
    """
    try:
        # create an s3 client
        s3 = boto3.client('s3')

        # parse a few things from the url
        bucket = s3url.split('/')[2]
        key = s3url.split(bucket + '/')[1]

        # upload the file to the S3 bucket
        with open(file, 'rb') as file:
            s3.upload_fileobj(file, bucket, key)
        return True

    except Exception as e:
        print('Failed to upload file to S3: %s to %s' % (file, s3url))
        return False


def main():
    """
    Convert a raw navy file to an HDF5 file
    :return: None
    """
    # parse and validate the command line parameters
    args = parse_args()

    # prepare the working directory
    workspace = prepare_workspace()
    if workspace is None:
        print('Failed to prepare workspace')
        return
    os.chdir(workspace)

    # download the input files from S3
    y = int(args.date[0:4])
    m = int(args.date[4:6])
    d = int(args.date[6:8])
    h = int(args.date[8:10])
    s3url = 's3://fsoi-gmao-ingest/Y%04d/M%02d/D%02d/H%02d' % (y, m, d, h)
    file_list = download_from_s3(s3url)
    input_dir = file_list[0][:file_list[0].rfind('/')]

    # run the process_NRL.py script
    from process_GMAO import main as process_gmao_main
    output_file = 'GMAO.moist.%s.h5' % args.date
    sys.argv = ('script -i %s -o %s -a %s -n moist' % ('/tmp/work', output_file, args.date)).split()
    process_gmao_main()

    # upload the processed file to S3 target
    upload_to_s3(output_file, args.output)


if __name__ == '__main__':
    main()
