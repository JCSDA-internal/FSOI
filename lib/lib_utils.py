#!/usr/bin/env python

'''
lib_utils.py contains handy utility functions
'''

import numpy as _np
import cPickle as _pickle
import pandas as _pd

__author__ = "Rahul Mahajan"
__email__ = "rahul.mahajan@nasa.gov"
__copyright__ = "Copyright 2016, NOAA / NCEP / EMC"
__license__ = "GPL"
__status__ = "Prototype"
__all__ = [
            'float10Power', 'roundNumber',
            'pickle', 'unpickle',
            'writeHDF', 'readHDF',
            'EmptyDataFrame',
            'printcolour', 'printcolor',
            'savefigure'
          ]


def float10Power(value):
    '''
        Obtain the power of the number
    '''
    if value == 0:
        return 0
    d = _np.log10(abs(value))
    if d >= 0:
        d = _np.ceil(d) - 1.
    else:
        d = _np.floor(d)
    return d


def roundNumber(value):
    '''
        Round a number to the nearest decimal or integer
        Input: Number
        Output: Number rounded to the nearest 10th.
        eg.
        0.01231 => 0.01    0.0164  => 0.02
        2.3     => 2.0     2.8     => 3.0
        6.2     => 10
        59      => 60
    '''

    d = float10Power(value)
    round_value = _np.round(abs(value)/10**d) * 10**d * _np.sign(value)

    return round_value


def pickle(fname, data, mode='wb'):
    '''
        Pickle some data to a file for quick access
        fname - filename to pickle to
        data  - data to pickle
        mode - mode to pickle (default: wb)
    '''
    print 'pickling ... %s' % fname
    try:
        _pickle.dump(data, open(fname, mode))
    except _pickle.PicklingError:
        raise
    return


def unpickle(fname, mode='rb'):
    '''
        Unpickle a file to get data
        fname - filename to unpickle to
        mode - mode to unpickle (default: rb)
    '''
    print 'unpickling ... %s' % fname
    try:
        data = _pickle.load(open(fname, mode))
    except _pickle.UnpicklingError:
        raise
    return data


def writeHDF(fname, vname, data, complevel=0, complib=None, fletcher32=False):
    '''
        Write to an pytable HDF5 file
    '''
    print 'writing ... %s' % fname
    try:
        hdf = _pd.HDFStore(fname,
                           complevel=complevel, complib=complib,
                           fletcher32=fletcher32)
        hdf.put(vname, data, format='table', append=True)
        hdf.close()
    except RuntimeError:
        raise
    return


def readHDF(fname, vname, **kwargs):
    '''
        Read from an pytable HDF5 file
    '''
    print 'reading ... %s' % fname
    try:
        data = _pd.read_hdf(fname, vname, **kwargs)
    except RuntimeError:
        raise
    return data


def EmptyDataFrame(columns, names, dtype=None):
    '''
        Create an empty Multi-index DataFrame
        Input:
            columns = 'name of all columns; including indices'
            names = 'name of index columns'
        Output:
            df = Multi-index DataFrame object
    '''

    levels = [[] for i in range(len(names))]
    labels = [[] for i in range(len(names))]
    indices = _pd.MultiIndex(levels=levels, labels=labels, names=names)
    df = _pd.DataFrame(index=indices, columns=columns, dtype=dtype)

    return df


def printcolour(text, colour='red'):
    '''
        Print the stdout in color
    '''

    colours = {
            'default': '\033[1;m',
            'gray': '\033[1;30m',
            'red': '\033[1;31m',
            'green': '\033[1;32m',
            'yellow': '\033[1;33m',
            'blue': '\033[1;34m',
            'magenta': '\033[1;35m',
            'cyan': '\033[1;36m',
            'white': '\033[1;37m',
            'crimson': '\033[1;38m'
            }
    print colours[colour] + text + colours['default']

    return


printcolor = printcolour


def savefigure(fh=None, fname='test',
               format=['png', 'eps', 'pdf'],
               orientation='landscape',
               dpi=100):
    '''
    Save a figure in png, eps and pdf formats
    '''

    if fh is None:
        fh = _plt
    if 'png' in format:
        fh.savefig('%s.png' % fname,
                   format='png', dpi=1*dpi,
                   orientation=orientation)
    if 'eps' in format:
        fh.savefig('%s.eps' % fname,
                   format='eps', dpi=2*dpi,
                   orientation=orientation)
    if 'pdf' in format:
        fh.savefig('%s.pdf' % fname,
                   format='pdf', dpi=2*dpi,
                   orientation=orientation)

    return
