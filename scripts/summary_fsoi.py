#!/usr/bin/env python

###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date$
# $Revision$
# $Author$
# $Id$
###############################################################

'''
summary_fsoi.py - create a summary figure of all platforms or
all channels given a platform
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
from matplotlib import pyplot as plt
import lib_obimpact as loi

def main():

    parser = ArgumentParser(description = 'Create and Plot Observation Impacts Statistics',formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c','--center',help='originating center',type=str,required=True,choices=['EMC','GMAO','NRL','JMA_adj','JMA_ens','MET'])
    parser.add_argument('-r','--rootdir',help='root path to directory',type=str,default='/scratch3/NCEPDEV/stmp2/Rahul.Mahajan/test/Thomas.Auligne/FSOI',required=False)
    parser.add_argument('-p','--platform',help='platform to plot channels',type=str,default='',required=False)
    parser.add_argument('-s','--savefigure',help='save figures',action='store_true',required=False)
    parser.add_argument('-x','--exclude',help='exclude platforms',type=str,nargs='+',required=False)

    args = parser.parse_args()

    rootdir = args.rootdir
    center = args.center
    platform = args.platform
    exclude = args.exclude
    savefig = args.savefigure

    fname = '%s/work/%s/bulk_stats.h5' % (rootdir,center)

    if platform:
        search_str = 'PLATFORM == \"%s\"' % platform
        try:
            df = loi.loadDF(fname,where=search_str)
        except RuntimeError,e:
            raise RuntimeError(e.message + fname)
        df = loi.tavg_CHANNEL(df)
    else:
        fpkl = '%s/work/%s/tavg_stats.pkl' % (rootdir,center)
        if os.path.isfile(fpkl):
            overwrite = raw_input('%s exists, OVERWRITE [y/N]: ' % fpkl)
        else:
            overwrite = 'Y'
        if overwrite.upper() in ['Y','YES']:
            try:
                df = loi.loadDF(fname)
            except RuntimeError,e:
                raise RuntimeError(e.message + fname)
            df = loi.accumBulkStats(df)
            platforms = loi.Platforms(center)
            df = loi.groupBulkStats(df,platforms)
            df = loi.tavg_PLATFORM(df)
            if os.path.isfile(fpkl):
                os.remove(fpkl)
            loi.pickleDF(fpkl,df)
        else:
            df = loi.unpickleDF(fpkl)

    if exclude is not None:
        if platform:
            print 'Excluding the following channels:'
            exclude = map(int, exclude)
        else:
            print 'Excluding the following platforms:'
        print ", ".join('%s'% x for x in exclude)
        df.drop(exclude,inplace=True)

    for qty in ['TotImp','ImpPerOb','FracBenObs','FracImp','ObCnt']:
        plotOpt = loi.getPlotOpt(qty,center=center,savefigure=savefig,platform=platform)
        plotOpt['figname'] = '%s/plots/%s/%s' % (rootdir,center,plotOpt.get('figname'))
        loi.summaryplot(df,qty=qty,plotOpt=plotOpt)

    if not savefig:
        plt.show()

    sys.exit(0)

if __name__ == '__main__': main()
