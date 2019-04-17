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
import numpy as np
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from matplotlib import pyplot as plt

import fsoi.stats.lib_utils as lutils
import fsoi.stats.lib_obimpact as loi


def load_centers(rootdir, centers, norm, cycle):
    DF = []
    for center in centers:

        fpkl = '%s/work/%s/%s/group_stats.pkl' % (rootdir, center, norm)
        df = lutils.unpickle(fpkl)
        indx = df.index.get_level_values('DATETIME').hour == -1
        for c in cycle:
            indx = np.ma.logical_or(indx, df.index.get_level_values('DATETIME').hour == c)
        df = df[indx]

        df, df_std = loi.tavg(df, level='PLATFORM')
        df = loi.summarymetrics(df)

        DF.append(df)

    return DF


def sort_centers(DF, pref):
    df = []
    for i in range(len(DF)):
        tmp = DF[i]
        pcenter = tmp.index.get_level_values('PLATFORM').unique()
        exclude = list(set(pcenter) - set(pref))
        tmp.drop(exclude, inplace=True)
        df.append(tmp)
    return df


def compare_fsoi_main():
    parser = ArgumentParser(description='Create and Plot Comparison Observation Impact Statistics',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--rootdir', help='root path to directory', type=str, required=True)
    parser.add_argument('--platform', help='platforms to plot', type=str, default='full',
                        choices=['full', 'conv', 'rad'], required=False)
    parser.add_argument('--cycle', help='cycle to process', nargs='+', type=int,
                        choices=[0, 6, 12, 18], required=True)
    parser.add_argument('--norm', help='metric norm', type=str, choices=['dry', 'moist'],
                        required=True)
    parser.add_argument('--savefigure', help='save figures', action='store_true', required=False)
    parser.add_argument('--centers', help='list of centers', type=str, nargs='+',
                        choices=['EMC', 'GMAO', 'NRL', 'JMA_adj', 'JMA_ens', 'MET', 'MeteoFr'],
                        required=True)

    args = parser.parse_args()

    rootdir = args.rootdir
    platform = args.platform
    cycle = sorted(list(set(args.cycle)))
    norm = args.norm
    savefig = args.savefigure
    centers = args.centers
    palette = loi.getcomparesummarypalette(centers)

    cyclestr = ''.join('%02dZ' % c for c in cycle)

    platforms = loi.RefPlatform(platform)

    DF = load_centers(rootdir, centers, norm, cycle)
    DF = sort_centers(DF, platforms)

    for qty in ['TotImp', 'ImpPerOb', 'FracBenObs', 'FracNeuObs', 'FracImp', 'ObCnt']:
        plotOpt = loi.getPlotOpt(qty, savefigure=savefig, center=None, cycle=cycle)
        plotOpt['figname'] = '%s/plots/compare/%s/%s_%s' % (
        rootdir, platform, plotOpt.get('figname'), cyclestr)
        tmpdf = []
        for c, center in enumerate(centers):
            tmp = DF[c][qty]
            tmp.name = center
            tmpdf.append(tmp)
        df = pd.concat(tmpdf, axis=1, sort=True)
        df = df.reindex(reversed(platforms))
        loi.comparesummaryplot(df, palette, qty=qty, plotOpt=plotOpt)

    if savefig:
        plt.close('all')
    else:
        plt.show()


if __name__ == '__main__': compare_fsoi_main()
