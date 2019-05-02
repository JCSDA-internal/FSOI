"""
Python module for FSOI
"""
__author__ = 'Rahul Mahajan'
__email__ = 'rahul.mahajan@noaa.gov'
__copyright__ = 'Copyright 2016, NOAA / NCEP / EMC'
__license__ = 'GPL'
__status__ = 'Prototype'
__version__ = '0.1'
__all__ = ['ingest', 'plots', 'stats', 'web', 'log']

from logging import Logger
from logging import DEBUG, INFO, WARN, ERROR, CRITICAL
import logging
import sys

log = Logger('fsoi')
log.setLevel(DEBUG)
log.addHandler(logging.StreamHandler(sys.stdout))
