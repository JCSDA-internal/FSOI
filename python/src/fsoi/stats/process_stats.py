"""
This utility will be useful to have around for a while, but should eventually be removed.
The 'process_stats' command will 1) do a listing of all objects in S3 for a given center; 2) check
to see if the bulk, accumbulk, and groupbulk stats have already been calculated; and if not, 3)
download the file, compute these statistics, and upload them to S3.
"""


import os
import sys
import boto3
from botocore.exceptions import ClientError
from fsoi.stats.lib_utils import readHDF
from fsoi.stats.lib_utils import writeHDF
from fsoi.stats.lib_obimpact import BulkStats
from fsoi.stats.lib_obimpact import accumBulkStats
from fsoi.stats.lib_obimpact import Platforms
from fsoi.stats.lib_obimpact import groupBulkStats


def list_files(center):
    """
    List all of the hdf5 files for the given center in S3
    :param center: The center
    :return: {list} List of S3 keys
    """
    s3 = boto3.client('s3')
    response = s3.list_objects(
        Bucket='fsoi',
        Prefix='intercomp/hdf5/%s' % center
    )

    contents = response['Contents']
    keys = []
    for item in contents:
        keys.append(item['Key'])

    return keys


def process_file(key, center):
    """
    Download a data from S3 and process the file
    :param key: The key in S3 (fsoi bucket)
    :param center: The center name
    :return: None
    """
    prefix = '/'.join(key.split('/')[0:-1])
    name = key.split('/')[-1]
    if not name.startswith(center):
        print('  Ignoring invalid file type: %s' % key)
        return

    # get an S3 client
    s3 = boto3.client('s3')

    # make sure this has not been processed already
    try:
        response = s3.head_object(
            Bucket='fsoi',
            Key='%s/%s.%s' % (prefix, 'groupbulk', name)
        )
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print('  Already processed %s' % key)
            return
    except ClientError as ignore:
        pass

    # download an S3 object
    print('  Downloading %s' % key)
    s3.download_file(
        Bucket='fsoi',
        Key=key,
        Filename='/tmp/%s/file.h5' % center
    )

    # process the data
    print('  Processing %s' % key)
    df0 = readHDF('/tmp/%s/file.h5' % center, 'df')
    df1 = BulkStats(df0)
    writeHDF('/tmp/%s/bulk.file.h5' % center, 'df', df1)
    df2 = accumBulkStats(df1)
    writeHDF('/tmp/%s/accumbulk.file.h5' % center, 'df', df2)
    platforms = Platforms(center)
    df3 = groupBulkStats(df2, platforms)
    writeHDF('/tmp/%s/groupbulk.file.h5' % center, 'df', df3)
    del df0, df1, df2, df3

    # upload the processed data to S3
    os.remove('/tmp/%s/file.h5' % center)
    for type in ['bulk', 'accumbulk', 'groupbulk']:
        print('  Uploading %s/%s.%s' % (prefix, type, name))
        s3.upload_file(
            Filename='/tmp/%s/%s.file.h5' % (center, type),
            Bucket='fsoi',
            Key='%s/%s.%s' % (prefix, type, name)
        )
        os.remove('/tmp/%s/%s.file.h5' % (center, type))


def main():
    center = sys.argv[1]
    keys = list_files(center)

    os.makedirs('/tmp/%s' % center, exist_ok=True)

    # for key in keys:
    for key in keys:
        try:
            process_file(key, center)
        except Exception as e:
            print('Failed to process %s' % key)
            print(e)


if __name__ == '__main__':
    main()
