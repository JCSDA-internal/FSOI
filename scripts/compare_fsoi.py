#!/usr/bin/env python

###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date$
# $Revision$
# $Author$
# $Id$
###############################################################

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

import sys
import pandas as pd
from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter
from matplotlib import pyplot as plt
import lib_obimpact as loi

def load_centers(rootdir,centers,platform=''):

    DF = []
    for center in centers:

        if platform:
            search_str = 'PLATFORM == \"%s\"' % platform
            fname = '%s/work/%s/bulk_stats.h5' % (rootdir,center)
            df = loi.loadDF(fname,where=search_str)
            df = loi.tavg_CHANNEL(df)
        else:
            fname = '%s/work/%s/tavg_stats.pkl' % (rootdir,center)
            df = loi.unpickleDF(fname)

        DF.append(df)

    return DF

def sort_centers(DF,pref):
    df = []
    for i in range(len(DF)):
        tmp = DF[i]
        pcenter = tmp.index.get_level_values('PLATFORM').unique()
        exclude = list(set(pcenter)-set(pref))
        tmp.drop(exclude,inplace=True)
        df.append(tmp)
    return df

def main():

    parser = ArgumentParser(description = 'Create and Plot Comparison Observation Impact Statistics',formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-r','--rootdir',help='root path to directory',type=str,default='/scratch3/NCEPDEV/stmp2/Rahul.Mahajan/test/Thomas.Auligne/FSOI',required=False)
    parser.add_argument('-p','--platform',help='platforms to plot',type=str,default='full',choices=['full','conv','rad'],required=False)
    parser.add_argument('-s','--savefigure',help='save figures',action='store_true',required=False)

    args = parser.parse_args()

    rootdir = args.rootdir
    platform = args.platform
    savefig = args.savefigure

    centers = ['JMA_adj','GMAO','NRL','MET','JMA_ens','EMC']
    platforms = loi.RefPlatform(platform)

    DF = load_centers(rootdir,centers)
    DF = sort_centers(DF,platforms)

    for qty in ['TotImp','ObCnt','ImpPerOb','FracBenObs','FracImp']:
        plotOpt = loi.getPlotOpt(qty,savefigure=savefig)
        plotOpt['figname'] = '%s/plots/compare/unstacked/%s/%s' % (rootdir,platform,plotOpt.get('figname'))
        tmpdf = []
        for c,center in enumerate(centers):
            tmp = DF[c][qty]
            tmp.name = center
            tmpdf.append(tmp)
        df = pd.concat(tmpdf,axis=1)
        df = df.reindex(reversed(platforms))
        loi.comparesummaryplot(df,qty=qty,plotOpt=plotOpt)

    if not savefig:
        plt.show()

    sys.exit(0)

if __name__ == '__main__': main()
