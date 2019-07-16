"""
FSOI Ingest NRL
"""
__all__ = ['download_nrl', 'process_nrl', 'download_and_process_nrl']


import os
import yaml
import pkgutil
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter as HelpFormatter
from fsoi.ingest.nrl.download_nrl import download_nrl
from fsoi.ingest.nrl.process_nrl import prepare_workspace
from fsoi.ingest.nrl.process_nrl import download_from_s3
from fsoi.ingest.nrl.process_nrl import process_nrl
from fsoi.ingest.nrl.process_nrl import upload_to_s3
from fsoi import log


def download_and_process_nrl():
    """
    Download NRL data and convert to HDF5 files
    :return: None
    """
    # load default values from the resource file
    config = yaml.full_load(pkgutil.get_data('fsoi', 'ingest/nrl/nrl_ingest.yaml'))
    bucket = config['raw_data_bucket']
    ftp_host = config['ftp_host']
    lag_in_days = config['lag_in_days']
    file = config['remote_path']
    output_bucket = config['processed_data_bucket']
    output_prefix = config['processed_data_prefix']

    # setup the arg parser
    parser = ArgumentParser(description='Download and process NRL', formatter_class=HelpFormatter)
    parser.add_argument('--lag', help='time lag in days', type=int, default=lag_in_days)
    parser.add_argument('--host', help='ftp-ex.nrlmry.navy.mil', type=str, default=ftp_host)
    parser.add_argument('--remote-path', help='Remote path template', default=file)
    parser.add_argument('--s3-bucket', help='Store in this bucket', default=bucket)
    parser.add_argument('--output-bucket', help='S3 for processed data', default=output_bucket)
    parser.add_argument('--output-prefix', help='S3 for processed data', default=output_prefix)
    args = parser.parse_args()

    # download the file from NRL
    input_file_s3_url = download_nrl(args.lag, args.host, args.remote_path, args.s3_bucket)

    # prepare the working directory
    workspace = prepare_workspace()
    if workspace is None:
        log.error('Failed to prepare workspace')
        return
    os.chdir(workspace)

    # download the input file from S3
    bzip_file = download_from_s3(input_file_s3_url)

    # process the NRL file
    date = bzip_file.split('_')[2][:-4]
    output_file = 'NRL.dry.%s.h5' % date
    processed_files = process_nrl(bzip_file, workspace, output_file, date)

    # upload the processed file to S3 target
    for processed_file in processed_files:
        target_url = 's3://%s/%s/%s' % ('fsoi', 'intercomp/hdf5/NRL', processed_file.split('/')[-1])
        log.debug('Uploading %s to %s' % (processed_file, target_url))
        if not upload_to_s3(processed_file, target_url):
            log.error('Failed to upload file to S3: aws s3 cp %s %s' % (processed_file, target_url))
