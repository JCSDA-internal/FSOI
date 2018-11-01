#!/usr/bin/env python

'''
lib_obimpact.py contains functions for FSOI project
Some functions can be used elsewhere
'''

__author__ = "Rahul Mahajan"
__email__ = "rahul.mahajan@noaa.gov"
__copyright__ = "Copyright 2016, NOAA / NCEP / EMC"
__license__ = "GPL"
__status__ = "Prototype"
__version__ = "0.1"

import numpy as _np
import pandas as _pd
from matplotlib import pyplot as _plt
from matplotlib import cm as _cm
import matplotlib.colors as _colors
from matplotlib.ticker import ScalarFormatter as _ScalarFormatter
import itertools as _itertools
import matplotlib.dates as _dates

import lib_utils as _lutils

class FSOI(object):

    def __init__(self):

        self.center_name = {
                'GMAO':'GMAO',
                'NRL':'NRL',
                'MET':'UK MetOffice',
                'MeteoFr':'Meteo France',
                'JMA_adj':'JMA',
                'JMA_ens':'JMA (Ens.)',
                'EMC':'NOAA (Ens.)'}

        all_centers = ['GMAO','NRL','MET','MeteoFr','JMA_adj','JMA_ens','EMC']
        # colors obtained from www.colorbrewer.org
        # chose qualitative, 7 class Set
        all_colors = ['#66c2a5','#fc8d62','#8da0cb','#e78ac3','#a6d854','#ffd92f','#e5c494'] # Set 2
        all_colors = ['#e41a1c','#377eb8','#4daf4a','#984ea3','#ff7f00','#ffff33','#a65628'] # Set 1
        self.center_color = {}
        for c,center in enumerate(all_centers):
            self.center_color[center] = all_colors[c]

        return

def RefPlatform(plat_type):

    if plat_type not in ['full', 'conv', 'rad']:
        print('Input to RefPlatform must be "full", "conv" or "rad", instead got %s' % plat_type)
        raise Exception()

    conv = [
        'Radiosonde',
        #'Dropsonde',
        'Ship',
        'Buoy',
        'Land Surface',
        'Aircraft',
        'PIBAL',
        'GPSRO',
        #'Profiler Wind',
        #'NEXRAD Wind',
        'Geo Wind',
        'MODIS Wind',
        'AVHRR Wind',
        #'ASCAT Wind',
        #'RAPIDSCAT Wind'
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
        #'SSMIS'
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

    platforms = {
    'Radiosonde':[
        'Radiosonde','RADIOSONDE'
        ],
    'Dropsonde':[
        'Dropsonde'
        ],
    'Ship':[
        'Ship','SHIP',
        'Moored_Buoy','MOORED_BUOY',
        'Mobile_Marine_Surface'
        ],
    'Buoy':[
        'Drifting_Buoy','DRIFTING_BUOY',
        'Platform_Buoy',
        'BUOY'
        ],
    'Land Surface':[
        'Land_Surface',
        'METAR',
        'SYNOP'
        ],
    'Aircraft':[
        'AIREP',
        'AMDAR',
        'MDCARS',
        'MIL_ACARS',
        'Aircraft','AIRCRAFT'],
    'PIBAL':[
        'PIBAL',
        'PILOT'
        ],
    'GPSRO':[
        'GPSRO',
        'GNSSRO'
        ],
    'Profiler Wind':[
        'Profiler_Wind',
        'PROFILER'
        ],
    'NEXRAD Wind':[
        'NEXRAD_Wind'
        ],
    'Geo Wind':[
        'GEO_Wind',
        'Sat_Wind',
        'AMV-GEOSTAT',
        'Geo_Wind'
        ],
    'MODIS Wind':[
        'MODIS_Wind',
        'AMV-MODIS'
        ],
    'AVHRR Wind':[
        'AVHRR_Wind',
        'AMV-AVHRR'
        ],
    'ASCAT Wind':[
            'ASCAT_Wind',
            'SCATWIND'
            ],
    'RAPIDSCAT Wind':[
            'RAPIDSCAT_Wind'
            ],
    'Ozone':[
        'Ozone',
        'OMI_AURA'
        ],
    'TMI Rain Rate':[
            'PCP_TMI_TRMM',
            'TMI_TRMM'
            ],
    'Synthetic':[
        'TCBogus',
        'TYBogus'
        ],
    'AIRS':[
        'AIRS_Aqua','AIRS_AQUA',
        'AIRS',
        'AIRS281SUBSET_AQUA'
        ],
    'AMSUA':[
        'AMSUA_N15','AMSUA_NOAA15',
        'AMSUA_N18','AMSUA_NOAA18',
        'AMSUA_N19','AMSUA_NOAA19',
        'AMSUA_AQUA','AMSUA_Aqua',
        'AMSUA_METOP-A','AMSUA_Metop-A',
        'AMSUA_METOP-B','AMSUA_Metop-B'
        ],
    'MHS':[
            'MHS_N18','MHS_NOAA18',
            'MHS_N19','MHS_NOAA19',
            'MHS_METOP-A','MHS_Metop-A',
            'MHS_METOP-B','MHS_Metop-B'
            ],
    'ATMS':[
            'ATMS_NPP'
            ],
    'CrIS':[
            'CRIS_NPP','CrIS_NPP'
            ],
    'HIRS':[
            'HIRS4_N18','HIRS4_NOAA18',
            'HIRS4_N19','HIRS4_NOAA19',
            'HIRS4_METOP-A','HIRS4_Metop-A',
            'HIRS4_METOP-B','HIRS4_Metop-B'
            'HIRS_METOP-A','HIRS_Metop-A',
            'HIRS_METOP-B','HIRS_Metop-B'
            ],
    'IASI':[
            'IASI_METOP-A','IASI_Metop-A',
            'IASI_METOP-B','IASI_Metop-B',
            'IASI616_METOP-A'
            ],
    'Seviri':[
            'SEVIRI_M10',
            'SEVIRI',
            'SEVIRI_MSR'
            ],
    'GOES':[
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
    'SSMIS':[
            'SSMIS_F17',
            'SSMIS_F18',
            'SSMIS',
            'SSMIS_DMSP-F16',
            'SSMIS_DMSP-F17',
            'SSMIS_DMSP-F18'
            ],
    'LEO-GEO':[
            'LEO-GEO',
            'AMV-LEOGEO'
            ],
    'WindSat':[
            'WINDSAT'
                ],
    'R/S AMV':[
            'R/S_AMV'
            ],
    'Aus Syn':[
            'UW_wiIR'
            ],
    'UAS':[
            'UAS'
            ],
    'TPW':[
            'SSMI_TPW',
            'WINDSAT_TPW'
            ],
    'PRH':[
            'SSMI_PRH',
            'WINDSAT_PRH'
            ],
    'UNKNOWN':[
            'UNKNOWN'
            ],
    'MTSAT':[
            'CSR_MTSAT-2',
            'MTSAT_CSR'
            ],
    'MVIRI':[
            'CSR_METEOSAT7',
            'CSR_METEOSAT10',
            'MVIRI_CSR'
            ],
    'AMSR':[
            'AMSRE_GCOM-W1',
            'AMSR2_GCOM-W1'
            ],
    'Ground GPS':[
            'GroundGPS'
            ]
    }

    return platforms

def Platforms(center):

    platforms={}
    exec('platforms = %s_platforms()' % center)
    return platforms

def GMAO_platforms():

    platforms = {
    'Radiosonde':['Radiosonde'],
    'Dropsonde':['Dropsonde'],
    'Ship':['Ship','Moored_Buoy'],
    'Buoy':['Drifting_Buoy'],
    'Land Surface':['Land_Surface','METAR'],
    'Aircraft':['AIREP','ASDAR','MDCARS'],
    'PIBAL':['PIBAL'],
    'GPSRO':['GPSRO'],
    'Profiler Wind':['Profiler_Wind'],
    'NEXRAD Wind':['NEXRAD_Wind'],
    'Geo Wind':['Geo_Wind'],
    'MODIS Wind':['MODIS_Wind'],
    'AVHRR Wind':['AVHRR_Wind'],
    'ASCAT Wind':['ASCAT_Wind'],
    'RAPIDSCAT Wind':['RAPIDSCAT_Wind'],
    'Ozone':['Ozone','OMI_AURA'],
    'TMI Rain Rate':['PCP_TMI_TRMM'],
    'Synthetic':['TCBogus'],
    'AIRS':['AIRS_AQUA'],
    'AMSUA':['AMSUA_N15','AMSUA_N18','AMSUA_N19','AMSUA_AQUA','AMSUA_METOP-A','AMSUA_METOP-B'],
    'MHS':['MHS_N18','MHS_N19','MHS_METOP-A','MHS_METOP-B'],
    'ATMS':['ATMS_NPP'],
    'CrIS':['CRIS_NPP'],
    'HIRS':['HIRS4_N18','HIRS4_N19','HIRS4_METOP-A','HIRS4_METOP-B'],
    'IASI':['IASI_METOP-A','IASI_METOP-B'],
    'Seviri':['SEVIRI_M10'],
    'GOES':['SNDRD1_G13','SNDRD2_G13','SNDRD3_G13','SNDRD4_G13','SNDRD1_G15','SNDRD2_G15','SNDRD3_G15','SNDRD4_G15'],
    'SSMIS':['SSMIS_F17','SSMIS_F18']
    }

    return platforms

def NRL_platforms():

    platforms = {
    'Radiosonde':['Radiosonde'],
    'Dropsonde':['Dropsonde'],
    'Ship':['Ship','Moored_Buoy'],
    'Buoy':['Drifting_Buoy'],
    'Land Surface':['Land_Surface'],
    'Aircraft':['AIREP','AMDAR','MDCARS','MIL_ACARS'],
    'PIBAL':['PIBAL'],
    'GPSRO':['GPSRO'],
    'Profiler Wind':['Profiler_Wind'],
    'NEXRAD Wind':['NEXRAD_Wind'],
    'Geo Wind':['Sat_Wind'],
    'MODIS Wind':['MODIS_Wind'],
    'AVHRR Wind':['AVHRR_Wind'],
    'ASCAT Wind':['ASCAT_Wind'],
    'RAPIDSCAT Wind':['RAPIDSCAT_Wind'],
    'Ozone':['Ozone','OMI_AURA'],
    'TMI Rain Rate':['PCP_TMI_TRMM'],
    'Synthetic':['TCBogus'],
    'AIRS':['AIRS'],
    'AMSUA':['AMSUA_N15','AMSUA_N18','AMSUA_N19','AMSUA_AQUA','AMSUA_METOP-A','AMSUA_METOP-B'],
    'MHS':['MHS_N18','MHS_N19','MHS_METOP-A','MHS_METOP-B'],
    'ATMS':['ATMS_NPP'],
    'CrIS':['CrIS_NPP'],
    'HIRS':['HIRS4_N18','HIRS4_N19','HIRS4_METOP-A','HIRS4_METOP-B'],
    'IASI':['IASI_METOP-A','IASI_METOP-B'],
    'Seviri':['SEVIRI'],
    'GOES':['SNDRD1_G13','SNDRD2_G13','SNDRD3_G13','SNDRD4_G13','SNDRD1_G15','SNDRD2_G15','SNDRD3_G15','SNDRD4_G15'],
    'SSMIS':['SSMIS'],
    'LEO-GEO':['LEO-GEO'],
    'WindSat':['WINDSAT'],
    'R/S AMV':['R/S_AMV'],
    'Aus Syn':['UW_wiIR'],
    'UAS':['UAS'],
    'TPW':['SSMI_TPW','WINDSAT_TPW'],
    'PRH':['SSMI_PRH','WINDSAT_PRH']
    }

    return platforms

def EMC_platforms():

    platforms = {
    'Radiosonde':['Radiosonde'],
    'Dropsonde':['Dropsonde'],
    'Ship':['Mobile_Marine_Surface','Moored_Buoy'],
    'Buoy':['Drifting_Buoy'],
    'Land Surface':['Land_Surface'],
    'Aircraft':['Aircraft'],
    'PIBAL':['PIBAL'],
    'GPSRO':['GPSRO'],
    'Profiler Wind':['Profiler_Wind'],
    'NEXRAD Wind':['NEXRAD_Wind'],
    'Geo Wind':['Sat_Wind'],
    'MODIS Wind':['MODIS_Wind'],
    'AVHRR Wind':['AVHRR_Wind'],
    'ASCAT Wind':['ASCAT_Wind'],
    'RAPIDSCAT Wind':['RAPIDSCAT_Wind'],
    'Ozone':['Ozone'],
    'TMI Rain Rate':['PCP_TMI_TRMM'],
    'Synthetic':['TCBogus'],
    'AIRS':['AIRS281SUBSET_AQUA'],
    'AMSUA':['AMSUA_N15','AMSUA_N18','AMSUA_N19','AMSUA_AQUA','AMSUA_METOP-A','AMSUA_METOP-B'],
    'MHS':['MHS_N18','MHS_N19','MHS_METOP-A','MHS_METOP-B'],
    'ATMS':['ATMS_NPP'],
    'CrIS':['CRIS_NPP'],
    'HIRS':['HIRS4_METOP-A'],
    'IASI':['IASI616_METOP-A'],
    'Seviri':['SEVIRI10'],
    'GOES':['SNDRD1_G15','SNDRD2_G15','SNDRD3_G15','SNDRD4_G15'],
    'SSMIS':['SSMIS_F17','SSMIS_F18'],
    'UNKNOWN':['UNKNOWN']
    }

    return platforms

def JMA_adj_platforms():
    return JMA_platforms()

def JMA_ens_platforms():
    return JMA_platforms()

def JMA_platforms():

    platforms = {
    'Radiosonde':['RADIOSONDE'],
    'Dropsonde':['Dropsonde'],
    'Ship':['SHIP','MOORED_BUOY'],
    'Buoy':['DRIFTING_BUOY','BUOY'],
    'Land Surface':['SYNOP'],
    'Aircraft':['AIRCRAFT'],
    'PIBAL':['PILOT'],
    'GPSRO':['GNSSRO'],
    'Profiler Wind':['PROFILER'],
    'NEXRAD Wind':['NEXRAD_Wind'],
    'Geo Wind':['AMV-GEOSTAT'],
    'MODIS Wind':['AMV-MODIS'],
    'AVHRR Wind':['AMV-AVHRR'],
    'ASCAT Wind':['SCATWIND'],
    'RAPIDSCAT Wind':['RAPIDSCAT_Wind'],
    'Ozone':['Ozone','OMI_AURA'],
    'TMI Rain Rate':['TMI_TRMM'],
    'Synthetic':['TYBOGUS'],
    'AIRS':['AIRS_Aqua'],
    'AMSUA':['AMSUA_NOAA15','AMSUA_NOAA18','AMSUA_NOAA19','AMSUA_Aqua','AMSUA_Metop-A','AMSUA_Metop-B'],
    'MHS':['MHS_NOAA18','MHS_NOAA19','MHS_Metop-A','MHS_Metop-B'],
    'ATMS':['ATMS_NPP'],
    'CrIS':['CrIS_NPP'],
    'HIRS':['HIRS4_NOAA18','HIRS4_NOAA19','HIRS4_Metop-A','HIRS4_Metop-B'],
    'IASI':['IASI_Metop-A','IASI_Metop-B'],
    'Seviri':['SEVIRI_M10'],
    'GOES':['CSR_GOES13','CSR_GOES15'],
    'SSMIS':['SSMIS_DMSP-F16','SSMIS_DMSP-F17','SSMIS_DMSP-F18'],
    'LEO-GEO':['AMV-LEOGEO'],
    'MTSAT':['CSR_MTSAT-2'],
    'MVIRI':['CSR_METEOSAT7','CSR_METEOSAT10'],
    'AMSR':['AMSRE_GCOM-W1','AMSR2_GCOM-W1'],
    }

    return platforms

def MET_platforms():

    platforms = {
    'Radiosonde':['Radiosonde'],
    'Dropsonde':['Dropsonde'],
    'Ship':['Ship','Moored_Buoy'],
    'Buoy':['Drifting_Buoy','Platform_Buoy'],
    'Land Surface':['SYNOP','METAR'],
    'Aircraft':['Aircraft'],
    'PIBAL':['PILOT'],
    'GPSRO':['GPSRO'],
    'Profiler Wind':['Profiler_Wind'],
    'NEXRAD Wind':['NEXRAD_Wind'],
    'Geo Wind':['Geo_Wind'],
    'MODIS Wind':['MODIS_Wind'],
    'AVHRR Wind':['AVHRR_Wind'],
    'ASCAT Wind':['ASCAT_Wind'],
    'RAPIDSCAT Wind':['RAPIDSCAT_Wind'],
    'Ozone':['Ozone','OMI_AURA'],
    'TMI Rain Rate':['PCP_TMI_TRMM'],
    'Synthetic':['TCBogus'],
    'AIRS':['AIRS_Aqua'],
    'AMSUA':['AMSUA_N15','AMSUA_N18','AMSUA_N19','AMSUA_METOP-A','AMSUA_METOP-B'],
    'MHS':['MHS_N18','MHS_N19','MHS_METOP-A','MHS_METOP-B'],
    'ATMS':['ATMS_NPP'],
    'CrIS':['CrIS_NPP'],
    'HIRS':['HIRS_METOP-A','HIRS_METOP-B'],
    'IASI':['IASI_METOP-A','IASI_METOP-B'],
    'Seviri':['SEVIRI_MSR'],
    'GOES':['GOES_CSR'],
    'SSMIS':['SSMIS_F17','SSMIS_F18'],
    'LEO-GEO':['LEO-GEO'],
    'MTSAT':['MTSAT_CSR'],
    'MVIRI':['MVIRI_CSR'],
    'Ground GPS':['GroundGPS']
    }

    return platforms

def MeteoFr_platforms():

    platforms = {
    'Radiosonde':['Radiosonde'],
    'Dropsonde':['Dropsonde'],
    'Ship':['Ship'],
    'Buoy':['Drifting_Buoy'],
    'Land Surface':['Land_Surface','RADOME'],
    'Aircraft':['AIREP','AMDAR','ACARS'],
    'PIBAL':['Pilot'],
    'GPSRO':['GPSRO'],
    'Profiler Wind':['Profiler'],
    'GOES Wind':['Imgr_GOES13','Imgr_GOES15'],
    'GMS Wind':['Imgr_GMS'],
    'Misc SatWind':['Misc_SatWind'],
    'METEOSAT Wind':['Imgr_METEOSAT7','Imgr_METEOSAT10'],
    'MODIS Wind':['MODIS_TERRA','MODIS_AQUA'],
    'AVHRR Wind':['AVHRR_NOAA15','AVHRR_NOAA16','AVHRR_NOAA18','AVHRR_NOAA19'],
    'ASCAT Wind':['ASCAT_METOP-A','ASCAT_METOP-B'],
    'Synthetic':['TCBogus'],
    'AIRS':['AIRS_AQUA'],
    'AMSUA':['AMSUA_AQUA','AMSUA_NOAA15','AMSUA_NOAA16','AMSUA_NOAA18','AMSUA_NOAA19','AMSUA_METOP-A','AMSUA_METOP-B'],
    'MHS':['MHS_NOAA19','MHS_METOP-A','MHS_METOP-B'],
    'ATMS':['ATMS_NPP'],
    'CrIS':['CRIS_NPP'],
    'HIRS':['HIRS_METOP-A','HIRS_METOP-B'],
    'IASI':['IASI_METOP-A','IASI_METOP-B'],
    'GOES':['GOESIMG_GOES13','GOESIMG_GOES15'],
    'Seviri':['SEVIRI_METEOSAT10'],
    'SSMIS':['SSMIS_DMSP16','SSMIS_DMSP17','SSMIS_DMSP18'],
    'Ground GPS':['GPSZTD']
    }

    return platforms

def add_dicts(dicts,unique=False):
    '''
    Add dictionaries and result is a common dictionary with common keys and values from both dictionaries. The unique keys are preserved
    '''

    result = {}
    for dic in dicts:
        for key in (result.viewkeys() | dic.keys()):
            if key in dic:
                result.setdefault(key, []).append(dic[key])

    # flatten out the values for a key
    for key in result.keys():
        value = list(set(list(_itertools.chain.from_iterable(result[key]))))
        result[key] = value

    return result

def read_ascii(adate,fname):

    # DataFrame for the data base
    names = ['PLATFORM','OBTYPE','CHANNEL','LONGITUDE','LATITUDE','PRESSURE','IMPACT','OMF','OBERR']
    index_cols = names[0:3]
    dtypes = {'PLATFORM':str,'OBTYPE':str,'CHANNEL':_np.int,'LONGITUDE':_np.float,'LATITUDE':_np.float,'PRESSURE':_np.float,'IMPACT':_np.float,'OMF':_np.float,'OBERR':_np.float}

    # read data into a DataFrame object
    print('reading ... %s' % fname)
    try:
        df = _pd.read_csv(fname,delim_whitespace=True,header=None,names=names,index_col=index_cols,dtype=dtypes)
    except RuntimeError:
        raise

    # Append the DateTime as the 1st level
    df['DATETIME'] = adate
    df.set_index('DATETIME', append=True, inplace=True)
    df = df.reorder_levels(['DATETIME']+index_cols)

    return df

def list_to_dataframe(adate,data):
    '''
    INPUT:  data = list of lists. Each list is a row e.g. [[...],[...],...,[...]]
           adate = date to append to the dataframe
    OUTPUT:   df = convert list data into a pandas dataframe
    '''

    columns = ['PLATFORM','OBTYPE','CHANNEL','LONGITUDE','LATITUDE','PRESSURE','IMPACT','OMF','OBERR']
    index_cols = columns[0:3]

    # read data into a DataFrame object
    try:
        df = _pd.DataFrame.from_records(data,columns=columns,index=index_cols)
    except RuntimeError:
        raise

    # Append the DateTime as the 1st level
    df['DATETIME'] = adate
    df.set_index('DATETIME', append=True, inplace=True)
    df = df.reorder_levels(['DATETIME']+index_cols)

    for col in ['LONGITUDE','LATITUDE','PRESSURE','IMPACT','OMF','OBERR']:
         df[col] = df[col].astype(_np.float)

    return df

def select(df,cycles=None,dates=None,platforms=None,obtypes=None,channels=None,latitudes=None,longitudes=None,pressures=None):
    '''
        Successively slice a dataframe given ranges of cycles, dates, platforms, obtypes, channels, latitudes, longitudes and pressures
    '''
    if cycles is not None:
        indx = df.index.get_level_values('DATETIME') == ''
        for cycle in cycles:
            indx = _np.ma.logical_or(indx,df.index.get_level_values('DATETIME').hour == cycle)
        df = df.iloc[indx]
    if dates is not None:
        indx = df.index.get_level_values('DATETIME') == ''
        for date in dates:
            indx = _np.ma.logical_or(indx,df.index.get_level_values('DATETIME') == date)
        df = df.iloc[indx]
    if platforms is not None:
        indx = df.index.get_level_values('PLATFORM') == ''
        for platform in platforms:
            indx = _np.ma.logical_or(indx,df.index.get_level_values('PLATFORM') == platform)
        df = df.iloc[indx]
    if obtypes is not None:
        indx = df.index.get_level_values('OBTYPE') == ''
        for obtype in obtypes:
            indx = _np.ma.logical_or(indx,df.index.get_level_values('OBTYPE') == obtype)
        df = df.iloc[indx]
    if channels is not None:
        indx = df.index.get_level_values('CHANNEL') == ''
        for channel in channels:
            indx = _np.ma.logical_or(indx,df.index.get_level_values('CHANNEL') == channel)
        df = df.iloc[indx]
    if latitudes is not None:
        indx1 = df.index.get_level_values('LATITUDE') >= _np.min(latitudes)
        indx2 = df.index.get_level_values('LATITUDE') <= _np.max(latitudes)
        indx = _np.ma.logical_and(indx1,indx2)
        df = df.iloc[indx]
    if longitudes is not None:
        indx1 = df.index.get_level_values('LONGITUDE') >= _np.min(longitudes)
        indx2 = df.index.get_level_values('LONGITUDE') <= _np.max(longitudes)
        indx = _np.ma.logical_and(indx1,indx2)
        df = df.iloc[indx]
    if pressures is not None:
        indx1 = df.index.get_level_values('PRESSURE') >= _np.min(pressures)
        indx2 = df.index.get_level_values('PRESSURE') <= _np.max(pressures)
        indx = _np.ma.logical_and(indx1,indx2)
        df = df.iloc[indx]

    return df

def BulkStats(DF, threshold=1.e-10):
    '''Collapse PRESSURE, LATITUDE, LONGITUDE'''

    print('... computing bulk statistics ...')

    columns = ['TotImp', 'ObCnt', 'ObCntBen', 'ObCntNeu']
    names = ['DATETIME', 'PLATFORM', 'OBTYPE', 'CHANNEL']
    df = _lutils.EmptyDataFrame(columns, names, dtype=_np.float)

    tmp = DF.reset_index()
    tmp.drop(['LONGITUDE', 'LATITUDE', 'PRESSURE', 'OMF', 'OBERR'], axis=1, inplace=True)

    df[['TotImp', 'ObCnt']] = tmp.groupby(names)['IMPACT'].agg(['sum', 'count'])
    df[['ObCntBen']] = tmp.groupby(names)['IMPACT'].apply(lambda c: (c < -threshold).sum())
    df[['ObCntNeu']] = tmp.groupby(names)['IMPACT'].apply(lambda c: ((-threshold < c) & (c < threshold)).sum())

    for col in ['ObCnt', 'ObCntBen', 'ObCntNeu']:
        df[col] = df[col].astype(_np.int)

    return df

def accumBulkStats(DF):
    '''Collapse OBTYPE and CHANNEL'''

    print('... accumulating bulk statistics ...')

    columns = ['TotImp','ObCnt','ObCntBen','ObCntNeu']
    names = ['DATETIME','PLATFORM']
    df = _lutils.EmptyDataFrame(columns,names,dtype=_np.float)

    tmp = DF.reset_index()
    tmp.drop(['OBTYPE','CHANNEL'], axis=1, inplace=True)

    df[['TotImp','ObCnt','ObCntBen','ObCntNeu']] = tmp.groupby(names).agg('sum')

    for col in ['ObCnt','ObCntBen','ObCntNeu']:
        df[col] = df[col].astype(_np.int)

    return df

def groupBulkStats(DF,Platforms):
    '''Group accumulated bulk statistics by aggregated platforms'''

    print('... grouping bulk statistics ...')

    tmp = DF.reset_index()

    for key in Platforms:
        tmp.replace(to_replace=Platforms[key],value=key,inplace=True)

    names = ['DATETIME','PLATFORM']
    df = tmp.groupby(names).agg('sum')

    for col in ['ObCnt','ObCntBen','ObCntNeu']:
        df[col] = df[col].astype(_np.int)

    return df

def tavg(DF,level=None):

    if level is None:
        print('A level is needed to do averaging over, e.g. PLATFORM or CHANNEL')
        raise Exception()

    print('... time-averaging bulk statistics over level = %s' % level)

    df = DF.mean(level=level)
    df2 = DF.std(level=level)

    for col in ['ObCnt','ObCntBen','ObCntNeu']:
        df[col] = df[col].astype(_np.int)
        df[col] = df2[col].fillna(0).astype(_np.int)

    return df, df2

def bin_df(DF, dlat=5., dlon=5., dpres=None):
    '''
    Bin a dataframe given dlat, dlon and dpres using Pandas method
    INPUT:
          DF : dataframe that needs to be binned
        dlat : latitude box in degrees (default: 5.)
        dlon : longitude box in degrees (default: 5.)
       dpres : pressure box in hPa (default: None, column sum)
    OUTPUT:
          df : binned dataframe
    '''

    tmp = DF.reset_index()

    columns = ['TotImp','ObCnt']
    names = ['DATETIME','PLATFORM','OBTYPE','CHANNEL','LONGITUDE','LATITUDE']

    if dpres is None:
        if 'PRESSURE' in tmp.columns:
            tmp.drop('PRESSURE', axis=1, inplace=True)
    else:
        if 'PRESSURE' in tmp.columns:
            names += ['PRESSURE']

    df = _lutils.EmptyDataFrame(columns,names,dtype=_np.float)

    lons = tmp['LONGITUDE'].values
    if _np.min(lons) < 0.:
        lons[lons<0.] = lons[lons<0.] + 360.
        tmp['LONGITUDE'] = lons

    lats = tmp['LATITUDE'].values
    if _np.min(lats) < -90.:
        lats[lats<-90.] = -90.
        tmp['LATITUDE'] = lats

    tmp['LONGITUDE'] = tmp['LONGITUDE'].apply(lambda x: [e for e in _np.arange(  0.,360.+dlon,dlon) if e <= x][-1])
    tmp['LATITUDE' ] = tmp['LATITUDE' ].apply(lambda x: [e for e in _np.arange(-90., 90.+dlat,dlat) if e <= x][-1])
    if not dpres is None:
        tmp['PRESSURE' ] = tmp['PRESSURE' ].apply(lambda x: [e for e in _np.arange(1000.,0.,-dpres) if e >= x][-1])

    df[['TotImp','ObCnt']] = tmp.groupby(names)['IMPACT'].agg(['sum','count'])
    df['ObCnt'] = df['ObCnt'].astype(_np.int)

    return df

def scipy_bin_df(df,dlat=5.,dlon=5.,dpres=None):

    raise NotImplementedError('lib_obimpact.py - scipy_bin_df is not yet active')

    return df

def summarymetrics(DF):

    df = DF[['TotImp', 'ObCnt']].copy()

    df['ImpPerOb'] = df['TotImp'] / df['ObCnt']
    df['FracBenObs'] = DF['ObCntBen'] / (DF['ObCnt'] - DF['ObCntNeu'] ) * 100.
    df['FracNeuObs'] = DF['ObCntNeu'] / (DF['ObCnt'] - DF['ObCntBen'] ) * 100.
    df['FracImp'] = df['TotImp'] / df['TotImp'].sum() * 100.

    for col in ['ObCnt']:
        df[col] = df[col].astype(_np.int)

    return df

def getPlotOpt(qty='TotImp',**kwargs):

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

    plotOpt['title'] = '%s 24h Observation Impact Summary\n%s %s DJF 2014-15' % (str(plotOpt['center_name']), domain_str,plotOpt['cycle'])
    plotOpt['figname'] = '%s' % qty if plotOpt['center'] is None else '%s_%s' % (plotOpt['center'],qty)

    if qty == 'TotImp':
        plotOpt['name'] = 'Total Impact'
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

    plotOpt['title'] = '%s\n%s %s' % (plotOpt['title'],plotOpt['platform'],plotOpt['xlabel'])

    plotOpt['legend'] = None

    return plotOpt

def getbarcolors(data,logscale,cmax,cmin,cmap):

    lmin = _np.log10(cmin)
    lmax = _np.log10(cmax)
    barcolors = []
    for cnt in data:
        if cnt <= cmin:
            cindex = 0
        elif cnt >= cmax:
            cindex = cmap.N - 1
        else:
            if logscale: # linear in log-space
                lcnt = _np.log10(cnt)
                cindex =  (lcnt - lmin) / (lmax - lmin) * (cmap.N - 1)
            else:
                cindex = (cnt - cmin) / (cmax - cmin) * (cmap.N - 1)
        cindex = _np.int(cindex)
        barcolors.append(cmap(cindex))

    return barcolors

def summaryplot(df,qty='TotImp',plotOpt={},std=None):

    if plotOpt['finite']:
        df = df[_np.isfinite(df[qty])]

    if plotOpt['platform']:
        df.sort_index(ascending=True,inplace=True)
    else:
        if qty in ['FracBenNeuObs']:
            df.sort_values(by='FracBenObs',ascending=plotOpt['sortAscending'],inplace=True,na_position='first')
        else:
            df.sort_values(by=qty,ascending=plotOpt['sortAscending'],inplace=True,na_position='first')

    fig = _plt.figure(figsize=(10,8))
    ax = fig.add_subplot(111, facecolor='w')

    alpha = plotOpt['alpha']
    logscale = plotOpt['logscale']
    cmax = plotOpt['cmax']
    cmin = plotOpt['cmin']
    cmap = _cm.get_cmap(plotOpt['cmap'])

    barcolors = getbarcolors(df['ObCnt'],logscale,cmax,cmin,cmap)
    norm = _colors.LogNorm() if logscale else _colors.Normalize()

    # dummy plot for keeping colorbar on a bar plot
    x = _np.array([0,   1,   2,   3,   4,   5,   6])
    y = _np.array([1e0, 1e1, 1e2, 1e3, 1e4, 1e5, 1e6])
    tmp = _plt.scatter(x,y,c=y,alpha=alpha,cmap=cmap,norm=norm,vmin=cmin,vmax=cmax)
    _plt.clf()
    cbar = _plt.colorbar(tmp, aspect=30, ticks=y, format='%.0e', alpha=alpha)

    width = 1.0
    if qty == 'FracBenNeuObs':
        left = df['FracBenObs'].values
        df['FracBenObs'].plot.barh(width=width,color=barcolors,alpha=alpha,edgecolor='k',linewidth=1.25)
        bax = df['FracNeuObs'].plot.barh(left=left,width=width,color=barcolors,alpha=alpha,edgecolor='k',linewidth=1.25)
    elif qty == 'TotImp':
        df[qty].plot.barh(width=width,color=barcolors,alpha=alpha,edgecolor='k',linewidth=1.25,xerr=std[qty],capsize=2.0,ecolor='#FF6103')
    else:
        df[qty].plot.barh(width=width,color=barcolors,alpha=alpha,edgecolor='k',linewidth=1.25)

    # For FracBenObs/FracBenNeuObs, draw a vline at 50% and hatch for FracBenNeuObs
    if qty in ['FracBenObs','FracBenNeuObs']:
        _plt.axvline(50.,color='k',linestyle='--',linewidth=1.25)
        if qty in ['FracBenNeuObs']:
            bars = bax.patches
            for b,bar in enumerate(bars):
                if b >= len(bars)/2:
                    if _np.mod(b,2):
                        bar.set_hatch('//')
                    else:
                        bar.set_hatch('\\\\')

    # Get a handle on the plot axis
    ax = _plt.gca()

    # Set title
    ax.set_title(plotOpt['title'],fontsize=18)

    # Set x-limits on the plot
    if qty in ['FracBenNeuObs']:
        xmin,xmax = df['FracBenObs'].min(), (df['FracBenObs'] + df['FracNeuObs']).max()
    else:
        df = df[qty]
        xmin,xmax = df.min(),df.max()
    dx = xmax - xmin
    xmin, xmax = xmin-0.1*dx,xmax+0.1*dx
    _plt.xlim(xmin,xmax)

    #xticks = _np.arange(-3,0.1,0.5)
    #ax.set_xticks(xticks)
    #x.set_xticklabels(_np.ndarray.tolist(xticks),fontsize=12)
    ax.set_xlabel(plotOpt['xlabel'],fontsize=14)
    ax.get_xaxis().get_offset_text().set_x(0)
    xfmt = _ScalarFormatter()
    xfmt.set_powerlimits((-3,3))
    ax.xaxis.set_major_formatter(xfmt)

    ax.set_ylabel('',visible=False)
    ax.set_yticklabels(df.index,fontsize=12)

    ax.autoscale(enable=True,axis='y',tight=True)
    ax.grid(False)

    # Colorbar properties
    cbar.solids.set_edgecolor("face")
    cbar.outline.set_visible(True)
    cbar.outline.set_linewidth(1.25)
    cbar.ax.tick_params(labelsize=12)

    cbar.set_label('Observation Count per Analysis',
                   rotation=90, fontsize=14, labelpad=20)
    cbarytks = _plt.getp(cbar.ax.axes, 'yticklines')
    _plt.setp(cbarytks, visible=True, alpha=alpha)

    _plt.tight_layout()

    if plotOpt['savefigure']:
        _lutils.savefigure(fname=plotOpt['figname'])

    return fig

def comparesummaryplot(df,qty='TotImp',plotOpt={}):

    alpha = plotOpt['alpha']
    barcolors = ["#000000", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"]
    barcolors = reversed(barcolors)

    width = 0.9
    df.plot.barh(width=width,stacked=True,color=barcolors,alpha=alpha,edgecolor='k',linewidth=1.25)
    _plt.axvline(0.,color='k',linestyle='-',linewidth=1.25)

    _plt.legend(frameon=False,loc=0)

    ax = _plt.gca()

    ax.set_title(plotOpt['title'],fontsize=18)

    xmin,xmax = ax.get_xlim()
    _plt.xlim(xmin,xmax)
    ax.set_xlabel(plotOpt['xlabel'],fontsize=14)
    ax.get_xaxis().get_offset_text().set_x(0)
    xfmt = _ScalarFormatter()
    xfmt.set_powerlimits((-2,2))
    ax.xaxis.set_major_formatter(xfmt)

    ax.set_ylabel('',visible=False)
    ax.set_yticklabels(df.index,fontsize=12)

    ax.autoscale(enable=True,axis='y',tight=True)
    ax.grid(False)

    _plt.tight_layout()

    if plotOpt['savefigure']:
        _lutils.savefigure(fname=plotOpt['figname'])

    return

def timeseriesplot(df,qty='TotImp',plotOpt={}):

    tmp = df.copy()
    tmp.reset_index(inplace=True)
    df = tmp.groupby(['DATETIME'])[df.columns].agg('sum')

    if plotOpt['finite']:
        df = df[_np.isfinite(df[qty])]

    fig = _plt.figure(figsize=(10,8))
    ax = fig.add_subplot(111, facecolor='w')

    alpha = plotOpt['alpha']
    logscale = plotOpt['logscale']
    cmax = plotOpt['cmax']
    cmin = plotOpt['cmin']
    cmap = _cm.get_cmap(plotOpt['cmap'])

    barcolors = getbarcolors(df['ObCnt'],logscale,cmax,cmin,cmap)
    norm = _colors.LogNorm() if logscale else _colors.Normalize()

    # dummy plot for keeping colorbar on a bar plot
    x = _np.array([0,   1,   2,   3,   4,   5,   6])
    y = _np.array([1e0, 1e1, 1e2, 1e3, 1e4, 1e5, 1e6])
    tmp = _plt.scatter(x,y,c=y,alpha=alpha,cmap=cmap,norm=norm,vmin=cmin,vmax=cmax)
    _plt.clf()
    cbar = _plt.colorbar(tmp, aspect=30, ticks=y, format='%.0e', alpha=alpha)

    width = 1.0

    df[qty].plot.bar(width=width,color=barcolors,alpha=alpha,edgecolor='k',linewidth=1.0)

    # Get a handle on the plot axis
    ax = _plt.gca()

    # Set title
    ax.set_title(plotOpt['title'], fontsize=18)

    # Set y-limits on the plot
    df = df[qty]
    ymin,ymax = df.min(),df.max()
    dy = ymax - ymin
    ymin, ymax = ymin-0.1*dy, ymax+0.1*dy
    _plt.ylim(ymin, ymax)

    labels = ax.get_xticklabels()
    #print labels
    #for l in labels:
    #    print l

    dates = df.index.get_level_values('DATETIME').unique()
    ax.xaxis.set_major_locator(_dates.DayLocator(interval=7))
    ax.xaxis.set_major_formatter(_dates.DateFormatter('%b %y'))
    labels = ax.get_xticklabels()
    _plt.setp(labels, rotation=85, fontsize=8)

    print(ax.get_xticks())
#    #xticks = _np.arange(-3,0.1,0.5)
#    #ax.set_xticks(xticks)
#    ax.set_xticklabels(_np.ndarray.tolist(xticks),fontsize=12)
#    ax.set_xlabel(plotOpt['xlabel'],fontsize=14)
    ax.get_yaxis().get_offset_text().set_y(0)
    yfmt = _ScalarFormatter()
    yfmt.set_powerlimits((-3,3))
    ax.yaxis.set_major_formatter(yfmt)
#
    ax.set_ylabel(plotOpt['xlabel'], fontsize=14)
    ax.set_xlabel('', visible=False)
#    ax.set_yticklabels(df.index,fontsize=12)

    ax.autoscale(enable=True,axis='x',tight=True)
#    ax.grid(False)
    #ax.xaxis.grid(True)

    # Colorbar properties
    cbar.solids.set_edgecolor("face")
    cbar.outline.set_visible(True)
    cbar.outline.set_linewidth(1.25)
    cbar.ax.tick_params(labelsize=12)

    cbar.set_label('Observation Count per Analysis',
                   rotation=90, fontsize=14, labelpad=20)
    cbarytks = _plt.getp(cbar.ax.axes, 'yticklines')
    _plt.setp(cbarytks, visible=True, alpha=alpha)

    _plt.tight_layout()

    if plotOpt['savefigure']:
        _lutils.savefigure(fname=plotOpt['figname'])

    return fig
