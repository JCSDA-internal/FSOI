"""
FSOI Ingest
"""
__all__ = ['emc', 'gmao', 'jma', 'met', 'meteofr', 'nrl', 'compute_date_from_lag']


import pytz
from datetime import datetime
from time import time


def compute_date_from_lag(lag):
    """
    Calculate a date from a number of days of lag (e.g., 2 days ago)
    :param lag: {int} Lag in days
    :return: {str} Date string in the format YYYYMMDD
    """
    date = datetime.utcfromtimestamp(time() - lag * 86400)
    date_str = '%04d%02d%02d' % (date.year, date.month, date.day)

    return date_str


def compute_lag_from_date(date):
    """
    Calculate the number of days of lag from a date
    :param date: {str} Date string in the format YYYYMMDD
    :return: {int} Lag in days
    """
    year = int(date[0:4])
    month = int(date[4:6])
    day = int(date[6:8])
    dt = pytz.utc.localize(datetime(year, month, day, 0, 0, 0))
    now = pytz.utc.localize(datetime.now())

    return int((now.timestamp() - dt.timestamp()) // 86400)
