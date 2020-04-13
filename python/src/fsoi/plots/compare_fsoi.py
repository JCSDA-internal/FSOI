"""
compare_fsoi.py contains functions for FSOI project
Some functions can be used elsewhere
"""

import pandas as pd
import numpy as np
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import fsoi.stats.lib_utils as lib_utils
import fsoi.stats.lib_obimpact as loi
from fsoi.web.request_handler import filter_platforms_from_data
# from bokeh.plotting import figure
# from bokeh.models import Title
# from bokeh.models.sources import ColumnDataSource
# from bokeh.embed import json_item
# from bokeh.io import export_png
import json


def load_centers(root_dir, centers, norm, cycle):
    """
    Load data for specified centers
    :param root_dir: {str} The root directory of the data
    :param centers: {list} The list of centers to load
    :param norm: {str} The norm to load (dry or moist)
    :param cycle: {int} The cycle to load (0, 6, 12, or 18)
    :return: {list<pandas.DataFrame>} The loaded data as a list of data frames
    """
    data_frame_list = []
    for center in centers:

        fpkl = '%s/work/%s/%s/group_stats.pkl' % (root_dir, center, norm)
        df = lib_utils.unpickle(fpkl)
        indx = df.index.get_level_values('DATETIME').hour == -1
        for c in cycle:
            indx = np.ma.logical_or(indx, df.index.get_level_values('DATETIME').hour == c)
        df = df[indx]

        df, df_std = loi.tavg(df, level='PLATFORM')
        df = loi.summarymetrics(df)

        data_frame_list.append(df)

    return data_frame_list


def sort_centers(data_frame_list):
    """
    Sort centers
    :param data_frame_list: {list<pandas.DataFrame>} A list of data frames
    :return: {pandas.DataFrame, list} A sorted data frame and list of platforms included by at least 2 centers
    """
    # count the number of centers that use each platform
    platform_count = {}
    for i in range(len(data_frame_list)):
        platforms_in_center = data_frame_list[i].index.get_level_values('PLATFORM').unique()
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

    df = []
    for i in range(len(data_frame_list)):
        # create a list of platforms to exclude
        exclusion_list = []
        for platform in data_frame_list[i].index.get_level_values('PLATFORM').unique():
            if platform.upper() not in pref:
                exclusion_list.append(platform)

        # exclude the platforms in the list
        data_frame_list[i].drop(exclusion_list, inplace=True)

        # add the data frame to the list of data frames
        df.append(data_frame_list[i])

    return df, pref


def compare_fsoi_main():
    """

    :return:
    """
    parser = ArgumentParser(description='Create and Plot Comparison Observation Impact Statistics',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--rootdir', help='root path to directory', type=str, required=True)
    parser.add_argument('--platform', help='platforms to plot', type=str, default='full', required=False)
    parser.add_argument('--cycle', help='cycle to process', nargs='+', type=int,
                        choices=[0, 6, 12, 18], required=True)
    parser.add_argument('--norm', help='metric norm', type=str, choices=['dry', 'moist', 'both'],
                        required=True)
    parser.add_argument('--savefigure', help='save figures', action='store_true', required=False)
    parser.add_argument('--centers', help='list of centers', type=str, nargs='+',
                        choices=['EMC', 'GMAO', 'NRL', 'JMA_adj', 'JMA_ens', 'MET', 'MeteoFr', 'MERRA2'],
                        required=True)

    args = parser.parse_args()

    rootdir = args.rootdir
    platform_list_csv = args.platform
    cycle = sorted(list(set(args.cycle)))
    norm = args.norm
    savefig = args.savefigure
    centers = args.centers
    palette = loi.getcomparesummarypalette(centers)

    cycle_str = ''.join('%02dZ' % c for c in cycle)

    data_frame_list = load_centers(rootdir, centers, norm, cycle)
    full_df, platforms = sort_centers(data_frame_list)

    for qty in ['TotImp', 'ImpPerOb', 'FracBenObs', 'FracNeuObs', 'FracImp', 'ObCnt']:
        plot_options = loi.getPlotOpt(qty, savefigure=savefig, center=None, cycle=cycle)
        plot_options['figure_name'] = '%s/plots/compare/%s/%s_%s' % \
                                      (rootdir, 'full', plot_options.get('figure_name'), cycle_str)
        tmpdf = []
        for c, center in enumerate(centers):
            tmp = full_df[c][qty]
            tmp.name = center
            index = []
            for single_platform in tmp.index:
                index.append((single_platform.upper()))
            tmp.index = pd.CategoricalIndex(data=index, name='PLATFORM')
            filter_platforms_from_data(tmp, platform_list_csv)
            tmp = tmp.reindex(platforms)
            tmpdf.append(tmp)

        df = pd.concat(tmpdf, axis=1, sort=True)
        platforms.reverse()
        df = df.reindex(platforms)
        filter_platforms_from_data(df, platform_list_csv)

        # matplotlibcomparesummaryplot(df, palette, qty=qty, plotOpt=plot_options)
        bokehcomparesummaryplot(df, palette, qty=qty, plot_options=plot_options)


def matplotlibcomparesummaryplot(df, palette, plot_opt=None):
    """
    Create an inter-center comparison plot with MatPlotLib
    :param df: {pandas.DataFrame} The data to plot
    :param palette: {list} List of hex colors (e.g. #c63c63) to use for each center
    :param plot_opt: {dict} A dictionary of plot options
    :return: None
    """
    from matplotlib import pyplot as plt
    from matplotlib.ticker import ScalarFormatter
    if plot_opt is None:
        plot_opt = {}
    sort_me = df.copy()
    sort_me.fillna(value=0, inplace=True)
    sort_me['SUM'] = 0
    for center in df:
        sort_me['SUM'] += sort_me[center]
    sort_me.sort_values(by='SUM', ascending=plot_opt['sortAscending'], inplace=True, na_position='first')
    sort_me.drop('SUM', 1, inplace=True)
    df = sort_me

    alpha = plot_opt['alpha']
    barcolors = reversed(palette)

    if palette is not None:
        barcolors = palette

    width = 0.9
    df.plot.barh(width=width, stacked=True, color=barcolors, alpha=alpha, edgecolor='k',
                 linewidth=1.25)
    plt.axvline(0., color='k', linestyle='-', linewidth=1.25)

    plt.legend(frameon=False, loc=0)

    ax = plt.gca()

    ax.set_title(plot_opt['title'], fontsize=18)

    xmin, xmax = ax.get_xlim()
    plt.xlim(xmin, xmax)
    ax.set_xlabel(plot_opt['xlabel'], fontsize=14)
    ax.get_xaxis().get_offset_text().set_x(0)
    xfmt = ScalarFormatter()
    xfmt.set_powerlimits((-2, 2))
    ax.xaxis.set_major_formatter(xfmt)

    ax.set_ylabel('', visible=False)
    ax.set_yticklabels(df.index, fontsize=10)

    ax.autoscale(enable=True, axis='y', tight=True)
    ax.grid(False)

    plt.tight_layout()

    if plot_opt['savefigure']:
        lib_utils.savefigure(fname=plot_opt['figure_name'])

    return


def bokehcomparesummaryplot(df, palette, qty='TotImp', plot_options=None):
    """
    Create an inter-center comparison plot with Bokeh
    :param df: {pandas.DataFrame} The data to plot
    :param palette: {list} List of hex colors (e.g. #c63c63) to use for each center
    :param qty: {str} The quantity to plot (e.g. TotImp)
    :param plot_options: {dict} A dictionary of plot options
    :return: None
    """
    from bokeh.plotting import figure
    from bokeh.models import Title
    from bokeh.models.sources import ColumnDataSource
    from bokeh.embed import json_item
    from bokeh.io import export_png
    if plot_options is None:
        plot_options = {}

    sort_me = df.copy()
    sort_me.fillna(value=0, inplace=True)
    sort_me['SUM'] = 0
    centers = []
    for center in df:
        sort_me['SUM'] += sort_me[center]
        centers.append(center)
    sort_me.sort_values(by='SUM', ascending=plot_options['sortAscending'], inplace=True, na_position='first')
    x_range = (sort_me['SUM'].min(), sort_me['SUM'].max())
    sort_me.drop('SUM', 1, inplace=True)
    sort_me['PLATFORMS'] = sort_me.index
    df = sort_me

    # define the tooltips
    tooltips = [
        ('Platform', '@PLATFORMS'),
        ('Center', '$name'),
        ('Value', '@$name'),
        ('Units', plot_options['xlabel'])
    ]
    # create the figure
    plot = figure(
        id='%s,%s' % (plot_options['center'], qty),
        plot_width=800,
        plot_height=800,
        y_range=list(df.index.unique()),
        x_range=x_range,
        tools='pan,hover,wheel_zoom,xwheel_zoom,box_zoom,save,reset',
        toolbar_location='right',
        tooltips=tooltips
    )

    # add the bar plot
    plot.hbar_stack(
        centers,
        y='PLATFORMS',
        height=0.9,
        source=ColumnDataSource(df),
        fill_color=palette,
        legend_label=centers,
        line_color='#000000'
    )
    plot.y_range.range_padding = 0.1

    # add the labels
    plot.xaxis.axis_label = plot_options['xlabel']
    title_lines = plot_options['title'].split('\n')
    title_lines.reverse()
    for line in title_lines:
        plot.add_layout(Title(text=line, text_font_size='1.5em', align='center'), 'above')

    # make the plots interactive
    plot.legend.click_policy = 'hide'

    # write the json object to a file
    with open('%s.json' % plot_options['figure_name'], 'w') as f:
        f.write(json.dumps(json_item(plot)))
        f.close()

    # write the png file
    export_png(plot, '%s.png' % plot_options['figure_name'])

    return


if __name__ == '__main__':
    compare_fsoi_main()
