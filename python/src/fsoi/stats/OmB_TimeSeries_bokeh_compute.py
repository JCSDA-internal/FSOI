import numpy as _np
import fsoi.stats.lib_utils as _lutils
from fsoi import log

def omfStats(DF, Platforms):
    """
    Collapse PRESSURE, LATITUDE, LONGITUDE
    :param DF:
    :return:
    """
    log.debug('... computing bulk statistics [OmFTimeSeries] ...')

    columns = ['omfmean', 'omfstd', 'bkmean', 'count', 'countrej']
    names = ['DATETIME', 'PLATFORM', 'OBTYPE', 'CHANNEL']
    df = _lutils.EmptyDataFrame(columns, names, dtype=_np.float)

    tmp = DF.reset_index()
    tmp.drop(['LONGITUDE', 'LATITUDE', 'PRESSURE', 'IMPACT', 'OBERR', 'C_PF', 'T_BK', 'IDT', 'C_DB', 'ICHK', 'SENS'], axis=1, inplace=True)

    df[['omfmean', 'omfstd', 'count']] = tmp[tmp.REJ==0].groupby(names)['OMF'].agg(['mean', 'std', 'count'])
    df[['bkmean']] = tmp[tmp.REJ==0].groupby(names)['BK'].agg(['mean'])
    df[['countrej']] = tmp[tmp.REJ!=0].groupby(names)['OMF'].agg(['count'])

    #Remplace nan with 0
    df['countrej'].fillna(0, inplace=True)

    #Remove rejected obs from the total count of obs
    df = df.assign(countused = df['count'] - df['countrej'])
    df.drop(['countrej'], axis=1, inplace=True)

    #Normalize the bias
    df['omfmean'] = df['omfmean'] / (df['omfmean'] + df['bkmean'])

    return df
