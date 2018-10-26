#!/usr/bin/env python

'''
summary_ts.py - create a timeseries figure of a chosen platform
'''

import os
import sys
import numpy as np
import pandas as pd
from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter
from matplotlib import pyplot as plt

sys.path.append('../lib')
import lib_utils as lutils
import lib_obimpact as loi

if __name__ == '__main__':

    parser = ArgumentParser(description='Create and Plot Observation Impacts Statistics',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--center', help='originating center', type=str, required=True,
                        choices=['EMC', 'GMAO', 'NRL', 'JMA_adj', 'JMA_ens', 'MET', 'MeteoFr'])
    parser.add_argument('--norm', help='metric norm', type=str,
                        default='dry', choices=['dry', 'moist'], required=False)
    parser.add_argument('--rootdir', help='root path to directory', type=str,
                        default='/scratch3/NCEPDEV/stmp2/Rahul.Mahajan/test/Thomas.Auligne/FSOI', required=False)
    parser.add_argument('--platform', help='platform to plot',
                        type=str, default='', required=True)
    parser.add_argument('--cycle', help='cycle to process', nargs='+',
                        type=int, default=[0], choices=[0, 6, 12, 18], required=False)
    parser.add_argument('--savefigure', help='save figures',
                        action='store_true', required=False)

    args = parser.parse_args()

    rootdir = args.rootdir
    center = args.center
    norm = args.norm
    platform = args.platform
    savefig = args.savefigure
    cycle = sorted(list(set(args.cycle)))

    cyclestr = ''.join('%02dZ' % c for c in cycle)

    fpkl = '%s/work/%s/%s/group_stats.pkl' % (rootdir,center,norm)

    if os.path.isfile(fpkl):
        df = pd.read_pickle(fpkl)
    else:
        raise IOError('%s does not exist and should, ABORT!' % fpkl)

    # Filter by cycle, platform
    df = loi.select(df,cycles=cycle, platforms=[platform])
    df = loi.summarymetrics(df)

    qtys = ['TotImp', 'ImpPerOb', 'FracBenObs',
            'FracNeuObs', 'FracImp', 'ObCnt']
    qtys = ['TotImp']
    for qty in qtys:
        plotOpt = loi.getPlotOpt(qty, cycle=cycle, center=center,
                                 savefigure=savefig, platform=platform, domain='Global')
        plotOpt['figname'] = '%s/plots/summary/%s/%s_%s' % (
            rootdir, center, plotOpt.get('figname'), cyclestr)
        loi.timeseriesplot(df,qty=qty,plotOpt=plotOpt)

    if savefig:
        plt.close('all')
    else:
        plt.show()

    sys.exit(0)
