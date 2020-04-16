"""
Check that the expected MERRA2 data exist
"""
from fsoi.data.s3_datastore import FsoiS3DataStore


def get_expected_data_list():
    """
    Create a list of data descriptors for MERRA2 that are expected to be found
    :return: {list} List of data descriptors
    """
    descriptors = []
    for year in range(1980, 2020):
        for month in [1, 7]:
            for day in range(1,32):
                dt = '%04d%02d%02d%02d' % (year, month, day, 0)
                for type in [None, 'groupbulk', 'accumbulk', 'bulk']:
                    descriptor = FsoiS3DataStore.create_descriptor('MERRA2', 'moist', datetime=dt, type=type)
                    descriptors.append(descriptor)

    return descriptors


def main():
    """
    Check that the expected data exist in S3.  Print a list of dates that are missing.
    :return: None
    """
    # get a list of expected data descriptors
    descriptors = get_expected_data_list()

    # create a datastore object for FSOI
    datastore = FsoiS3DataStore()

    # check that each data descriptor exists
    missing_count = 0
    missing_dates = set()
    for descriptor in descriptors:
        if not datastore.data_exist(descriptor):
            print(descriptor['datetime'])
            missing_dates.add(descriptor['datetime'])
            missing_count += 1

    # print out the commands to process the missing date
    for missing_date in missing_dates:
        print('process_merra --date %s --path /data/MERRA --norm moist' % missing_date)

    print('Total missing: %d of %d' % (missing_count, len(descriptors)))


if __name__ == '__main__':
    main()
