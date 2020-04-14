"""
These are generic data store classes and methods
"""

from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
from fsoi import log


class DataStore:
    """
    Abstract class that defines the FSOI data store interface.  In general, save_* methods are
    writing data to a data store, and load_* methods are retrieving data from a data store.
    """
    def save_from_http(self, url, target):
        """
        Save data from the URL to the data store
        :param url: {str} URL with HTTPS or HTTP protocol
        :param target: {dict} A dictionary with attributes to describe the data store target
        :return: {bool} True if successful, otherwise False
        """
        raise NotImplementedError('save_from_http not implemented')
    
    def save_from_ftp(self, url, target):
        """
        Save data from the URL to the data store
        :param url: {str} URL with FTP protocol
        :param target: {dict} A dictionary with attributes to describe the data store target
        :return: 
        """
        raise NotImplementedError('save_from_ftp not implemented')

    def save_from_local_file(self, local_file, target):
        """
        Save data to the data store from a local file
        :param local_file: {str} Full path to the local file
        :param target: {dict} A dictionary with attributes to describe the data store target
        :return: {bool} True if successful, otherwise False
        """
        raise NotImplementedError('save_from_local_file not implemented')

    def load_to_local_file(self, source, local_file):
        """
        Load data from the data store to a local file
        :param source: {dict} A dictionary with attributes to describe the data store source
        :param local_file: {str} Full path to the local file (directories will be created if they
                                 do not already exist.
        :return: True if successful, otherwise False
        """
        raise NotImplementedError('load_to_local_file not implemented')

    def list_data_store(self, filters):
        """
        Get a list of available data
        :param filters: {dict} A dictionary with options for filtering the data sources
        :return: {list} A list of dictionaries that describe data sources
        """
        raise NotImplementedError('list_data_store not implemented')

    def data_exist(self, target):
        """
        Check if the specified target exists
        :param target: {dict} A dictionary with attributes to describe the data store target
        :return: True if the target exists, otherwise False
        """
        raise NotImplementedError('data_exist not implemented')

    def delete(self, target):
        """
        Delete the specified target from the data store
        :param target: {dict} A dictionary with attributes to describe the data store target
        :return: True if successfully deleted, otherwise False
        """
        raise NotImplementedError('delete not implemented')


class DataStoreOperation:
    """
    This class will perform a data store operation on a separate thread
    """
    # define the valid operations
    valid_operations = [
        'data_exist',
        'delete',
        'list_data_store',
        'load_to_local_file',
        'save_from_local_file',
        'save_from_http',
        'save_from_ftp'
    ]

    def __init__(self, datastore, operation, parameters):
        """
        Create a DataStoreOperation object
        :param datastore: {DataStore} The data store to use for the operation
        :param operation: {str} @see valid_operations
        :param parameters: {list} List of parameters to the operation
        """
        # call the super constructor
        Thread.__init__(self)

        # initialize return values
        self.started = False
        self.finished = False
        self.success = False
        self.response = None

        # save the parameters
        self.datastore = datastore
        self.operation = operation
        self.parameters = parameters

        # validate the parameters
        if datastore is None or not isinstance(datastore, DataStore):
            raise TypeError('datastore is invalid: %s' % type(datastore))
        if operation not in DataStoreOperation.valid_operations:
            raise ValueError('operation is invalid: %s' % operation)

    def run(self):
        """
        Run the data store operation
        :return: None
        """
        # mark the thread as started
        self.started = True

        # get the function
        function = getattr(self.datastore, self.operation)

        # execute the function
        try:
            if self.operation in ['data_exist', 'delete', 'list_data_store']:
                self.response = function(self.parameters[0])
            else:
                self.response = function(self.parameters[0], self.parameters[1])

        except Exception as e:
            # log any exceptions
            log.error('Failed to execute DataStoreOperation: %s => %s' %
                      (self.operation, ','.join(self.parameters)), e)

            # mark thread as failed and finished
            self.success = False
            self.finished = True
            return

        # mark the thread as successful and finished
        self.success = True
        self.finished = True


class ThreadedDataStore(DataStore):
    """
    This class will manage a thread pool to process DataStoreOperations
    """
    def __init__(self, backing_datastore, thread_pool_size):
        """
        Initialize the thread pool
        :param backing_datastore: {DataStore} Data store object that will be doing the actual work
        :param thread_pool_size: {int} The number of threads to run
        """
        self.operations = []
        self.datastore = backing_datastore
        self.thread_pool = ThreadPoolExecutor(max_workers=thread_pool_size)
        self.futures = []
        self.errors = []

    def join(self):
        """
        Wait for all operations to finish
        :return: None
        """
        wait(self.futures)
        self.futures.clear()

    def save_from_http(self, url, target):
        """
        Save data from the URL to the data store
        :param url: {str} URL with HTTPS or HTTP protocol
        :param target: {dict} A dictionary with attributes to describe the data store target
        :return: {bool} True if successful, otherwise False
        """
        operation = DataStoreOperation(self.datastore, 'save_from_http', [url, target])
        self.operations.append(operation)
        self.futures.append(self.thread_pool.submit(operation.run))

    def save_from_ftp(self, url, target):
        """
        Save data from the URL to the data store
        :param url: {str} URL with FTP protocol
        :param target: {dict} A dictionary with attributes to describe the data store target
        :return:
        """
        operation = DataStoreOperation(self.datastore, 'save_from_ftp', [url, target])
        self.operations.append(operation)
        self.futures.append(self.thread_pool.submit(operation.run))

    def save_from_local_file(self, local_file, target):
        """
        Save data to the data store from a local file
        :param local_file: {str} Full path to the local file
        :param target: {dict} A dictionary with attributes to describe the data store target
        :return: {bool} True if successful, otherwise False
        """
        operation = DataStoreOperation(self.datastore, 'save_from_local_file', [local_file, target])
        self.operations.append(operation)
        self.futures.append(self.thread_pool.submit(operation.run))

    def load_to_local_file(self, source, local_file):
        """
        Load data from the data store to a local file
        :param source: {dict} A dictionary with attributes to describe the data store source
        :param local_file: {str} Full path to the local file (directories will be created if they
                                 do not already exist.
        :return: True if successful, otherwise False
        """
        operation = DataStoreOperation(self.datastore, 'load_to_local_file', [source, local_file])
        self.operations.append(operation)
        self.futures.append(self.thread_pool.submit(operation.run))

    def list_data_store(self, filters):
        """
        Get a list of available data
        :param filters: {dict} A dictionary with options for filtering the data sources
        :return: {list} A list of dictionaries that describe data sources
        """
        operation = DataStoreOperation(self.datastore, 'list_data_store', [filters])
        self.operations.append(operation)
        self.futures.append(self.thread_pool.submit(operation.run))

    def data_exist(self, target):
        """
        Check if the specified target exists
        :param target: {dict} A dictionary with attributes to describe the data store target
        :return: True if the target exists, otherwise False
        """
        operation = DataStoreOperation(self.datastore, 'data_exist', [target])
        self.operations.append(operation)
        self.futures.append(self.thread_pool.submit(operation.run))

    def delete(self, target):
        """
        Delete the specified target from the data store
        :param target: {dict} A dictionary with attributes to describe the data store target
        :return: True if successfully deleted, otherwise False
        """
        operation = DataStoreOperation(self.datastore, 'delete', [target])
        self.operations.append(operation)
        self.futures.append(self.thread_pool.submit(operation.run))
