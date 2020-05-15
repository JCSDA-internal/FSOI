"""
FSOI Ingest
"""
__all__ = ['emc', 'gmao', 'jma', 'met', 'meteofr', 'nrl', 'compute_date_from_lag']


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
