import os
import tempfile
from fsoi.data.s3_datastore import S3DataStore
from fsoi.data.datastore import DataStoreOperation


def test_s3_datastore():
    """
    Test the datastore operations with the S3 class
    :return: None
    """
    run_datastore_operations(S3DataStore())


def test_datastore_operation():
    """
    Test the DataStoreOperation class, which is a thread
    :return: None
    """
    list_filter = {'bucket': 'jcsda-scratch', 'prefix': ''}
    operation = DataStoreOperation(S3DataStore(), 'list_data_store', [list_filter])
    operation.run()
    assert operation.started
    assert operation.finished
    assert operation.success
    assert isinstance(operation.response, list)
    assert len(operation.response) > 0


def run_datastore_operations(ds):
    """
    Run a number of datastore operations on the given datastore object
    :param ds: {DataStore} The data store object to test
    :return: None
    """
    # create a file to use for testing
    data = 'i will now focus its radiation on a giant medium-sized ant to see what happens'
    local_file = tempfile.mktemp()
    with open(local_file, 'w') as fs:
        fs.write(data)
        fs.close()
    assert os.path.exists(local_file)

    # create a descriptor for this data in the data store
    descriptor = {'bucket': 'jcsda-scratch', 'key': 'fsoi-test/datastore-test-data'}

    # delete the desciptor without checking the return code so we start fresh (data may be left
    # over from a failed previous test)
    ds.delete(descriptor)

    # the data should not exist in the data store
    assert not ds.data_exist(descriptor)

    # the data store list should be empty
    list_filter = {'bucket': 'jcsda-scratch', 'prefix': 'fsoi-test'}
    available_descriptors = ds.list_data_store(list_filter)
    assert len(available_descriptors) == 0

    # save the local file to the data store
    assert ds.save_from_local_file(local_file, descriptor)

    # verify that the file was copied to the data store
    assert ds.data_exist(descriptor)

    # copy from the data store to the local file
    local_file2 = tempfile.mktemp()
    assert ds.load_to_local_file(descriptor, local_file2)
    with open(local_file2) as fs:
        data2 = fs.read()
        fs.close()
    assert data == data2

    # delete from the data store
    assert ds.delete(descriptor)

    # save to the data store from an http url
    assert ds.save_from_http('https://www.google.com', descriptor)

    # should find one descriptor when we list them here
    available_descriptors = ds.list_data_store(list_filter)
    assert len(available_descriptors) == 1

    # delete from the data store
    assert ds.delete(descriptor)

    # should not find any descriptors here
    available_descriptors = ds.list_data_store(list_filter)
    assert len(available_descriptors) == 0
