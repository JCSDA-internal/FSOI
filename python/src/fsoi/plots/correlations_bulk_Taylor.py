"""
Make Taylor Diagrams of correlations in bulk mode
"""

import sys
import pandas as pd
import fsoi.stats.lib_utils as lutils
import fsoi.stats.lib_obimpact as loi
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from matplotlib import pyplot as plt
from fsoi.stats.TaylorDiagram import TaylorDiagram


def read_center_bulk(rootdir, center, norm, platform, cycle, obtype, channel):
    """
    Read data for a center
    :param rootdir:
    :param center:
    :param norm:
    :param platform:
    :param cycle:
    :param obtype:
    :param channel:
    :return:
    """
    fname = '%s/work/%s/%s/%s.h5' % (rootdir, center, norm, platform.lower())
    tmp = lutils.readHDF(fname, 'df')
    tmp = loi.select(tmp, cycles=cycle, obtypes=obtype, channels=channel)
    tmp.reset_index(inplace=True)
    tmp = tmp.groupby(['DATETIME'])[['TotImp']].agg('sum')
    tmp.columns = [center]
    return tmp


def compute_std_corr_bulk(df):
    """
    Compute the standard deviation and correlation from dictionary of dataframe
    :param df:
    :return:
    """
    df2 = pd.concat(df, axis=1)
    df2.columns = df2.columns.levels[0]
    df_stdv = df2.std()
    df_corr = df2.corr()

    return df_stdv, df_corr


def compute_std_corr_bulk_brute_force(df, centers):
    """
    Compute the standard deviation and correlation from dictionary of dataframe
    :param df:
    :param centers:
    :return:
    """
    ref_center = centers[0]

    stdv = {}
    corr = {}
    for center in centers:

        stdv[center] = df[center].std()

        if center == ref_center:
            corr[center] = stdv[center] / stdv[center]
        else:
            r1 = df[ref_center].join(df[center])
            corr[center] = r1.corr()[::2][center]

    df_stdv = pd.concat(stdv).reset_index().drop('level_1', axis=1)
    df_stdv.columns = ['CENTERS', 'STDDEV']
    df_stdv = df_stdv.pivot_table(values='STDDEV', index='CENTERS')

    df_corr = pd.concat(corr).reset_index().drop('level_1', axis=1)
    df_corr.columns = ['CENTERS', 'CORRELATION']
    df_corr = df_corr.pivot_table(values='CORRELATION', index='CENTERS')

    return df_stdv, df_corr


def plot_taylor(ref_center, stdv, corr, fig=None, full=False, norm=True, title=None, colors=None,
                center_names=None):
    """
    Plot Taylor diagram
    :param ref_center:
    :param stdv:
    :param corr:
    :param fig:
    :param full:
    :param norm:
    :param title:
    :param colors:
    :param center_names:
    :return:
    """

    if colors == None: colors = lutils.discrete_colors(len(center_names) - 1)
    centers = corr.columns.get_values()
    if center_names == None:
        center_names = {}
        for c, center in enumerate(centers):
            center_names[center] = centers[c]

    if fig == None: fig = plt.figure()

    refstd = stdv[ref_center]

    dia = TaylorDiagram(refstd, fig=fig, rect=111, label=center_names[ref_center], norm=norm,
                        full=full)

    corr = corr[ref_center]

    for center in centers:

        if center == ref_center: continue

        std = stdv[center]
        cor = corr[center]

        col = colors[center]
        lab = center_names[center]

        # Add samples to Taylor diagram
        dia.add_sample(std, cor, marker='s', ms=10, mec=col, ls='', c=col, label=lab, alpha=0.7)

    # Add RMS contours, and label them
    contours = dia.add_contours(colors='0.5')
    plt.clabel(contours, inline=1, fontsize=10)

    # Add a figure legend
    fig.legend(dia.samplePoints,
               [p.get_label() for p in dia.samplePoints],
               numpoints=1, prop=dict(size='small'), loc='upper right')

    fig.suptitle(title, fontsize=14, fontweight='bold')

    return fig


def main():
    """
    Main
    :return:
    """
    parser = ArgumentParser(
        description='Create and Plot Observation Impact Correlation Taylor Diagrams',
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--rootdir', help='root path to directory', type=str,
                        default='/scratch3/NCEPDEV/stmp2/Rahul.Mahajan/test/Thomas.Auligne/FSOI',
                        required=False)
    parser.add_argument('--norm', help='metric norm', type=str, default='dry',
                        choices=['dry', 'moist'], required=False)
    parser.add_argument('--centers', help='originating centers', nargs='+', type=str,
                        choices=['GMAO', 'NRL', 'MET', 'MeteoFr', 'JMA_adj', 'JMA_ens', 'EMC'],
                        required=True)
    parser.add_argument('--cycle', help='cycle to process', nargs='+', type=int, default=None,
                        choices=[0, 6, 12, 18], required=False)
    parser.add_argument('--platform', help='platform to plot', type=str, required=True)
    parser.add_argument('--obtype', help='observation types to include', nargs='+', type=str,
                        default=None, required=False)
    parser.add_argument('--channel', help='channel to process', nargs='+', type=int, default=None,
                        required=False)
    parser.add_argument('--savefigure', help='save figures', action='store_true', required=False)

    args = parser.parse_args()

    rootdir = args.rootdir
    norm = args.norm
    centers = args.centers
    cycle = [0, 6, 12, 18] if args.cycle is None else sorted(list(set(args.cycle)))
    platform = args.platform
    obtype = args.obtype
    channel = args.channel
    savefig = args.savefigure

    cyclestr = ' '.join('%02dZ' % c for c in cycle)
    channelstr = 'all' if channel is None else ', '.join('%d' % c for c in channel)

    print('cycles to process: %s' % cyclestr)
    print('channels to process: %s' % channelstr)

    fsoi = loi.FSOI()

    df = {}
    for center in centers:
        df[center] = read_center_bulk(rootdir, center, norm, platform, cycle, obtype, channel)

    df_stdv, df_corr = compute_std_corr_bulk(df)

    titlestr = '%s' % (platform)

    for center in centers:

        fig = plot_taylor(center, df_stdv, df_corr, title=titlestr, colors=fsoi.center_color,
                          center_names=fsoi.center_name)

        if savefig:
            fname = 'Taylor-%s-%s' % (center, platform)
            lutils.savefigure(fname=fname, format='pdf', fh=fig)

    plt.close('all') if savefig else plt.show()

    sys.exit(0)

if __name__ == '__main__':
    main()
