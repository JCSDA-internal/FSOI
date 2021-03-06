"""
lib_obimpact.py contains functions for FSOI project
Some functions can be used elsewhere
"""

import yaml
import pkgutil
import pandas as _pd
import itertools as _itertools
from fsoi import log
import numpy as _np
from fsoi.stats import lib_utils as _lutils


all_platforms = {}


class FSOI(object):
    """
    FSOI Class
    """

    def __init__(self):
        """
        Constructor
        """
        self.center_name = {
            'GMAO': 'GMAO',
            'NRL': 'NRL',
            'MET': 'Met Office',
            'MeteoFr': 'Meteo France',
            'JMA_adj': 'JMA',
            'JMA_ens': 'JMA (Ens.)',
            'EMC': 'EMC (Ens.)'}

        all_centers = ['GMAO', 'NRL', 'MET', 'MeteoFr', 'JMA_adj', 'JMA_ens', 'EMC']
        # colors obtained from www.colorbrewer.org
        # chose qualitative, 7 class Set
        all_colors = ['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f',
                      '#e5c494']  # Set 2
        all_colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33',
                      '#a65628']  # Set 1
        self.center_color = {}
        for c, center in enumerate(all_centers):
            self.center_color[center] = all_colors[c]

        return


def RefPlatform(plat_type):
    """

    :param plat_type:
    :return:
    """
    if plat_type not in ['full', 'conv', 'rad']:
        log.error('Input to RefPlatform must be "full", "conv" or "rad", instead got %s' % plat_type)
        raise Exception()

    conv = [
        'Radiosonde',
        # 'Dropsonde',
        'Ship',
        'Buoy',
        'Land Surface',
        'Aircraft',
        'PIBAL',
        'GPSRO',
        # 'Profiler Wind',
        # 'NEXRAD Wind',
        'Geo Wind',
        'MODIS Wind',
        'AVHRR Wind',
        # 'ASCAT Wind',
        # 'RAPIDSCAT Wind'
    ]

    rad = [
        'AIRS',
        'AMSUA',
        'MHS',
        'ATMS',
        'CrIS',
        'HIRS',
        'IASI',
        'Seviri',
        'GOES',
        # 'SSMIS'
    ]

    full = conv + rad

    if plat_type == 'conv':
        platforms = conv
    elif plat_type == 'rad':
        platforms = rad
    elif plat_type == 'full':
        platforms = full

    return platforms


def OnePlatform():
    """

    :return:
    """
    platforms = {
        'Radiosonde': [
            'Radiosonde', 'RADIOSONDE'
        ],
        'Dropsonde': [
            'Dropsonde'
        ],
        'Ship': [
            'Ship', 'SHIP',
            'Moored_Buoy', 'MOORED_BUOY',
            'Mobile_Marine_Surface'
        ],
        'Buoy': [
            'Drifting_Buoy', 'DRIFTING_BUOY',
            'Platform_Buoy',
            'BUOY'
        ],
        'Land Surface': [
            'Land_Surface',
            'METAR',
            'SYNOP'
        ],
        'Aircraft': [
            'AIREP',
            'AMDAR',
            'MDCARS',
            'MIL_ACARS',
            'Aircraft', 'AIRCRAFT'],
        'PIBAL': [
            'PIBAL',
            'PILOT'
        ],
        'GPSRO': [
            'GPSRO',
            'GNSSRO'
        ],
        'Profiler Wind': [
            'Profiler_Wind',
            'PROFILER'
        ],
        'NEXRAD Wind': [
            'NEXRAD_Wind'
        ],
        'Geo Wind': [
            'GEO_Wind',
            'Sat_Wind',
            'AMV-GEOSTAT',
            'Geo_Wind'
        ],
        'MODIS Wind': [
            'MODIS_Wind',
            'AMV-MODIS'
        ],
        'AVHRR Wind': [
            'AVHRR_Wind',
            'AMV-AVHRR'
        ],
        'ASCAT Wind': [
            'ASCAT_Wind',
            'SCATWIND'
        ],
        'RAPIDSCAT Wind': [
            'RAPIDSCAT_Wind'
        ],
        'Ozone': [
            'Ozone',
            'OMI_AURA'
        ],
        'TMI Rain Rate': [
            'PCP_TMI_TRMM',
            'TMI_TRMM'
        ],
        'Synthetic': [
            'TCBogus',
            'TYBogus'
        ],
        'AIRS': [
            'AIRS_Aqua', 'AIRS_AQUA',
            'AIRS',
            'AIRS281SUBSET_AQUA'
        ],
        'AMSUA': [
            'AMSUA_N15', 'AMSUA_NOAA15',
            'AMSUA_N18', 'AMSUA_NOAA18',
            'AMSUA_N19', 'AMSUA_NOAA19',
            'AMSUA_AQUA', 'AMSUA_Aqua',
            'AMSUA_METOP-A', 'AMSUA_Metop-A',
            'AMSUA_METOP-B', 'AMSUA_Metop-B'
        ],
        'MHS': [
            'MHS_N18', 'MHS_NOAA18',
            'MHS_N19', 'MHS_NOAA19',
            'MHS_METOP-A', 'MHS_Metop-A',
            'MHS_METOP-B', 'MHS_Metop-B'
        ],
        'ATMS': [
            'ATMS_NPP'
        ],
        'CrIS': [
            'CRIS_NPP', 'CrIS_NPP'
        ],
        'HIRS': [
            'HIRS4_N18', 'HIRS4_NOAA18',
            'HIRS4_N19', 'HIRS4_NOAA19',
            'HIRS4_METOP-A', 'HIRS4_Metop-A',
            'HIRS4_METOP-B', 'HIRS4_Metop-B'
                             'HIRS_METOP-A', 'HIRS_Metop-A',
            'HIRS_METOP-B', 'HIRS_Metop-B'
        ],
        'IASI': [
            'IASI_METOP-A', 'IASI_Metop-A',
            'IASI_METOP-B', 'IASI_Metop-B',
            'IASI616_METOP-A'
        ],
        'Seviri': [
            'SEVIRI_M10',
            'SEVIRI',
            'SEVIRI_MSR'
        ],
        'GOES': [
            'SNDRD1_G13',
            'SNDRD2_G13',
            'SNDRD3_G13',
            'SNDRD4_G13',
            'SNDRD1_G15',
            'SNDRD2_G15',
            'SNDRD3_G15',
            'SNDRD4_G15',
            'CSR_GOES13',
            'CSR_GOES15',
            'GOES_CSR'
        ],
        'SSMIS': [
            'SSMIS_F17',
            'SSMIS_F18',
            'SSMIS',
            'SSMIS_DMSP-F16',
            'SSMIS_DMSP-F17',
            'SSMIS_DMSP-F18'
        ],
        'LEO-GEO': [
            'LEO-GEO',
            'AMV-LEOGEO'
        ],
        'WindSat': [
            'WINDSAT'
        ],
        'R/S AMV': [
            'R/S_AMV'
        ],
        'Aus Syn': [
            'UW_wiIR'
        ],
        'UAS': [
            'UAS'
        ],
        'TPW': [
            'SSMI_TPW',
            'WINDSAT_TPW'
        ],
        'PRH': [
            'SSMI_PRH',
            'WINDSAT_PRH'
        ],
        'UNKNOWN': [
            'UNKNOWN'
        ],
        'MTSAT': [
            'CSR_MTSAT-2',
            'MTSAT_CSR'
        ],
        'MVIRI': [
            'CSR_METEOSAT7',
            'CSR_METEOSAT10',
            'MVIRI_CSR'
        ],
        'AMSR': [
            'AMSRE_GCOM-W1',
            'AMSR2_GCOM-W1'
        ],
        'Ground GPS': [
            'GroundGPS'
        ]
    }

    return platforms


def Platforms(center):
    """
    Get a list of platforms for a specified center
    :param center: {str} Name of the center
    :return: {dict} A dictionary of platforms for the given center
    """
    if not all_platforms:
        platforms = yaml.full_load(pkgutil.get_data('fsoi', 'platforms.yaml'))
        for center in platforms:
            all_platforms[center] = platforms[center]

    if center not in all_platforms:
        log.warn('Unknown center requested: %s' % center)
        return None
    return all_platforms[center]


def add_dicts(dicts, unique=False):
    """
    Add dictionaries and result is a common dictionary with common keys and values from both dictionaries. The unique keys are preserved
    """
    result = {}
    for dic in dicts:
        for key in (result.keys() | dic.keys()):
            if key in dic:
                result.setdefault(key, []).append(dic[key])

    # flatten out the values for a key
    for key in result.keys():
        value = list(set(list(_itertools.chain.from_iterable(result[key]))))
        result[key] = value

    return result


def read_ascii(adate, fname):
    """

    :param adate:
    :param fname:
    :return:
    """
    # DataFrame for the data base
    names = ['PLATFORM', 'OBTYPE', 'CHANNEL', 'LONGITUDE', 'LATITUDE', 'PRESSURE', 'IMPACT', 'OMF',
             'OBERR']
    index_cols = names[0:3]
    dtypes = {'PLATFORM': str, 'OBTYPE': str, 'CHANNEL': _np.int, 'LONGITUDE': _np.float,
              'LATITUDE': _np.float, 'PRESSURE': _np.float, 'IMPACT': _np.float, 'OMF': _np.float,
              'OBERR': _np.float}

    # read data into a DataFrame object
    log.debug('reading ... %s' % fname)
    try:
        df = _pd.read_csv(fname, delim_whitespace=True, header=None, names=names,
                          index_col=index_cols, dtype=dtypes)
    except RuntimeError:
        raise

    # Append the DateTime as the 1st level
    df['DATETIME'] = adate
    df.set_index('DATETIME', append=True, inplace=True)
    df = df.reorder_levels(['DATETIME'] + index_cols)

    return df


def list_to_dataframe(adate, data):
    """
    INPUT:  data = list of lists. Each list is a row e.g. [[...],[...],...,[...]]
           adate = date to append to the dataframe
    OUTPUT:   df = convert list data into a pandas dataframe
    :param adate:
    :param data:
    :return:
    """
    columns = ['PLATFORM', 'OBTYPE', 'CHANNEL', 'LONGITUDE', 'LATITUDE', 'PRESSURE', 'IMPACT',
               'OMF', 'OBERR']
    index_cols = columns[0:3]

    # read data into a DataFrame object
    try:
        df = _pd.DataFrame.from_records(data, columns=columns, index=index_cols)
    except RuntimeError:
        raise

    # Append the DateTime as the 1st level
    df['DATETIME'] = adate
    df.set_index('DATETIME', append=True, inplace=True)
    df = df.reorder_levels(['DATETIME'] + index_cols)

    for col in ['LONGITUDE', 'LATITUDE', 'PRESSURE', 'IMPACT', 'OMF', 'OBERR']:
        df[col] = df[col].astype(_np.float)

    return df


def select(df, cycles=None, dates=None, platforms=None, obtypes=None, channels=None, latitudes=None,
           longitudes=None, pressures=None):
    """
    Successively slice a dataframe given ranges of cycles, dates, platforms, obtypes, channels, latitudes, longitudes and pressures
    :param df:
    :param cycles:
    :param dates:
    :param platforms:
    :param obtypes:
    :param channels:
    :param latitudes:
    :param longitudes:
    :param pressures:
    :return:
    """
    if cycles is not None:
        indx = df.index.get_level_values('DATETIME') == ''
        for cycle in cycles:
            indx = _np.ma.logical_or(indx, df.index.get_level_values('DATETIME').hour == cycle)
        df = df.iloc[indx]
    if dates is not None:
        indx = df.index.get_level_values('DATETIME') == ''
        for date in dates:
            indx = _np.ma.logical_or(indx, df.index.get_level_values('DATETIME') == date)
        df = df.iloc[indx]
    if platforms is not None:
        indx = df.index.get_level_values('PLATFORM') == ''
        for platform in platforms:
            indx = _np.ma.logical_or(indx, df.index.get_level_values('PLATFORM') == platform)
        df = df.iloc[indx]
    if obtypes is not None:
        indx = df.index.get_level_values('OBTYPE') == ''
        for obtype in obtypes:
            indx = _np.ma.logical_or(indx, df.index.get_level_values('OBTYPE') == obtype)
        df = df.iloc[indx]
    if channels is not None:
        indx = df.index.get_level_values('CHANNEL') == ''
        for channel in channels:
            indx = _np.ma.logical_or(indx, df.index.get_level_values('CHANNEL') == channel)
        df = df.iloc[indx]
    if latitudes is not None:
        indx1 = df.index.get_level_values('LATITUDE') >= _np.min(latitudes)
        indx2 = df.index.get_level_values('LATITUDE') <= _np.max(latitudes)
        indx = _np.ma.logical_and(indx1, indx2)
        df = df.iloc[indx]
    if longitudes is not None:
        indx1 = df.index.get_level_values('LONGITUDE') >= _np.min(longitudes)
        indx2 = df.index.get_level_values('LONGITUDE') <= _np.max(longitudes)
        indx = _np.ma.logical_and(indx1, indx2)
        df = df.iloc[indx]
    if pressures is not None:
        indx1 = df.index.get_level_values('PRESSURE') >= _np.min(pressures)
        indx2 = df.index.get_level_values('PRESSURE') <= _np.max(pressures)
        indx = _np.ma.logical_and(indx1, indx2)
        df = df.iloc[indx]

    return df


def BulkStats(DF, threshold=1.e-10):
    """
    Collapse PRESSURE, LATITUDE, LONGITUDE
    :param DF:
    :param threshold:
    :return:
    """
    log.debug('... computing bulk statistics ...')

    columns = ['TotImp', 'ObCnt', 'ObCntBen', 'ObCntNeu']
    names = ['DATETIME', 'PLATFORM', 'OBTYPE', 'CHANNEL']
    df = _lutils.EmptyDataFrame(columns, names, dtype=_np.float)

    tmp = DF.reset_index()
    tmp.drop(['LONGITUDE', 'LATITUDE', 'PRESSURE', 'OMF', 'OBERR'], axis=1, inplace=True)

    df[['TotImp', 'ObCnt']] = tmp.groupby(names)['IMPACT'].agg(['sum', 'count'])
    df[['ObCntBen']] = tmp.groupby(names)['IMPACT'].apply(lambda c: (c < -threshold).sum())
    df[['ObCntNeu']] = tmp.groupby(names)['IMPACT'].apply(
        lambda c: ((-threshold < c) & (c < threshold)).sum())

    for col in ['ObCnt', 'ObCntBen', 'ObCntNeu']:
        df[col] = df[col].astype(_np.int)

    return df


def accumBulkStats(DF):
    """
    Collapse OBTYPE and CHANNEL
    :param DF:
    :return:
    """

    log.debug('... accumulating bulk statistics ...')

    columns = ['TotImp', 'ObCnt', 'ObCntBen', 'ObCntNeu']
    names = ['DATETIME', 'PLATFORM']
    df = _lutils.EmptyDataFrame(columns, names, dtype=_np.float)

    tmp = DF.reset_index()
    tmp.drop(['OBTYPE', 'CHANNEL'], axis=1, inplace=True)

    df[['TotImp', 'ObCnt', 'ObCntBen', 'ObCntNeu']] = tmp.groupby(names).agg('sum')

    for col in ['ObCnt', 'ObCntBen', 'ObCntNeu']:
        df[col] = df[col].astype(_np.int)

    return df


def groupBulkStats(DF, Platforms):
    """
    Group accumulated bulk statistics by aggregated platforms
    :param DF:
    :param Platforms:
    :return:
    """
    log.debug('... grouping bulk statistics ...')

    tmp = DF.reset_index()

    for key in Platforms:
        tmp.replace(to_replace=Platforms[key], value=key, inplace=True)

    names = ['DATETIME', 'PLATFORM']
    df = tmp.groupby(names).agg('sum')

    for col in ['ObCnt', 'ObCntBen', 'ObCntNeu']:
        df[col] = df[col].astype(_np.int)

    return df


def tavg(DF, level=None):
    """

    :param DF:
    :param level:
    :return:
    """
    if level is None:
        log.error('A level is needed to do averaging over, e.g. PLATFORM or CHANNEL')
        raise Exception()

    log.debug('... time-averaging bulk statistics over level = %s' % level)

    df = DF.mean(level=level)
    df2 = DF.std(level=level)

    for col in ['ObCnt', 'ObCntBen', 'ObCntNeu']:
        df[col] = df[col].astype(_np.int)
        df2[col] = df2[col].fillna(0).astype(_np.int)

    return df, df2


def bin_df(DF, dlat=5., dlon=5., dpres=None):
    """
    Bin a dataframe given dlat, dlon and dpres using Pandas method
    :param DF: dataframe that needs to be binned
    :param dlat: latitude box in degrees (default: 5.)
    :param dlon: longitude box in degrees (default: 5.)
    :param dpres: pressure box in hPa (default: None, column sum)
    :return: binned dataframe
    """
    tmp = DF.reset_index()

    columns = ['TotImp', 'ObCnt']
    names = ['DATETIME', 'PLATFORM', 'OBTYPE', 'CHANNEL', 'LONGITUDE', 'LATITUDE']

    if dpres is None:
        if 'PRESSURE' in tmp.columns:
            tmp.drop('PRESSURE', axis=1, inplace=True)
    else:
        if 'PRESSURE' in tmp.columns:
            names += ['PRESSURE']

    df = _lutils.EmptyDataFrame(columns, names, dtype=_np.float)

    lons = tmp['LONGITUDE'].values
    if _np.min(lons) < 0.:
        lons[lons < 0.] = lons[lons < 0.] + 360.
        tmp['LONGITUDE'] = lons

    lats = tmp['LATITUDE'].values
    if _np.min(lats) < -90.:
        lats[lats < -90.] = -90.
        tmp['LATITUDE'] = lats

    tmp['LONGITUDE'] = tmp['LONGITUDE'].apply(
        lambda x: [e for e in _np.arange(0., 360. + dlon, dlon) if e <= x][-1])
    tmp['LATITUDE'] = tmp['LATITUDE'].apply(
        lambda x: [e for e in _np.arange(-90., 90. + dlat, dlat) if e <= x][-1])
    if not dpres is None:
        tmp['PRESSURE'] = tmp['PRESSURE'].apply(
            lambda x: [e for e in _np.arange(1000., 0., -1 * dpres) if e >= x][-1])

    df[['TotImp', 'ObCnt']] = tmp.groupby(names)['IMPACT'].agg(['sum', 'count'])
    df['ObCnt'] = df['ObCnt'].astype(_np.int)

    return df


def scipy_bin_df(df, dlat=5., dlon=5., dpres=None):
    """

    :param df:
    :param dlat:
    :param dlon:
    :param dpres:
    :return:
    """
    raise NotImplementedError('lib_obimpact.py - scipy_bin_df is not yet active')


def summarymetrics(DF, level=None, mavg=None):
    """

    :param DF:
    :param level:
    :param mavg:
    :return:
    """
    df = DF[['TotImp', 'ObCnt']].copy()

    df['ImpPerOb'] = df['TotImp'] / df['ObCnt']
    df['FracBenObs'] = DF['ObCntBen'] / (DF['ObCnt'] - DF['ObCntNeu']) * 100.
    df['FracNeuObs'] = DF['ObCntNeu'] / (DF['ObCnt'] - DF['ObCntBen']) * 100.

    if mavg:
        for col in ['TotImp', 'ObCnt', 'ImpPerOb', 'FracBenObs', 'FracNeuObs']:
            df[col] = df.groupby(level='PLATFORM')[col].apply(
                lambda x: x.rolling(window=mavg, min_periods=1).mean())

    df['FracImp'] = df['TotImp'] / df['TotImp'].sum(level=level) * 100.

    for col in ['ObCnt']:
        df[col] = df[col].astype(_np.int)

    return df


def getPlotOpt(qty='TotImp', **kwargs):
    """

    :param qty:
    :param kwargs:
    :return:
    """
    plotOpt = {}

    plotOpt['center'] = kwargs['center'] if 'center' in kwargs else None
    plotOpt['domain'] = kwargs['domain'] if 'domain' in kwargs else None
    plotOpt['savefigure'] = kwargs['savefigure'] if 'savefigure' in kwargs else False
    plotOpt['logscale'] = kwargs['logscale'] if 'logscale' in kwargs else True
    plotOpt['finite'] = kwargs['finite'] if 'finite' in kwargs else True
    plotOpt['alpha'] = kwargs['alpha'] if 'alpha' in kwargs else 0.7
    plotOpt['cmap'] = kwargs['cmap'] if 'cmap' in kwargs else 'Blues'
    plotOpt['cmax'] = kwargs['cmax'] if 'cmax' in kwargs else 1.e6
    plotOpt['cmin'] = kwargs['cmin'] if 'cmin' in kwargs else 1.e3
    plotOpt['platform'] = kwargs['platform'] if 'platform' in kwargs else ''
    plotOpt['cmin'] = kwargs['cmin'] if 'cmin' in kwargs else 1.e3
    if plotOpt['platform']:
        plotOpt['cmax'] = kwargs['cmax'] if 'cmax' in kwargs else 1.e4
    else:
        plotOpt['cmax'] = kwargs['cmax'] if 'cmax' in kwargs else 1.e6
    plotOpt['cycle'] = ' '.join('%02dZ' % c for c in kwargs['cycle']) if 'cycle' in kwargs else '00'
    plotOpt['mavg'] = kwargs['mavg'] if 'mavg' in kwargs else 10

    if plotOpt['center'] is None:
        plotOpt['center_name'] = ''
    elif plotOpt['center'] in ['MET']:
        plotOpt['center_name'] = 'Met Office'
    elif plotOpt['center'] in ['MeteoFr']:
        plotOpt['center_name'] = 'Meteo France'
    elif plotOpt['center'] in ['JMA_adj', 'JMA_ens']:
        algorithm = plotOpt['center'].split('_')[-1]
        plotOpt['center_name'] = 'JMA (%s)' % ('Adjoint' if algorithm == 'adj' else 'Ensemble')
    else:
        plotOpt['center_name'] = '%s' % plotOpt['center']

    domain_str = '' if plotOpt['domain'] is None else '%s,' % plotOpt['domain']

    plotOpt['title'] = '%s 24h Observation Impact Summary\n%s %s' % (
    str(plotOpt['center_name']), domain_str, plotOpt['cycle'])
    plotOpt['figure_name'] = '%s' % qty if plotOpt['center'] is None else '%s_%s' % (
    plotOpt['center'], qty)

    if qty == 'TotImp':
        plotOpt['name'] = 'Mean Total Impact'
        plotOpt['xlabel'] = '%s (J/kg)' % plotOpt['name']
        plotOpt['sortAscending'] = False
    elif qty == 'ObCnt':
        plotOpt['name'] = 'Observation Count'
        plotOpt['xlabel'] = '%s per Analysis' % plotOpt['name']
        plotOpt['sortAscending'] = True
    elif qty == 'ImpPerOb':
        plotOpt['name'] = 'Impact per Observation'
        plotOpt['xlabel'] = '%s (J/kg)' % plotOpt['name']
        plotOpt['sortAscending'] = False
    elif qty == 'FracBenNeuObs':
        plotOpt['name'] = 'Fraction of Ben. & Neu. Observations'
        plotOpt['xlabel'] = '%s (%%)' % plotOpt['name']
        plotOpt['sortAscending'] = True
    elif qty == 'FracBenObs':
        plotOpt['name'] = 'Fraction of Beneficial Observations'
        plotOpt['xlabel'] = '%s (%%)' % plotOpt['name']
        plotOpt['sortAscending'] = True
    elif qty == 'FracNeuObs':
        plotOpt['name'] = 'Fraction of Neutral Observations'
        plotOpt['xlabel'] = '%s (%%)' % plotOpt['name']
        plotOpt['sortAscending'] = True
    elif qty == 'FracImp':
        plotOpt['name'] = 'Fractional Impact'
        plotOpt['xlabel'] = '%s (%%)' % plotOpt['name']
        plotOpt['sortAscending'] = True

    plotOpt['title'] = '%s\n%s' % (plotOpt['title'], plotOpt['xlabel'])

    plotOpt['legend'] = None

    return plotOpt


def getbarcolors(data, logscale, cmax, cmin, cmap):
    """

    :param data:
    :param logscale:
    :param cmax:
    :param cmin:
    :param cmap:
    :return:
    """
    lmin = _np.log10(cmin)
    lmax = _np.log10(cmax)
    barcolors = []
    for cnt in data:
        if cnt <= cmin:
            cindex = 0
        elif cnt >= cmax:
            cindex = len(cmap.palette) - 1
        else:
            if logscale:  # linear in log-space
                lcnt = _np.log10(cnt)
                cindex = (lcnt - lmin) / (lmax - lmin) * (len(cmap.palette) - 1)
            else:
                cindex = (cnt - cmin) / (cmax - cmin) * (len(cmap.palette) - 1)
        cindex = _np.int(cindex)
        c = cmap.palette[cindex]
        barcolors.append(
            [
                int(c[1:3], 16) / 255,
                int(c[3:5], 16) / 255,
                int(c[5:7], 16) / 255
            ]
        )

    return barcolors


def getcomparesummarypalette(
        centers=['GMAO', 'NRL', 'MET', 'MeteoFr', 'JMA_adj', 'JMA_ens', 'EMC']):
    """
    Get a color palette that can be passed to comparesummaryplot
    :param centers: A list of centers in the plot
    :return: A color palette
    """
    colors = {
        'GMAO': '#b23136',  # 178, 49, 54
        'NRL': '#dd684c',  # 221, 104, 76
        'MET': '#e3e3ce',  # 227, 227, 206
        'MeteoFr': '#878d92',  # 135, 141, 146
        'JMA_adj': '#3eafa8',  # 62, 175, 168
        'JMA_ens': '#15695d',  # 21, 105, 93
        'EMC': '#e1f2f2',  # 225, 242, 242
        'ExtraBonus': '#e7a53e'  # 231, 165, 62
    }

    # create a palette so that each center always maps to the same color
    palette = []
    for center in centers:
        if center in colors:
            palette.append(colors[center])
        else:
            palette.append(colors['ExtraBonus'])

    return palette
