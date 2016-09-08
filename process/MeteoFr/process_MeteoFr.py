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
import numpy as np
import pandas as pd
from time import time
from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter

def get_files(datadir):
    '''
    Get a list of files in a directory
    '''

    files = glob.glob('%s/fic_odb.*.bg.lst' % datadir)

    return files

def parse_file(fname):
    '''
    Call the appropriate file parser depending on platform
    '''

    platform = fname.split('.')[1]

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
    new_names = ['latitude','longitude','platform','variable','level','omf','impact','obserr']
    data.rename(columns=dict(zip(old_names,new_names)), inplace=True)

    data['channel'] = 999

    return data

def parse_satem(fname):
    '''
    Parse satellite radiances and scatterometer file
    '''

    instrument = fname.split('.')[1].split('_')[-1]

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
        new_names = ['latitude','longitude','variable','level','omf','impact','obserr','platform']
        data['channel'] = 999
    else:
        new_names = ['latitude','longitude','variable','channel','omf','impact','obserr','platform']
        data['level'] = 999
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

    data['lat@hdr'] = data['lat@hdr'] * 180./np.pi
    data['lon@hdr'] = data['lon@hdr'] * 180./np.pi
    data['fc_sens_obs@body'] = data['fc_sens_obs@body'] * data['fg_depar@body']

    data['statid@hdr'].replace(to_replace=sat_ids,value=sat_names,inplace=True)
    data['varno@body'].replace(to_replace=var_ids,value=var_names,inplace=True)

    old_names = ['lat@hdr','lon@hdr','varno@body','vertco_reference_1@body','fg_depar@body','fc_sens_obs@body','obs_error@errstat','statid@hdr']
    new_names = ['latitude','longitude','variable','level','omf','impact','obserr','platform']
    data.rename(columns=dict(zip(old_names,new_names)), inplace=True)

    data['channel'] = 999

    return data

def parse_gpsro(fname):
    '''
    Parse GPSRO file
    '''

    var_ids,var_names = get_varid_varname()

    data = read_file(fname)

    data.drop(['obstype@hdr','codetype@hdr','instrument_type@hdr','vertco_reference_2@body','statid@hdr'],axis=1,inplace=True)

    data['varno@body'].replace(to_replace=var_ids,value=var_names,inplace=True)

    old_names = ['lat@hdr','lon@hdr','varno@body','vertco_reference_1@body','fg_depar@body','fc_sens_obs@body','obs_error@errstat']
    new_names = ['latitude','longitude','variable','level','omf','impact','obserr']
    data.rename(columns=dict(zip(old_names,new_names)), inplace=True)

    data['channel'] = 999
    data['platform'] = 'GPSRO'

    return data

def read_file(fname):
    '''
    Read a file into a dataframe
    Drop the useless columns
    Convert latitude, longitude from radians to degrees
    Calculate observation impact as the product of sensitivity and OmF
    '''

    try:
        data = pd.read_csv(fname,header=0,delim_whitespace=True,skipinitialspace=True,index_col=False,quotechar="'")
    except RuntimeError:
        raise

    data.drop(['date@hdr','time@hdr','seqno@hdr','an_depar@body','fg_error@errstat'],axis=1,inplace=True)

    data['lat@hdr'] = data['lat@hdr'] * 180./np.pi
    data['lon@hdr'] = data['lon@hdr'] * 180./np.pi
    data['fc_sens_obs@body'] = data['fc_sens_obs@body'] * data['fg_depar@body']

    return data

def reorder_columns(df):

    new_order = ['platform','variable','channel','longitude','latitude','level','impact','omf','obserr']
    df = df[new_order]

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
                165,
                35,36,135,37,
                32,
                34,134]
    plat_names = ['Land_Surface','Land_Surface','RADOME',
                  'Ship','Ship',
                  'GPSZTD',
                  'AIREP','AMDAR','ACARS',
                  'Drifting_Buoy',
                  'Radiosonde','Radiosonde','Dropsonde','Radiosonde',
                  'Pilot',
                  'Profiler','Profiler']

    return plat_ids,plat_names

def get_satwindid_satwindname():

    sat_ids = [206,207,209,223,
               783,784,
               172,
               257,259,
               54,57]
    sat_names = ['AVHRR_NOAA15','AVHRR_NOAA16','AVHRR_NOAA18','AVHRR_NOAA19',
                 'MODIS_TERRA','MODIS_AQUA',
                 'Imager_GMS',
                 'Imager_GOES13','Imager_GOES15',
                 'Imager_METEOSAT7','Imager_METEOSAT10']

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

def write_data(df,fname):
    '''
    Convert dataframe into string and write to file
    '''

    def _fmts15(x): return '{0:<15}'.format(x)
    def _fmts10(x): return '{0:<10}'.format(x)
    def _fmti(  x): return '%5d'    % x
    def _fmtf10(x): return '%10.4f' % x
    def _fmtf15(x): return '%15.8e' % x

    fh = open(fname,'a')

    formatters = [_fmts15,_fmts10,_fmti,_fmtf10,_fmtf10,_fmtf10,_fmtf15,_fmtf15,_fmtf15]
    try:
        df.to_string(buf=fh,header=False,index=False,formatters=formatters)
    except RuntimeError:
        raise

    fh.writelines('\n')
    fh.close()

    return

def main():

    parser = ArgumentParser(description = 'Process Meteo France data',formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i','--indir',help='path to data directory',type=str,required=True)
    parser.add_argument('-o','--output',help='Processed Meteo France file',type=str,required=True)
    parser.add_argument('-a','--adate',help='analysis date to process',metavar='YYYYMMDDHH',required=True)
    parser.add_argument('-n','--norm',help='norm to process',type=str,required=True)
    args = parser.parse_args()

    datapth = args.indir
    fname_out = args.output
    adate = args.adate
    norm = args.norm

    if os.path.isfile(fname_out): os.remove(fname_out)

    flist = get_files(os.path.join(datapth,norm,adate))
    nobs = 0
    for fname in flist:

        ffname = os.path.basename(fname)

        print 'processing %s' % ffname

        if os.stat(fname).st_size == 0:
            print '%s is an empty file ... skipping' % ffname
            continue

        data = parse_file(fname)
        print 'number of observations in %s = %d ' % (ffname,len(data))

        nobs += len(data)

        write_data(data,fname_out)

    print 'total number of observations for %s = %d' % (adate, nobs)

    sys.exit(0)

if __name__ == '__main__': main()
