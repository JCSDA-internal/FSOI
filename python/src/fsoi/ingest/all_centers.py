"""
A proof-of-concept to show how to process data to make IOS web application faster
"""

import os
import pandas as pd
from fsoi.stats.lib_utils import readHDF
from fsoi.stats.lib_utils import writeHDF
from fsoi.stats.lib_obimpact import BulkStats
from fsoi.stats.lib_obimpact import accumBulkStats
from fsoi.stats.lib_obimpact import Platforms
from fsoi.stats.lib_obimpact import groupBulkStats
from fsoi.stats.lib_obimpact import tavg
from fsoi.stats.lib_obimpact import summaryplot
from fsoi.stats.lib_obimpact import summarymetrics
from fsoi.stats.lib_obimpact import getPlotOpt


def main():
    """
    Test the new functions
    """
    # process_data()
    create_plot()


def process_data():
    """
    Process all data in /Volumes/JCSDA/data/GMAO 2015-02-15 to 2015-02-21
    :return: None
    """
    for cycle in [0, 6, 12, 18]:
        for date in range(15, 22):
            path = '/Volumes/JCSDA/data/GMAO'
            file = 'GMAO.dry.201502%02d%02d.h5' % (date, cycle)
            if not os.path.exists('%s/%s' % (path, file)):
                print('Not found: %s' % file)
                continue

            df = readHDF('%s/%s' % (path, file), 'df')
            df = BulkStats(df)
            writeHDF('%s/bulk.%s' % (path, file), 'df', df)

            df = accumBulkStats(df)
            writeHDF('%s/accumbulk.%s' % (path, file), 'df', df)

            platforms = Platforms('GMAO')
            df = groupBulkStats(df, platforms)
            writeHDF('%s/groupbulk.%s' % (path, file), 'df', df)


def create_plot():
    """
    Create a plot with the data
    :return: None
    """
    # create a list of files
    files = []
    for cycle in [0]:
        for date in range(26, 27):
            path = '/tmp/work'
            file = 'groupbulk.NRL.dry.201904%02d%02d.h5' % (date, cycle)
            files.append('%s/%s' % (path, file))

    # read all of the files
    ddf = {}
    for (i, file) in enumerate(files):
        ddf[i] = readHDF(file, 'df')

    # concatenate and time-average the data frames
    df, df_std = tavg(pd.concat(ddf, axis=0), 'PLATFORM')
    df = summarymetrics(df)

    # create the plots
    center = 'NRL'
    platform = Platforms(center)
    for qty in ['TotImp', 'ImpPerOb', 'FracBenObs', 'FracNeuObs', 'FracImp', 'ObCnt']:
        try:
            plot_options = getPlotOpt(qty, cycle=[0], center=center, savefigure=True,
                                      platform=platform, domain='Global')
            plot_options['figname'] = '/tmp/work/images/%s' % qty
            summaryplot(df, qty=qty, plotOpt=plot_options, std=df_std)
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()
