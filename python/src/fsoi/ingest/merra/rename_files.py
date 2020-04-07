"""
The MERRA2 files are in directories that are labeled 9 hours behind what they should be.  This script will rename
all of the directories to the correct date and time.
"""


def rename_merra_files():
    """
    Rename the MERRA directories by adding 9 hours
    :return: None
    """
    merra_dir = '/data/MERRA'
    dir_list = get_merra_dirs(merra_dir)

    for source in dir_list:
        target = get_time_adjusted_dir(source)
        if not move_merra_dir(target, source):
            print('Failed to move %s to %s' % (source, target))


def move_merra_dir(target, source):
    """
    Move the target directory to the source directory
    :param target: {str} Full directory name to move FROM
    :param source: {str} Full directory name to move TO
    :return: {bool} True if successfully moved
    """
    import os

    if os.path.exists(target):
        print('Will not overwrite %s with %s' % (target, source))
        return False

    if not os.path.exists(source):
        print('Source does not exist: %s' % source)
        return False

    target_parent = target[:target.rfind('/')]
    if not os.path.exists(target_parent):
        os.makedirs(target_parent, exist_ok=True)

    os.rename(source, target)

    return True


def get_merra_dirs(merra_dir):
    """
    Get all the YMDH subdirectores as a list
    :param merra_dir: {str} Root level directory for MERRA data
    :return: {list} List of strings that are the YMDH subdirectories for MERRA data
    """
    import os

    dir_list = []

    skipped = 0
    years = os.listdir(merra_dir)
    for year in years:
        if len(year) != 5 or not year.startswith('Y'):
            continue

        months = os.listdir('%s/%s' % (merra_dir, year))
        for month in months:
            if len(month) != 3 or not month.startswith('M'):
                continue

            days = os.listdir('%s/%s/%s' % (merra_dir, year, month))
            for day in days:
                if len(day) != 3 or not day.startswith('D'):
                    continue

                hours = os.listdir('%s/%s/%s/%s' % (merra_dir, year, month, day))
                for hour in hours:
                    if len(hour) != 3 or not hour.startswith('H'):
                        continue

                    dir_list.append('%s/%s/%s/%s/%s' % (merra_dir, year, month, day, hour))

    dir_list.sort(reverse=True)

    return dir_list


def get_time_adjusted_dir(dir, offset_hours=9):
    """
    Convert a YMDH subdirectory to the correct time given the subdirectory name and offset
    :param dir: {str} Subdirectory name in the format Yxxxx/Mxx/Dxx/Hxx
    :param offset_hours: {int} Number of hours to add to correct the time (defaults to +9 hours)
    :return: {str} New subdirectory name in the format Yxxxx/Mxx/Dxx/Hxx
    """
    import pytz
    from datetime import datetime as dt
    from datetime import timedelta as td

    tokens = dir.split('/')
    year = int(tokens[-4][1:])
    month = int(tokens[-3][1:])
    day = int(tokens[-2][1:])
    hour = int(tokens[-1][1:])

    a = pytz.utc.localize(dt(year, month, day, hour, 0, 0, 0))
    b = a + td(hours=offset_hours)

    tokens[-4] = 'Y%04d' % b.year
    tokens[-3] = 'M%02d' % b.month
    tokens[-2] = 'D%02d' % b.day
    tokens[-1] = 'H%02d' % b.hour
    d = '/'.join(tokens)

    return d


if __name__ == '__main__':
    rename_merra_files()


