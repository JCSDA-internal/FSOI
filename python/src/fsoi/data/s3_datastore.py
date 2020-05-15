"""
This class will be used to interface with an S3 data store.
"""

import os
import boto3
import botocore.exceptions
import urllib3
import certifi
import tempfile
import pkgutil
import yaml
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
    def _validate_descriptor(descriptor):
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
    def _to_bucket_and_key(descriptor):
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
    def _to_public_url(descriptor):
        """
        Get the public URL for the object (permissions must already be set)
        :param descriptor: {dict} A 'target' or 'source' data descriptor
        :return: {str} Public URL to the S3 bucket (bucket must already be public)
        """
        region = os.environ['REGION']
        bucket, key = S3DataStore._to_bucket_and_key(descriptor)
        public_url = 'http://%s.s3-website-%s.amazonaws.com/%s' % (bucket, region, key)

        return public_url

    @staticmethod
    def __get_s3_client():
        """
        Get an S3 client
        :return: S3 client
        """
        if S3DataStore.s3_client is None:
            S3DataStore.s3_client = boto3.client('s3')
        return S3DataStore.s3_client

    @staticmethod
    def get_suggested_file_name(descriptor):
        """
        Get a suggested file name from the descriptor
        :param descriptor: {dict} A valid data descriptor
        :return: {str} A suggested file name
        """
        # return everything after the last slash character in the S3 key
        bucket, key = S3DataStore._to_bucket_and_key(descriptor)
        return key[key.rfind('/') + 1:]

    @staticmethod
    def descriptor_to_string(descriptor):
        """
        Get a human-readable string of the descriptor for logging and error message purposes
        :param descriptor: {dict} The data descriptor
        :return: {str} human-readable string
        """
        type = descriptor['type']
        center = descriptor['center']
        norm = descriptor['norm']
        date = descriptor['date'] if 'date' in descriptor else descriptor['datetime'][0:8]
        hour = descriptor['hour'] if 'hour' in descriptor else descriptor['datetime'][8:10]
        return 'type=%s, center=%s, norm=%s, date=%s, hour=%s' % (type, center, norm, date, hour)

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
            if not self._validate_descriptor(target):
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
            (bucket, key) = self._to_bucket_and_key(target)
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

    def save_from_ftp(self, url, target, username=None, password=None):
        """
        Save data from the URL to the data store
        :param url: {str} URL with FTP protocol
        :param target: {dict} A dictionary with attributes to describe the data store target
        :param username: {str} An optional username
        :param password: {str} An optional password
        :return: {boolean} True if successfully downloaded from FTP and uploaded to S3
        """
        try:

            # validate the url
            if not url.startswith('ftp://'):
                log.error('Invalid URL, expecting ftp://...: %s' % url)
                return False

            # validate the target
            if not self._validate_descriptor(target):
                return False

            # parse the URL
            host = url.split('/')[2]
            remote_file = url.split(host)[1][1:]

            # connect and login
            ftp = FTP(host)
            if username is not None:
                ftp.login(user=username, passwd=password)
            else:
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
            if not self._validate_descriptor(target):
                return False

            # ensure that the target has bucket and key attributes
            bucket, key = self._to_bucket_and_key(target)

            # get an S3 client
            s3_client = self.__get_s3_client()

            # upload the data to S3
            s3_client.upload_file(Filename=local_file, Bucket=bucket, Key=key)

            # check to see if the target exists
            return self.data_exist(target)

        except Exception as e:
            log.error('Failed to save data from local file')
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
            if not self._validate_descriptor(source):
                return False

            # verify that the data exist
            if not self.data_exist(source):
                return False

            # get the bucket and key from the descriptor
            bucket, key = self._to_bucket_and_key(source)

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
            log.error('Failed to download data to local file')
            print(e)

    def load(self, source):
        """
        Load data from the data store to memory
        :param source: {dict} A dictionary with attributes to describe the data store source
        :return: {bytes} S3 data, or None if unsuccessful
        """
        try:
            # validate the source descriptor
            if not self._validate_descriptor(source):
                return False

            # verify that the data exist
            if not self.data_exist(source):
                return False

            # get the bucket and key from the descriptor
            bucket, key = self._to_bucket_and_key(source)

            # get the S3 client
            s3_client = self.__get_s3_client()

            # download the data from S3 to a file
            from io import BytesIO
            bio = BytesIO()
            s3_client.download_fileobj(Bucket=bucket, Key=key, Fileobj=bio)

            # check that there was data returned
            data = bio.getvalue()
            return None if len(data) == 0 else data

        except Exception as e:
            log.error('Failed to download data to local file')
            print(e)

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
            return [{'bucket': bucket, 'key': item['Key']} for item in contents]

        except Exception as e:
            log.error('Failed to list data store')
            return None

    def data_exist(self, target):
        """
        Check if the specified target exists
        :param target: {dict} A dictionary with attributes to describe the data store target
        :return: True if the target exists, otherwise False, raise Exception if failed
        """
        try:
            # validate the target
            if not self._validate_descriptor(target):
                return False

            # get the bucket and key from the target
            bucket, key = self._to_bucket_and_key(target)

            # get the S3 client
            s3_client = self.__get_s3_client()

            # check if the target exists in the S3 bucket
            try:
                response = s3_client.head_object(Bucket=bucket, Key=key)
            except botocore.exceptions.ClientError:
                return False

            # check the response (successful response indicates target exists)
            return response['ResponseMetadata']['HTTPStatusCode'] == 200

        except botocore.exceptions.ClientError as ce:
            log.error('Failed to check if data exist')
            print(ce)
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
            if not self._validate_descriptor(target):
                return False

            # get the bucket and key from the target
            bucket, key = self._to_bucket_and_key(target)

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
            if 200 <= response_code < 300:
                return True

            # delete request failed
            return False

        except Exception as e:
            log.error('Failed to delete target: s3://%s/%s' % self._to_bucket_and_key(target), e)
            return False


class FsoiS3DataStore(S3DataStore):
    """
    Interface with an S3 data store specifically for FSOI data.  The 'target' and 'source'
    parameters passed to these methods must be dictionaries that contain either: 1) 'center',
    'norm', 'date', and 'hour' attributes; or 2) 'center', 'norm', and 'datetime' attributes.
    """
    @staticmethod
    def _validate_descriptor(descriptor):
        """
        Validate the descriptor object
        :param descriptor: {dict} Data 'target' or 'source' descriptor
        :return: True if valid, otherwise False
        """
        # descriptor must be a dictionary
        if not isinstance(descriptor, dict):
            log.error('Descriptor type is invalid: %s' % type(descriptor).__name__)
            return False

        # descriptor must contain center and norm
        if 'center' not in descriptor or 'norm' not in descriptor:
            return False

        # validate a descriptor with date and hour
        if 'date' in descriptor and 'hour' in descriptor:
            if not descriptor['date'].isnumeric() and len(descriptor['date']) != 8:
                return False
            if not descriptor['hour'].isnumeric() and len(descriptor['hour']) != 2:
                return False
            return True

        # validate a descriptor with datetime
        if 'datetime' in descriptor:
            if not descriptor['datetime'].isnumeric() and len(descriptor['datetime']) != 10:
                return False
            return True

        return False

    @staticmethod
    def _to_bucket_and_key(descriptor):
        """
        Get the bucket and key from the data descriptor
        :param descriptor: {dict} A 'target' or 'source' data descriptor
        :return: ({str}, {str}) A tuple with bucket and key, or None if descriptor is invalid
        """
        full_config = yaml.full_load(pkgutil.get_data('fsoi', 'data/datastore.yaml'))
        config = full_config['fsoi']['s3']

        bucket = config['bucket']

        # construct the type of file: None, groupbulk, bulk, or accumbulk
        data_type = descriptor['type'] + ('.' if descriptor['type'] is not '' else '')

        # create the key based on 'date' and 'hour' in the descriptor
        if 'date' in descriptor and 'hour' in descriptor:
            key = config['key'] % (
                descriptor['center'],
                data_type,
                descriptor['center'],
                descriptor['norm'],
                descriptor['date'],
                descriptor['hour']
            )
            return bucket, key

        # create the key based on 'datetime' in the descriptor
        if 'datetime' in descriptor:
            date = descriptor['datetime'][:8]
            hour = descriptor['datetime'][8:10]
            key = config['key'] % (
                descriptor['center'],
                data_type,
                descriptor['center'],
                descriptor['norm'],
                date,
                hour
            )
            return bucket, key

        return None

    @staticmethod
    def create_descriptor(center=None, norm=None, date=None, hour=None, datetime=None, type=None):
        """
        Convenience method to create a descriptor
        :param center: {str} The center name (NRL, GMAO, MET, MeteoFr, EMC, JMA_adj, or JMA_ens)
        :param norm: {str} The norm (dry or moist)
        :param date: {str} Date string YYYYMMDD (not compatible with datetime parameter)
        :param hour: {str} Hour string (00, 06, 12, or 18) (not compatible with datetime parameter)
        :param datetime: {str} Date/Time String YYYYMMDDHH (not compatible with date or hour parameters)
        :param type: {str} The statistics type: None, groupbulk, accumbulk, or bulk
        :return: Descriptor with given parameters
        """
        # check that options are compatible
        if datetime is not None and (date is not None or hour is not None):
            log.error('create_descriptor should be passed either [datetime] or [date AND hour]')
            return None

        # create the descriptor with common attributes
        descriptor = {'center': center, 'norm': norm}

        if datetime is not None:
            # add datetime if it was specified
            descriptor['datetime'] = datetime
        else:
            # add date and hour if they were specified
            descriptor['date'] = date
            descriptor['hour'] = hour

        # set the type value
        descriptor['type'] = type if type is not None else ''

        return descriptor

    @staticmethod
    def descriptor_to_string(descriptor):
        """
        Get a human-readable string of the descriptor for logging and error message purposes
        :param descriptor: {dict} The data descriptor
        :return: {str} human-readable string
        """
        bucket, key = S3DataStore._to_bucket_and_key(descriptor)
        return 'bucket=%s, key=%s' % (bucket, key)

    @staticmethod
    def get_suggested_file_name(descriptor):
        """
        Get a suggested file name from the descriptor
        :param descriptor: {dict} A valid data descriptor
        :return: {str} A suggested file name
        """
        # return everything after the last slash character in the S3 key
        bucket, key = FsoiS3DataStore._to_bucket_and_key(descriptor)
        return key[key.rfind('/') + 1:]
