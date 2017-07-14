#!/usr/bin/env python
###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date$
# $Revision$
# $Author$
# $Id$
###############################################################

import os
import sys
import glob
import shutil
import tarfile
import numpy as np
import pandas as pd
from datetime import datetime
from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter

sys.path.append('../../lib')
import lib_utils as lutils

def parse_file(adate,fname):
    '''
    Call the appropriate file parser depending on platform
    '''

    ffname = os.path.basename(fname)
    platform = ffname.split('.')[1]

    if platform in ['aircraft', 'buoy' , 'pilot', 'synop_gpssol', 'synop_insitu', 'temp']:
        data = parse_conv(fname)

    elif platform in ['satem_airs', 'satem_amsua', 'satem_amsub', 'satem_atms', 'satem_cris', 'satem_goesimg', 'satem_hirs', 'satem_iasi', 'satem_mhs', 'satem_seviri', 'satem_ssmis', 'scatt']:
        data = parse_satem(fname)

    elif platform in ['satwind']:
        data = parse_satwind(fname)

    elif platform in ['gpsro']:
        data = parse_gpsro(fname)

    else:
        return None

    data['DATETIME'] = adate
    data = reorder_columns(data)

    return data

def parse_conv(fname):
    '''
    Parse conventional observations file
    '''

    plat_ids,plat_names = get_platid_platname()
    var_ids,var_names = get_varid_varname()

    data = read_file(fname)

    data.drop(['obstype@hdr','statid@hdr'],axis=1,inplace=True)

    data['varno@body'].replace(to_replace=var_ids,value=var_names,inplace=True)
    data['codetype@hdr'].replace(to_replace=plat_ids,value=plat_names,inplace=True)

    old_names = ['lat@hdr','lon@hdr','codetype@hdr','varno@body','vertco_reference_1@body','fg_depar@body','fc_sens_obs@body','obs_error@errstat']
    new_names = ['LATITUDE','LONGITUDE','PLATFORM','OBTYPE','PRESSURE','OMF','IMPACT','OBERR']
    data.rename(columns=dict(zip(old_names,new_names)), inplace=True)

    data['CHANNEL'] = 999

    return data

def parse_satem(fname):
    '''
    Parse satellite radiances and scatterometer file
    '''

    ffname = os.path.basename(fname)
    instrument = ffname.split('.')[1].split('_')[-1]

    var_ids,var_names = get_varid_varname()
    sat_ids,sat_names = get_satid_satname()

    if instrument == 'scatt':
        sat_names = ['ASCAT' + '_%s' % sat_name for sat_name in sat_names]
    else:
        sat_names = [instrument.upper() + '_%s' % sat_name for sat_name in sat_names]

    data = read_file(fname)

    data.drop(['obstype@hdr','codetype@hdr','instrument_type@hdr','sensor@hdr'],axis=1,inplace=True)

    data['statid@hdr'].replace(to_replace=sat_ids,value=sat_names,inplace=True)
    data['varno@body'].replace(to_replace=var_ids,value=var_names,inplace=True)

    old_names = ['lat@hdr','lon@hdr','varno@body','vertco_reference_1@body','fg_depar@body','fc_sens_obs@body','obs_error@errstat','statid@hdr']
    if instrument == 'scatt':
        new_names = ['LATITUDE','LONGITUDE','OBTYPE','PRESSURE','OMF','IMPACT','OBERR','PLATFORM']
        data['CHANNEL'] = 999
    else:
        new_names = ['LATITUDE','LONGITUDE','OBTYPE','CHANNEL','OMF','IMPACT','OBERR','PLATFORM']
        data['PRESSURE'] = 999
    data.rename(columns=dict(zip(old_names,new_names)), inplace=True)

    return data

def parse_satwind(fname):
    '''
    Parse satellite winds file
    '''

    sat_ids,sat_names = get_satwindid_satwindname()
    var_ids,var_names = get_varid_varname()

    data = read_file(fname)

    data.drop(['obstype@hdr','codetype@hdr','comp_method@satob'],axis=1,inplace=True)

    data['statid@hdr'].replace(to_replace=sat_ids,value=sat_names,inplace=True)
    data['varno@body'].replace(to_replace=var_ids,value=var_names,inplace=True)

    old_names = ['lat@hdr','lon@hdr','varno@body','vertco_reference_1@body','fg_depar@body','fc_sens_obs@body','obs_error@errstat','statid@hdr']
    new_names = ['LATITUDE','LONGITUDE','OBTYPE','PRESSURE','OMF','IMPACT','OBERR','PLATFORM']
    data.rename(columns=dict(zip(old_names,new_names)), inplace=True)

    data['CHANNEL'] = 999

    return data

def parse_gpsro(fname):
    '''
    Parse GPSRO file
    '''

    var_ids,var_names = get_varid_varname()

    data = read_file(fname)

    data.drop(['obstype@hdr','codetype@hdr','instrument_type@hdr','vertco_reference_1@body','statid@hdr'],axis=1,inplace=True)

    data['varno@body'].replace(to_replace=var_ids,value=var_names,inplace=True)

    old_names = ['lat@hdr','lon@hdr','varno@body','vertco_reference_2@body','fg_depar@body','fc_sens_obs@body','obs_error@errstat']
    new_names = ['LATITUDE','LONGITUDE','OBTYPE','PRESSURE','OMF','IMPACT','OBERR']
    data.rename(columns=dict(zip(old_names,new_names)), inplace=True)

    data['CHANNEL'] = 999
    data['PLATFORM'] = 'GPSRO'

    return data

def read_file(fname):
    '''
    Read a file into a dataframe
    Drop the useless columns
    Convert latitude, LONGITUDE from radians to degrees
    Rescale impact by 1.e5 because units in the file are JPa/kg
    '''

    try:
        data = pd.read_csv(fname,header=0,delim_whitespace=True,skipinitialspace=True,index_col=False,quotechar="'")
    except RuntimeError:
        raise

    data.drop(['date@hdr','time@hdr','seqno@hdr','an_depar@body','fg_error@errstat'],axis=1,inplace=True)

    data['lat@hdr'] = data['lat@hdr'] * 180./np.pi
    data['lon@hdr'] = data['lon@hdr'] * 180./np.pi
    data['fc_sens_obs@body'] = data['fc_sens_obs@body'] * 1.e-5

    return data

def reorder_columns(df):

    new_order = ['DATETIME','PLATFORM','OBTYPE','CHANNEL','LONGITUDE','LATITUDE','PRESSURE','IMPACT','OMF','OBERR']
    df = df[new_order]
    df.set_index(new_order[0:4],inplace=True)

    return df

def get_varid_varname():

    var_ids   = [1,   2,  3,  4,  7,  41,    42,    58,    119, 124, 125, 128,  162]
    var_names = ['Z','T','U','V','Q','U10m','V10m','RH2m','Tb','Ua','Va','APD','BA']

    return var_ids,var_names

def get_platid_platname():

    plat_ids = [11,14,16,
                21,24,
                110,
                141,144,145,
                165,63,
                35,36,135,37,
                32,
                34,134]
    plat_names = ['Land_Surface','Land_Surface','RADOME',
                  'Ship','Ship',
                  'GPSZTD',
                  'AIREP','AMDAR','ACARS',
                  'Drifting_Buoy','Misc_Buoy',
                  'Radiosonde','Radiosonde','Dropsonde','Radiosonde',
                  'Pilot',
                  'Profiler','Profiler']

    return plat_ids,plat_names

def get_satwindid_satwindname():

    sat_ids = [206,207,209,223,
               783,784,
               172,
               257,259,
               54,57,
               55,224]
    sat_names = ['AVHRR_NOAA15','AVHRR_NOAA16','AVHRR_NOAA18','AVHRR_NOAA19',
                 'MODIS_TERRA','MODIS_AQUA',
                 'Imgr_GMS',
                 'Imgr_GOES13','Imgr_GOES15',
                 'Imgr_METEOSAT7','Imgr_METEOSAT10',
                 'Misc_SatWind','Misc_SatWind']

    return sat_ids,sat_names

def get_satid_satname():

    sat_ids = [784,222,
               3,4,
               206,207,209,223,
               224,
               257,259,
               54,57,
               249,285,286,
               783,
               172]
    sat_names = ['AQUA','AQUA',
                 'METOP-B','METOP-A',
                 'NOAA15','NOAA16','NOAA18','NOAA19',
                 'NPP',
                 'GOES13','GOES15',
                 'METEOSAT7','METEOSAT10',
                 'DMSP16','DMSP17','DMSP18',
                 'TERRA',
                 'GMS']

    return sat_ids,sat_names

if __name__ == '__main__':

    parser = ArgumentParser(description = 'Process Meteo France data',formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i','--indir',help='path to data directory',type=str,required=True)
    parser.add_argument('-o','--output',help='Processed Meteo France HDF file',type=str,required=True)
    parser.add_argument('-a','--adate',help='analysis date to process',metavar='YYYYMMDDHH',required=True)
    parser.add_argument('-n','--norm',help='norm to process',type=str,required=True)
    args = parser.parse_args()

    datapth = args.indir
    fname_out = args.output
    adate = datetime.strptime(args.adate,'%Y%m%d%H')
    norm = args.norm

    datadir = os.path.join(datapth,norm,args.adate)
    workdir = os.path.join(datadir,'work')
    if os.path.isdir(workdir): shutil.rmtree(workdir)
    os.makedirs(workdir)

    tf = tarfile.open('%s/fic_odb.all_obs.bg.tar.gz' % datadir)
    tf.extractall(path=workdir)
    flist = glob.glob('%s/fic_odb.*.bg.lst' % workdir)

    nobs = 0
    bufr = []
    for fname in flist:

        ffname = os.path.basename(fname)

        print 'processing %s' % ffname

        if os.stat(fname).st_size == 0:
            print '%s is an empty file ... skipping' % ffname
            continue

        data = parse_file(adate,fname)
        print 'number of observations in %s = %d ' % (ffname,len(data))

        nobs += len(data)
        bufr.append(data)

    if bufr != []:
        df = pd.concat(bufr)
        if os.path.isfile(fname_out): os.remove(fname_out)
        lutils.writeHDF(fname_out,'df',df,complevel=1,complib='zlib',fletcher32=True)

    print 'total number of observations for %s = %d' % (args.adate, nobs)

    shutil.rmtree(workdir)

    sys.exit(0)
