"""
FSOI Ingest GMAO
"""
__all__ = ['download_gmao', 'process_gmao', 'download_and_process_gmao']


import yaml
import pkgutil
import datetime
import time
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter as HelpFormatter
from fsoi.ingest.gmao.download_gmao import download_gmao
from fsoi.ingest.gmao.process_gmao import process_gmao
from fsoi import log


def download_and_process_gmao():
    """
    Download GMAO data and convert to HDF5 files
    :return: None
    """
    # read default parameter values from GMAO config file
    config = yaml.full_load(pkgutil.get_data('fsoi', 'resources/fsoi/ingest/gmao/gmao_ingest.yaml'))
    lag = config['lag_in_days']
    https_host = config['https_host']
    remote_path = config['remote_path']
    bucket = config['raw_data_bucket']
    cycle_hour = 0

    # parse the command line parameters
    parser = ArgumentParser(description='Download GMAO data', formatter_class=HelpFormatter)
    parser.add_argument('--lag', help='download data from N days ago', type=int, default=lag)
    parser.add_argument('--host', help='portal.nccs.nasa.gov', type=str, default=https_host)
    parser.add_argument('--remote-path', help='Remote path template', default=remote_path)
    parser.add_argument('--bucket-name', help='S3 bucket name', default=bucket)
    parser.add_argument('--norm', help='Norm', default='moist', type=str, choices=['dry', 'moist'])
    parser.add_argument('--cycle-hour', help='Forecast cycle hour', type=int, default=cycle_hour,
                        choices=[0, 6, 12, 18])
    args = parser.parse_args()

    # get the values from the command line parameters
    lag = args.lag
    https_host = args.host
    remote_path = args.remote_path
    bucket = args.bucket_name
    cycle_hour = args.cycle_hour
    norm = args.norm
    date = datetime.datetime.utcfromtimestamp(time.time() - lag * 86400)
    date_str = '%04d%02d%02d%02d' % (date.year, date.month, date.day, cycle_hour)

    files = download_gmao(lag, https_host, remote_path, bucket, cycle_hour)
    processed_files = process_gmao(norm, date_str)

    if files and processed_files:
        log.info('Ingest completed.')
