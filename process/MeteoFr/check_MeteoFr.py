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
from datetime import datetime
from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter
from matplotlib import pyplot as plt

def get_files(datadir):
    '''
    Get a list of files in a directory
    '''

    files = glob.glob('%s/deltaJ.*.bg.lst' % datadir)

    return files

def parse_date(datadir,adate):
    '''
    Call the appropriate file parser depending on platform
    '''

    flist = get_files(datadir)
    tmpdf = []
    for fname in flist:
        if os.stat(fname).st_size == 0:
            print '%s is an empty file ... skipping' % fname
            continue
        tmpdf.append(read_file(fname))
    data = pd.concat(tmpdf,axis=0)

    old_platform_names = ['aircraft', 'buoy', 'gpsro', 'pilot', 'satem_airs', 'satem_amsua',
    'satem_amsub', 'satem_atms', 'satem_cris', 'satem_goesimg', 'satem_hirs', 'satem_iasi',
    'satem_mhs', 'satem_seviri', 'satem_ssmis', 'satwind', 'scatt', 'synop_gpssol', 'synop_insitu',
    'temp']
    new_platform_names = ['Aircraft', 'Buoy', 'GPSRO', 'Pilot', 'AIRS', 'AMSUA', 'AMSUB', 'ATMS',
    'CrIS', 'GOES', 'HIRS', 'IASI', 'MHS', 'Seviri', 'SSMIS', 'SatWind', 'Scat', 'GPSSOL', 'Surface',
    'Radiosonde']
    data['PLATFORM'].replace(to_replace=old_platform_names,value=new_platform_names,inplace=True)

    data['DATETIME'] = adate
    data.set_index(['DATETIME','PLATFORM'],inplace=True)
    data = data.reorder_levels(['DATETIME','PLATFORM'])

    data['TotImp'] = data['TotImp'].astype(np.float) * 1.e-5
    data['TotImpDet'] = data['TotImpDet'].astype(np.float) * 1.e-5
    data['ObCnt'] = data['ObCnt'].astype(np.int)
    data['ObCntBen'] = data['ObCntBen'].astype(np.int)
    data['ObCntDet'] = data['ObCntDet'].astype(np.int)

    return data

def read_file(fname):
    '''
    Read a file into a dataframe
    '''

    names = ['obtype','PLATFORM','TotImp','ObCnt','ObCntBen','ObCntDet','TotImpDet']
    try:
        data = pd.read_csv(fname,header=None,delim_whitespace=True,skipinitialspace=True,names=names)
    except RuntimeError:
        raise
    data.drop(['obtype'],axis=1,inplace=True)

    return data

def main():

    parser = ArgumentParser(description = 'Process Meteo France data',formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i','--indir',help='path to input data directory',type=str,required=True)
    parser.add_argument('-o','--outdir',help='path to output directory',type=str,required=True)
    parser.add_argument('-n','--norm',help='norm to process',type=str,required=True)
    parser.add_argument('-b','--begin_date',help='dataset begin date',type=str,default='2014120100',required=False)
    parser.add_argument('-e','--end_date',help='dataset end date',type=str,default='2015022818',required=False)
    args = parser.parse_args()

    datapthin = args.indir
    datapthout = args.outdir
    norm = args.norm
    bdate = datetime.strptime(args.begin_date,('%Y%m%d%H'))
    edate = datetime.strptime(args.end_date,('%Y%m%d%H'))

    tmpdata = []
    for adate in pd.date_range(bdate,edate,freq='6H'):

        adatestr = adate.strftime('%Y%m%d%H')
        print 'processing %s' % adatestr

        datadir = os.path.join(datapthin,norm,adatestr)

        tmpdata.append(parse_date(datadir,adate))

    df = pd.concat(tmpdata,axis=0)

    # Write to a file
    fname_out = os.path.join(datapthout,'deltaJ.%s.h5'%norm)
    if os.path.isfile(fname_out): os.remove(fname_out)
    hdf = pd.HDFStore(fname_out)
    hdf.put('df',df,format='table',append=True)
    hdf.close()

    # Compute time-mean and plot
    dfm = df.mean(level='PLATFORM')
    dfm.sort_values(by='TotImp',inplace=True,ascending=False)
    dfs = df.std(level='PLATFORM')
    ax = dfm['TotImp'].plot(kind='barh',xerr=dfs,width=1.,alpha=0.6,title='Meteo France Total Impact')
    ax.figure.tight_layout()
    plt.show()

    sys.exit(0)

if __name__ == '__main__': main()
