#!/usr/bin/env python

###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date$
# $Revision$
# $Author$
# $Id$
###############################################################

'''
csv2h5.py - converts ASCII txt files into H5 files
'''

__author__ = "Rahul Mahajan"
__email__ = "rahul.mahajan@noaa.gov"
__copyright__ = "Copyright 2016, NOAA / NCEP / EMC"
__license__ = "GPL"
__status__ = "Prototype"
__version__ = "0.1"

import os
import sys
import pandas as pd
from datetime import datetime
from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter

import lib_obimpact as loi

def main():

    parser = ArgumentParser(description = 'Create Observation Impacts database',formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c','--center',help='originating center',type=str,required=True,choices=['EMC','GMAO','NRL','JMA_adj','JMA_ens','MET'])
    parser.add_argument('-r','--rootdir',help='root path to directory',type=str,default='/scratch3/NCEPDEV/stmp2/Rahul.Mahajan/test/Thomas.Auligne/FSOI',required=False)
    parser.add_argument('-b','--begin_date',help='dataset begin date',type=str,default='2014120100',required=False)
    parser.add_argument('-e','--end_date',help='dataset end date',type=str,default='2015022800',required=False)
    parser.add_argument('-i','--interval',help='dataset interval',type=int,default=24,required=False)

    args = parser.parse_args()

    center = args.center
    rootdir = args.rootdir
    bdate = datetime.strptime(args.begin_date,'%Y%m%d%H')
    edate = datetime.strptime(args.end_date,'%Y%m%d%H')
    interval = args.interval

    skip_dates = []

    fname_raw = '%s/work/%s/raw_data.h5' % (rootdir,center)
    if os.path.isfile(fname_raw): os.remove(fname_raw)
    fname_bulk = '%s/work/%s/bulk_stats.h5' % (rootdir,center)
    if os.path.isfile(fname_bulk): os.remove(fname_bulk)

    for adate in pd.date_range(bdate,edate,freq='%dH'%interval):
        if adate in skip_dates: continue
        fname = '%s/ascii/%s/%s_%s.txt' % (rootdir,center,center,adate.strftime('%Y%m%d%H'))
        if not os.path.isfile(fname): continue
        df = loi.read_ascii(adate,fname)
        loi.dumpDF(fname_raw,df)
        df = loi.BulkStats(df)
        loi.dumpDF(fname_bulk,df)

    sys.exit(0)

if __name__ == '__main__': main()
