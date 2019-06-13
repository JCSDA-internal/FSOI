"""
This class will be used to interface with an S3 data store.
"""

import os
import boto3
import botocore
import urllib3
import certifi
import tempfile
from ftplib import FTP
from fsoi.data.datastore import DataStore
from fsoi import log


class S3DataStore(DataStore):
    """
    Interface with an S3 data store.  The 'target' and 'source' parameters passed to these methods
    must be dictionaries that contain either: 1) 'bucket' and 'key' attributes; or 2) 'bucket',
    'prefix', and 'name' attributes.
    """
    # the static s3 client
    s3_client = None

    @staticmethod
    def __validate_descriptor(descriptor):
        """
        Validate the descriptor object
        :param descriptor: {dict} Data 'target' or 'source' descriptor
        :return: True if valid, otherwise False
        """
        if not isinstance(descriptor, dict):
            log.error('Descriptor type is invalid: %s' % type(descriptor).__name__)
            return False

        if 'bucket' in descriptor and 'key' in descriptor:
            return True

        if 'bucket' in descriptor and 'prefix' in descriptor and 'name' in descriptor:
            return True

        return False

    @staticmethod
    def __to_bucket_and_key(descriptor):
        """
        Get the bucket and key from the data descriptor
        :param descriptor: {dict} A 'target' or 'source' data descriptor
        :return: ({str}, {str}) A tuple with bucket and key, or None if descriptor is invalid
        """
        if 'bucket' in descriptor and 'key' in descriptor:
            return descriptor['bucket'], descriptor['key']

        if 'bucket' in descriptor and 'prefix' in descriptor and 'name' in descriptor:
            key = descriptor['prefix'] + '/' + descriptor['name']
            while '//' in key:
                key = key.replace('//', '/')
            return descriptor['bucket'], key

        return None

    @staticmethod
    def __get_s3_client():
        """
        Get an S3 client
        :return: S3 client
        """
        if S3DataStore.s3_client is None:
            S3DataStore.s3_client = boto3.client('s3')
        return S3DataStore.s3_client

    def save_from_http(self, url, target):
        """
        Save data from the URL to the data store
        :param url: {str} URL with HTTPS or HTTP protocol
        :param target: {dict} A dictionary with attributes to describe the data store target
        :return: {bool} True if successful, otherwise False
        """
        try:

            # validate the URL parameter
            if not url.startswith('http://') and not url.startswith('https://'):
                log.error('Invalid url, expecting http://... or https://...')
                return False

            # validate the target
            if not self.__validate_descriptor(target):
                return False

            # read the data from the URL
            https = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
            response = https.request('GET', url)

            # check that the response is OK (200)
            if response.status != 200:
                log.error('Website responded with %d' % response.status)
                log.error('URL: %s' % url)
                log.error(response.data.decode())
                return False

            # write the data to S3
            (bucket, key) = self.__to_bucket_and_key(target)
            s3_client = self.__get_s3_client()
            s3_response = s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=response.data
            )

            # check for an error in the response
            if s3_response['ResponseMetadata']['HTTPStatusCode'] != 200:
                log.error('Error uploading data to S3')
                log.error('URL: %s' % url)
                log.error('S3 URL: s3://%s/%s' % (bucket, key))
                return

            # happy
            return True

        except Exception as e:
            log.error('Failed to save data from URL: %s' % url, e)
            return False

    def save_from_ftp(self, url, target):
        """
        Save data from the URL to the data store
        :param url: {str} URL with FTP protocol
        :param target: {dict} A dictionary with attributes to describe the data store target
        :return:
        """
        try:

            # validate the url
            if not url.startswith('ftp://'):
                log.error('Invalid URL, expecting ftp://...: %s' % url)
                return False

            # validate the target
            if not self.__validate_descriptor(target):
                return False

            # parse the URL
            host = url.split('/')[2]
            remote_file = url.split(host)[1][1:]

            # connect and login
            ftp = FTP(host)
            ftp.login()
            ftp.makepasv()

            # parse file names
            remote_dir = remote_file[0:remote_file.rfind('/')]
            remote_file_only = remote_file[1 + remote_file.rfind('/'):]
            local_file = tempfile.mktemp()

            # download the remote file
            ftp.cwd(remote_dir)
            out = open(local_file, 'wb')
            ftp.retrbinary('RETR ' + remote_file_only, out.write)

            # upload the file to S3
            uploaded = self.save_from_local_file(local_file, target)

            # clean up and return
            if uploaded:
                os.remove(local_file)
            return uploaded

        except Exception as e:
            log.error('Failed to save data from URL: %s' % url, e)
            return False

    def save_from_local_file(self, local_file, target):
        """
        Save data to the data store from a local file
        :param local_file: {str} Full path to the local file
        :param target: {dict} A dictionary with attributes to describe the data store target
        :return: {bool} True if successful, otherwise False
        """
        try:
            # validate the target descriptor
            if not self.__validate_descriptor(target):
                return False

            # ensure that the target has bucket and key attributes
            bucket, key = self.__to_bucket_and_key(target)

            # get an S3 client
            s3_client = self.__get_s3_client()

            # upload the data to S3
            s3_client.upload_file(Filename=local_file, Bucket=bucket, Key=key)

            # check to see if the target exists
            return self.data_exist(target)

        except Exception as e:
            log.error('Failed to save data from local file', e)
            return False

    def load_to_local_file(self, source, local_file):
        """
        Load data from the data store to a local file
        :param source: {dict} A dictionary with attributes to describe the data store source
        :param local_file: {str} Full path to the local file (directories will be created if they
                                 do not already exist.
        :return: True if successful, otherwise False
        """
        try:
            # validate the source descriptor
            if not self.__validate_descriptor(source):
                return False

            # get the bucket and key from the descriptor
            bucket, key = self.__to_bucket_and_key(source)

            # ensure that the local directory exists
            local_dir = local_file[:local_file.rfind('/')]
            os.makedirs(local_dir, exist_ok=True)

            # get the S3 client
            s3_client = self.__get_s3_client()

            # download the data from S3 to a file
            s3_client.download_file(Bucket=bucket, Key=key, Filename=local_file)

            # check that the file was created
            return os.path.exists(local_file)

        except Exception as e:
            log.error('Failed to download data to local file', e)

    def list_data_store(self, filters):
        """
        Get a list of available data
        :param filters: {dict} This dictionary must have attributes: 'bucket' and 'prefix'
        :return: {list} A list of dictionaries that describe data sources, or None
        """
        try:
            # get the s3 pager
            s3_client = self.__get_s3_client()
            s3_pager = s3_client.get_paginator('list_objects')

            # validate the filters
            if 'bucket' not in filters or 'prefix' not in filters:
                log.error('Filters must contain bucket and prefix attributes')
                return False

            # extract the filter values
            bucket = filters['bucket']
            prefix = filters['prefix']

            # list the data objects in the S3 bucket
            response = s3_pager.paginate(
                Bucket=bucket,
                Prefix=prefix,
                PaginationConfig={
                    'PageSize': 1000
                }
            ).build_full_result()

            # return an empty list if there are no results
            if 'Contents' not in response:
                return []

            # create a list of S3 keys
            contents = response['Contents']
            sources = []
            for item in contents:
                sources.append({
                    'bucket': bucket,
                    'key': item['Key']
                })

            return sources

        except Exception as e:
            log.error('Failed to list data store', e)
            return None

    def data_exist(self, target):
        """
        Check if the specified target exists
        :param target: {dict} A dictionary with attributes to describe the data store target
        :return: True if the target exists, otherwise False, raise Exception if failed
        """
        try:
            # validate the target
            if not self.__validate_descriptor(target):
                return False

            # get the bucket and key from the target
            bucket, key = self.__to_bucket_and_key(target)

            # get the S3 client
            s3_client = self.__get_s3_client()

            # check if the target exists in the S3 bucket
            response = s3_client.head_object(Bucket=bucket, Key=key)

            # check the response (successful response indicates target exists)
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                return True

            # target does not exist
            return False

        except botocore.exceptions.ClientError as ce:
            return False

        except Exception as e:
            log.error('Failed to check if target exists')
            return False

    def delete(self, target):
        """
        Delete the specified target from the data store
        :param target: {dict} A dictionary with attributes to describe the data store target
        :return: True if successfully deleted, otherwise False
        """
        try:
            # validate the target
            if not self.__validate_descriptor(target):
                return False

            # get the bucket and key from the target
            bucket, key = self.__to_bucket_and_key(target)

            # ensure that the target exists
            if not self.data_exist(target):
                log.warn('Trying to delete a non-existant target: s3://%s/%s' % (bucket, key))
                return False

            # get the S3 client
            s3_client = self.__get_s3_client()

            # delete the
            response = s3_client.delete_object(Bucket=bucket, Key=key)

            # check the response (successful response indicates target exists)
            response_code = response['ResponseMetadata']['HTTPStatusCode']
            if response_code >= 200 and response_code < 300:
                return True

            # delete request failed
            return False
        except Exception as e:
            log.error('Failed to delete target: s3://%s/%s' % self.__to_bucket_and_key(target))
            return False
