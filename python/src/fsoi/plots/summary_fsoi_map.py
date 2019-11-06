"""
summary_fsoi_map.py - make spatial maps of FSOI
"""

import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from matplotlib import pyplot as plt
import numpy as np
import fsoi.stats.lib_mapping as lmapping
import fsoi.stats.lib_utils as lutils
import fsoi.stats.lib_obimpact as loi

def main():
    """

    :return:
    """
    parser = ArgumentParser(description='Create and Plot Observation Impact Summary Maps',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--rootdir', help='root path to directory', type=str,
                        default='/scratch3/NCEPDEV/stmp2/Rahul.Mahajan/test/Thomas.Auligne/FSOI',
                        required=False)
    parser.add_argument('--center', help='originating center', type=str,
                        choices=['GMAO', 'NRL', 'MET', 'MeteoFr', 'JMA_adj', 'JMA_ens', 'EMC'],
                        required=True)
    parser.add_argument('--norm', help='metric norm', type=str, default='dry', choices=['dry', 'moist'],
                        required=False)
    parser.add_argument('--cycle', help='cycle to process', nargs='+', type=int, default=None,
                        choices=[0, 6, 12, 18], required=False)
    parser.add_argument('--platform', help='platform to plot', type=str, required=True)
    parser.add_argument('--obtype', help='observation types to include', nargs='+', type=str,
                        default=None, required=False)
    parser.add_argument('--channel', help='channel to process', nargs='+', type=int, default=None,
                        required=False)
    parser.add_argument('--savefigure', help='save figures', action='store_true', required=False)

    args = parser.parse_args()

    center = args.center
    platform = args.platform
    obtype = args.obtype
    obtype = args.obtype
    rootdir = args.rootdir
    norm = args.norm
    cycle = args.cycle
    channel = args.channel
    savefig = args.savefigure

    if cycle is None:
        cycle = [0, 6, 12, 18]
        cyclestr = ''.join('%02dZ' % c for c in cycle)
    else:
        cycle = sorted(list(set(args.cycle)))
        cyclestr = ''.join('%02dZ' % c for c in cycle)

    fbinned = '%s/work/%s/%s/%s.binned.h5' % (rootdir, center, norm, platform.lower())
    df = lutils.readHDF(fbinned, 'df')

    # Select by cycles, obtypes and channels
    df = loi.select(df, cycles=cycle, obtypes=obtype, channels=channel)

    # Aggregate over observation types
    tmp = df.reset_index()
    tmp.drop(['PLATFORM'], axis=1, inplace=True)
    names = ['DATETIME', 'LONGITUDE', 'LATITUDE']
    df = tmp.groupby(names)['TotImp'].agg('sum')

    cmap = plt.cm.get_cmap(name='coolwarm', lut=20)

    # plot means
    tmp = df.reset_index()
    names = ['LONGITUDE', 'LATITUDE']
    df2 = tmp.groupby(names)['TotImp'].agg('mean').reset_index()

    lats = df2['LATITUDE'].values
    lons = df2['LONGITUDE'].values
    imps = df2['TotImp'].values * 1.e3

    cmax = lutils.roundNumber(np.mean(np.abs(imps)))

    plotOpt = loi.getPlotOpt('TotImp', cycle=cycle, center=center, savefigure=savefig,
                             platform=platform, domain=None)

    plt.figure()

    proj = lmapping.Projection('mill', resolution='c', llcrnrlat=-80., urcrnrlat=80.)
    bmap = lmapping.createMap(proj)
    x, y = bmap(lons, lats)

    lmapping.drawMap(bmap, proj, fillcontinents=False)
    sc = bmap.scatter(x, y, c=imps, s=20, marker='s', cmap=cmap, alpha=1.0, edgecolors='face',
                      vmin=-cmax, vmax=cmax)
    bmap.colorbar(sc, 'right', size='5%', pad='2%')

    titlestr = plotOpt['title']
    channelstr = '' if channel is None else ', ch. %d' % channel[0]
    titlestr = '%s %s%s\n Mean Total Impact (J/g)' % (plotOpt['center_name'], platform, channelstr)
    plt.title('%s' % (titlestr), fontsize=18)

    if savefig:
        fname = 'SummaryMap-%s-%s' % (center, platform)
        lutils.savefigure(fname=fname, format='pdf')
        plt.close('all')
    else:
        plt.show()


if __name__ == '__main__':
    main()
