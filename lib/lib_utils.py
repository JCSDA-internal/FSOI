#!/usr/bin/env python

'''
lib_utils.py contains handy utility functions
'''

import numpy as _np
import pickle as _pickle
import pandas as _pd
import matplotlib.pyplot as _plt

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
            'discrete_colors',
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
    print('pickling ... %s' % fname)
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
    print('unpickling ... %s' % fname)
    try:
        data = _pickle.load(open(fname, mode))
    except _pickle.UnpicklingError:
        raise
    return data


def writeHDF(fname, vname, data, complevel=0, complib=None, fletcher32=False):
    '''
        Write to an pytable HDF5 file
    '''
    print('writing ... %s' % fname)
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
    print('reading ... %s' % fname)
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


def discrete_colors(N, base_cmap=None, colormap=False):
    """Create an N-bin discrete colors or colormap from the specified input map"""

    from matplotlib.colors import LinearSegmentedColormap as _lscmap

    # Note that if base_cmap is a string or None, you can simply do
    #    return plt.cm.get_cmap(base_cmap, N)
    # The following works for string, None, or a colormap instance:

    base = _plt.cm.get_cmap(base_cmap)
    color_list = base(_np.linspace(0, 1, N))
    cmap_name = base.name + str(N)

    #return base.from_list(cmap_name, color_list, N)
    return _lscmap.from_list(cmap_name, color_list, N) if colormap else color_list


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
