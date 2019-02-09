"""
This script will take input and output locations (both S3 urls) and convert a raw navy FSOI
file to an HDF5 file that can be used by the IOS webapp.  This script is intended to run in
a docker container in AWS Batch.
"""

import os
import sys
import shutil
import bz2
import gzip
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
    parser.add_argument('--input', help='S3 url for input data', type=str, required=True)
    parser.add_argument('--output', help='S3 url for output data', type=str, required=True)
    args = parser.parse_args()

    # validate the command line parameters
    if not args.input.startswith('s3://'):
        print('input parameter is not a valid S3 URL: ' + args.input)
        exit(-1)
    if not args.input.endswith('.bz2'):
        print('input parameter must point to a bz2 S3 object: ' + args.input)
        exit(-1)
    if not args.output.startswith('s3://'):
        print('output parameter is not a valid S3 URL: ' + args.output)
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
    Download a BZ2 object from S3 and uncompress it
    :param s3url: {str} The S3 URL
    :return: {str}
    """
    # create an s3 client
    s3 = boto3.client('s3')

    # parse a few things from the url
    input_name = s3url.split('/')[-1]
    bucket = s3url.split('/')[2]
    key = s3url.split(bucket + '/')[1]

    # download the data object from S3 to a file
    with open(input_name, 'wb') as file:
        s3.download_fileobj(bucket, key, file)
        file.close()

    # bunzip2 the data file
    with gzip.open(input_name[0:-4] + '.gz', 'wb') as out, bz2.BZ2File(input_name, 'rb') as inp:
        for data in iter(lambda: inp.read(102400), b''):
            out.write(data)

    return input_name[0:-4] + '.gz'


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

    # download the input file from S3
    gzip_file = download_from_s3(args.input)

    # run the process_NRL.py script
    from process_NRL import main as process_nrl_main
    date = gzip_file.split('_')[2][:-3]
    output_file = 'NRL.dry.%s.h5' % date
    sys.argv = ('script -i %s -o %s -a %s' % (gzip_file, output_file, date)).split()
    process_nrl_main()

    # upload the processed file to S3 target
    upload_to_s3(output_file, args.output)


if __name__ == '__main__':
    main()
