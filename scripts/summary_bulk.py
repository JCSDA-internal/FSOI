#!/usr/bin/env python

'''
summary_bulk.py - reads raw data and writes out accumulated bulk statistics
'''

import os
import sys
import pandas as pd
from datetime import datetime
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

sys.path.append('../lib')
import lib_utils as lutils
import lib_obimpact as loi

if __name__ == '__main__':

    parser = ArgumentParser(description='Create Observation Impacts database',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--center', help='originating center', type=str, required=True,
                        choices=['EMC', 'GMAO', 'NRL', 'JMA_adj', 'JMA_ens', 'MET', 'MeteoFr'])
    parser.add_argument('--norm', help='norm', type=str,
                        default='dry', choices=['dry', 'moist'], required=False)
    parser.add_argument('--rootdir', help='root path to directory', type=str,
                        default='/scratch3/NCEPDEV/stmp2/Rahul.Mahajan/test/Thomas.Auligne/FSOI', required=False)
    parser.add_argument('--begin_date', help='dataset begin date',
                        type=str, default='2014120100', required=False)
    parser.add_argument('--end_date', help='dataset end date',
                        type=str, default='2015022818', required=False)
    parser.add_argument('--interval', help='dataset interval',
                        type=int, default=6, required=False)

    args = parser.parse_args()

    center = args.center
    norm = args.norm
    rootdir = args.rootdir
    bdate = datetime.strptime(args.begin_date, '%Y%m%d%H')
    edate = datetime.strptime(args.end_date, '%Y%m%d%H')
    interval = args.interval

    skip_dates = []

    # Create a work directory if it does not exist
    bulkdir= '%s/work/%s/%s' % (rootdir, center, norm)
    if not os.path.exists(bulkdir):
        os.makedirs(bulkdir)

    fname_bulk = '%s/bulk_stats.h5' % bulkdir
    if os.path.isfile(fname_bulk):
        os.remove(fname_bulk)

    for adate in pd.date_range(bdate, edate, freq='%dH' % interval):
        adatestr = adate.strftime('%Y%m%d%H')
        if adate in skip_dates:
            continue
        fname = '%s/data/%s/%s.%s.%s.h5' % (rootdir,
                                            center, center, norm, adatestr)
        if not os.path.isfile(fname):
            print('%s : %s does not exist, SKIPPING ...' % (adatestr, fname))
            continue
        df = lutils.readHDF(fname, 'df')
        df = loi.BulkStats(df)
        lutils.writeHDF(fname_bulk, 'df', df, complevel=1,
                        complib='zlib', fletcher32=True)

    sys.exit(0)
