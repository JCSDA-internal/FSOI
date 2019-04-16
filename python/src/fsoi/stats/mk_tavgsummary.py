#!/usr/bin/env python

###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date$
# $Revision$
# $Author$
# $Id$
###############################################################

'''
mk_tavgsummary.py - Compute time-average statistics and dump to a pkl file
'''

__author__ = "Rahul Mahajan"
__email__ = "rahul.mahajan@noaa.gov"
__copyright__ = "Copyright 2016, NOAA / NCEP / EMC"
__license__ = "GPL"
__status__ = "Prototype"
__version__ = "0.1"

import os
import sys
from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter

sys.path.append('../lib')
import lib_utils as lutils
import lib_obimpact as loi

def main():

    parser = ArgumentParser(description = 'Create time-average data given bulk statistics',formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c','--center',help='originating center',type=str,required=True,choices=['EMC','GMAO','NRL','JMA_adj','JMA_ens','MET'])
    parser.add_argument('-r','--rootdir',help='root path to directory',type=str,default='/scratch3/NCEPDEV/stmp2/Rahul.Mahajan/test/Thomas.Auligne/FSOI',required=False)

    args = parser.parse_args()

    rootdir = args.rootdir
    center = args.center

    fname = '%s/work/%s/bulk_stats.h5' % (rootdir,center)
    df = lutils.readHDF(fname,'df')
    df = loi.accumBulkStats(df)
    platforms = loi.OnePlatform()
    df = loi.groupBulkStats(df,platforms)
    df, df_std = loi.tavg(df,level='PLATFORM')

    fpkl = '%s/work/%s/tavg_stats.pkl' % (rootdir,center)
    if os.path.isfile(fpkl):
        os.remove(fpkl)
    lutils.pickle(fpkl,df)

    sys.exit(0)

if __name__ == '__main__': main()
