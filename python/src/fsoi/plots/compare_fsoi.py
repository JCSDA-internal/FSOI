"""
lib_obimpact.py contains functions for FSOI project
Some functions can be used elsewhere
"""

import pandas as pd
import numpy as np
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from matplotlib import pyplot as plt
import fsoi.stats.lib_utils as lutils
import fsoi.stats.lib_obimpact as loi


def load_centers(rootdir, centers, norm, cycle):
    """

    :param rootdir:
    :param centers:
    :param norm:
    :param cycle:
    :return:
    """
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


def sort_centers(DF):
    """

    :param DF:
    :return:
    """
    # count the number of centers that use each platform
    platform_count = {}
    for i in range(len(DF)):
        platforms_in_center = DF[i].index.get_level_values('PLATFORM').unique()
        for platform in list(platforms_in_center):
            platform = platform.upper()
            if platform in platform_count:
                platform_count[platform] += 1
            else:
                platform_count[platform] = 1

    # set 'pref' to a list of platforms included by 2 or more centers
    pref = []
    for key in platform_count:
        if platform_count[key] > 1:
            pref.append(key)

# CHECK TO SEE IF 2019-05-11 00Z GMAO is fixed: Only contains WINDSAT or WindSat
    df = []
    for i in range(len(DF)):
        # create a list of platforms to exclude
        exclusion_list = []
        for platform in DF[i].index.get_level_values('PLATFORM').unique():
            if platform.upper() not in pref:
                exclusion_list.append(platform)

        # exclude the platforms in the list
        DF[i].drop(exclusion_list, inplace=True)

        # add the data frame to the list of data frames
        df.append(DF[i])

    return df, pref


def compare_fsoi_main():
    """

    :return:
    """
    parser = ArgumentParser(description='Create and Plot Comparison Observation Impact Statistics',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--rootdir', help='root path to directory', type=str, required=True)
    parser.add_argument('--platform', help='platforms to plot', type=str, default='full',
                        choices=['full', 'conv', 'rad'], required=False)
    parser.add_argument('--cycle', help='cycle to process', nargs='+', type=int,
                        choices=[0, 6, 12, 18], required=True)
    parser.add_argument('--norm', help='metric norm', type=str, choices=['dry', 'moist', 'both'],
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

    DF = load_centers(rootdir, centers, norm, cycle)
    DF, platforms = sort_centers(DF)

    for qty in ['TotImp', 'ImpPerOb', 'FracBenObs', 'FracNeuObs', 'FracImp', 'ObCnt']:
        plotOpt = loi.getPlotOpt(qty, savefigure=savefig, center=None, cycle=cycle)
        plotOpt['figname'] = '%s/plots/compare/%s/%s_%s' % \
                             (rootdir, platform, plotOpt.get('figname'), cyclestr)
        tmpdf = []
        for c, center in enumerate(centers):
            tmp = DF[c][qty]
            tmp.name = center
            index = []
            for single_platform in tmp.index:
                index.append((single_platform.upper()))
            tmp.index = pd.CategoricalIndex(data=index, name='PLATFORM')
            tmpdf.append(tmp)

        df = pd.concat(tmpdf, axis=1, sort=True)
        platforms.reverse()
        df = df.reindex(platforms)
        loi.comparesummaryplot(df, palette, qty=qty, plotOpt=plotOpt)

    if savefig:
        plt.close('all')
    else:
        plt.show()


if __name__ == '__main__':
    compare_fsoi_main()
