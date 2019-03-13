import os
import time
import datetime
import urllib3
import re


def get_list_of_files_from_url(url):
    """
    Retrieve a list of files available at this URL
    :param url: The base URL to the GMAO download portal
    :return: {list} A list of files at this URL (file name only), or None if an error occurred
    """
    # read the data on the website with a GET request
    https = urllib3.PoolManager()
    response = https.request('GET', url)
    if response.status != 200:
        print('Website responded with %d' % response.status)
        print('URL: %s' % url)
        print(response.data.decode())
        return None

    # parse the file names from the data
    data = response.data.decode()
    files = re.findall('f522.*?\.ods', data, re.MULTILINE)
    return list(set(files))


def download_file(url, output_file):
    """
    Download a file from the website
    :param url: {str} The file url
    :param output_file: The output file
    :return: {bool} True if file was downloaded
    """
    # ensure the local path exists
    local_path = output_file[:output_file.rfind('/')]
    if not os.path.exists(local_path):
        os.makedirs(local_path)

    # read the data from the URL
    https = urllib3.PoolManager()
    response = https.request('GET', url)

    # check that the response is OK (200)
    if not response.status == 200:
        print('Website responded with %d' % response.status)
        print('URL: %s' % url)
        print(response.data.decode())
        return False

    # write the data to a file
    file = open(output_file, 'wb')
    file.write(response.data)
    file.close()

    # happy
    return True


def main(event, context):
    """
    The main lambda entry point, or main function if called stand-alone
    :param event: {NoneType} Not used, but required for Lambda
    :param context: {NoneType} Not used, but required for Lambda
    :return: None
    """
    # TODO: Delete this block once the environment is setup
    os.environ['LAG_IN_DAYS'] = '8'
    os.environ['HTTPS_HOST'] = 'portal.nccs.nasa.gov'
    os.environ['REMOTE_PATH'] = 'datashare/gmao_ops/pub/f522_fp/.internal/obs/Y%04d/M%02d/D%02d/H%02d/'

    log = {'ok': False, 'runtime': int(time.time()), 'size': -1, 'file_count': 0, 'name': 'n/a'}

    lag = int(os.environ['LAG_IN_DAYS'])
    https_host = os.environ['HTTPS_HOST']
    remote_path = os.environ['REMOTE_PATH']
    cycle_hour = 0

    # compute the base url with the date
    date = datetime.datetime.utcfromtimestamp(time.time() - lag * 86400)
    remote_path = remote_path % (date.year, date.month, date.day, cycle_hour)
    base_url = 'https://%s/%s' % (https_host, remote_path)
    files = get_list_of_files_from_url(base_url)

    # download the data files
    file_count = 0
    for remote_file in files:
        output_file = '/tmp/ods/Y%04d/M%02d/D%02d/H%02d/%s' % \
                      (date.year, date.month, date.day, cycle_hour, remote_file)
        file_count += 1 if download_file('%s/%s' % (base_url, remote_file), output_file) else 0

    print('Downloaded %d file.' % file_count)


if __name__ == '__main__':
    main(None, None)
