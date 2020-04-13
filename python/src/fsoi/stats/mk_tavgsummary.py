"""
mk_tavgsummary.py - Compute time-average statistics and dump to a pkl file
"""

import os
import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import fsoi.stats.lib_utils as lutils
import fsoi.stats.lib_obimpact as loi


def main():
    """

    :return:
    """
    parser = ArgumentParser(description='Create time-average data given bulk statistics',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c', '--center', help='originating center', type=str, required=True,
                        choices=['EMC', 'GMAO', 'NRL', 'JMA_adj', 'JMA_ens', 'MET'])
    parser.add_argument('-r', '--rootdir', help='root path to directory', type=str,
                        default='/scratch3/NCEPDEV/stmp2/Rahul.Mahajan/test/Thomas.Auligne/FSOI',
                        required=False)

    args = parser.parse_args()

    rootdir = args.rootdir
    center = args.center

    fname = '%s/work/%s/bulk_stats.h5' % (rootdir, center)
    df = lutils.readHDF(fname, 'df')
    df = loi.accumBulkStats(df)
    platforms = loi.OnePlatform()
    df = loi.groupBulkStats(df, platforms)
    df, df_std = loi.tavg(df, level='PLATFORM')

    fpkl = '%s/work/%s/tavg_stats.pkl' % (rootdir, center)
    if os.path.isfile(fpkl):
        os.remove(fpkl)
    lutils.pickle(fpkl, df)

    sys.exit(0)


if __name__ == '__main__':
    main()
