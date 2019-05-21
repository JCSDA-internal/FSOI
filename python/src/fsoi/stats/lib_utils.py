"""
lib_utils.py contains handy utility functions
"""

import numpy as _np
import pickle as _pickle
import pandas as _pd
import matplotlib.pyplot as _plt
from fsoi import log


def float10Power(value):
    """
    Obtain the power of the number
    :param value:
    :return:
    """
    if value == 0:
        return 0
    d = _np.log10(abs(value))
    if d >= 0:
        d = _np.ceil(d) - 1.
    else:
        d = _np.floor(d)
    return d


def roundNumber(value):
    """
    Round a number to the nearest decimal or integer
    Input: Number
    Output: Number rounded to the nearest 10th.
    eg.
    0.01231 => 0.01    0.0164  => 0.02
    2.3     => 2.0     2.8     => 3.0
    6.2     => 10
    59      => 60
    :param value:
    :return:
    """
    d = float10Power(value)
    round_value = _np.round(abs(value) / 10 ** d) * 10 ** d * _np.sign(value)

    return round_value


def pickle(fname, data, mode='wb'):
    """
    Pickle some data to a file for quick access
    :param fname: filename to pickle to
    :param data: data to pickle
    :param mode: mode to pickle (default: wb)
    :return:
    """
    log.debug('pickling ... %s' % fname)
    try:
        _pickle.dump(data, open(fname, mode))
    except _pickle.PicklingError:
        raise
    return


def unpickle(fname, mode='rb'):
    """
    Unpickle a file to get data
    :param fname: filename to unpickle to
    :param mode: mode to unpickle (default: rb)
    :return:
    """
    log.debug('unpickling ... %s' % fname)
    try:
        data = _pickle.load(open(fname, mode))
    except _pickle.UnpicklingError:
        raise
    return data


def writeHDF(fname, vname, data, complevel=0, complib=None, fletcher32=False):
    """
    Write to an pytable HDF5 file
    :param fname:
    :param vname:
    :param data:
    :param complevel:
    :param complib:
    :param fletcher32:
    :return:
    """
    log.debug('writing ... %s' % fname)
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
    """
    Read from an pytable HDF5 file
    :param fname:
    :param vname:
    :param kwargs:
    :return:
    """
    log.debug('reading ... %s' % fname)
    try:
        data = _pd.read_hdf(fname, vname, **kwargs)
    except RuntimeError:
        raise
    return data


def EmptyDataFrame(columns, names, dtype=None):
    """
    Create an empty Multi-index DataFrame
    :param columns: name of all columns; including indices
    :param names: name of index columns
    :param dtype:
    :return: Multi-index DataFrame object
    """

    levels = [[] for i in range(len(names))]
    labels = [[] for i in range(len(names))]
    indices = _pd.MultiIndex(levels=levels, codes=labels, names=names)
    df = _pd.DataFrame(index=indices, columns=columns, dtype=dtype)

    return df


def discrete_colors(N, base_cmap=None, colormap=False):
    """
    Create an N-bin discrete colors or colormap from the specified input map
    :param N:
    :param base_cmap:
    :param colormap:
    :return:
    """
    from matplotlib.colors import LinearSegmentedColormap as _lscmap

    # Note that if base_cmap is a string or None, you can simply do
    #    return plt.cm.get_cmap(base_cmap, N)
    # The following works for string, None, or a colormap instance:

    base = _plt.cm.get_cmap(base_cmap)
    color_list = base(_np.linspace(0, 1, N))
    cmap_name = base.name + str(N)

    # return base.from_list(cmap_name, color_list, N)
    return _lscmap.from_list(cmap_name, color_list, N) if colormap else color_list
