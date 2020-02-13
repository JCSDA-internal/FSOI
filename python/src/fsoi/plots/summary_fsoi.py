"""
summary_fsoi.py - create a summary figure of all platforms
"""

import os
import json
import pandas
import numpy
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from matplotlib import pyplot as plt
import fsoi.stats.lib_utils as lib_utils
import fsoi.stats.lib_obimpact as loi
from fsoi import log
import math
from matplotlib import cm
import matplotlib.colors
from matplotlib.ticker import ScalarFormatter
from bokeh.plotting import figure
from bokeh.models import Title, ColorBar, LinearColorMapper, BasicTicker
from bokeh.models.sources import ColumnDataSource
from bokeh.embed import json_item
from bokeh.io import export_png
import bokeh.palettes


def summary_fsoi_main():
    """

    :return:
    """
    parser = ArgumentParser(description='Create and Plot Observation Impacts Statistics',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--center', help='originating center', type=str, required=True,
                        choices=['EMC', 'GMAO', 'NRL', 'JMA_adj', 'JMA_ens', 'MET', 'MeteoFr'])
    parser.add_argument('--norm', help='metric norm', type=str, default='dry',
                        choices=['dry', 'moist'], required=False)
    parser.add_argument('--rootdir', help='root path to directory', type=str,
                        default='/scratch3/NCEPDEV/stmp2/Rahul.Mahajan/test/Thomas.Auligne/FSOI',
                        required=False)
    parser.add_argument('--platform', help='platform to plot', type=str, default='', required=False)
    parser.add_argument('--savefigure', help='save figures', action='store_true', required=False)
    parser.add_argument('--exclude', help='exclude platforms', type=str, nargs='+', required=False)
    parser.add_argument('--cycle', help='cycle to process', nargs='+', type=int, default=[0],
                        choices=[0, 6, 12, 18], required=False)

    args = parser.parse_args()

    rootdir = args.rootdir
    center = args.center
    norm = args.norm
    platform = args.platform
    exclude = args.exclude
    savefig = args.savefigure
    cycle = sorted(list(set(args.cycle)))

    cyclestr = ''.join('%02dZ' % c for c in cycle)

    fname = '%s/work/%s/%s/bulk_stats.h5' % (rootdir, center, norm)
    fpkl = '%s/work/%s/%s/group_stats.pkl' % (rootdir, center, norm)

    if os.path.isfile(fpkl):
        overwrite = input('%s exists, OVERWRITE [y/N]: ' % fpkl)
    else:
        overwrite = 'Y'

    if overwrite.upper() in ['Y', 'YES']:
        df = lib_utils.readHDF(fname, 'df')
        df = loi.accumBulkStats(df)
        platforms = loi.Platforms(center)
        df = loi.groupBulkStats(df, platforms)
        if os.path.isfile(fpkl):
            print('OVERWRITING %s' % fpkl)
            os.remove(fpkl)
        lib_utils.pickle(fpkl, df)
    else:
        df = pandas.read_pickle(fpkl)

    # Filter by cycle
    print('extracting data for cycle %s' % ' '.join('%02dZ' % c for c in cycle))
    index = df.index.get_level_values('DATETIME').hour == -1
    for c in cycle:
        index = numpy.ma.logical_or(index, df.index.get_level_values('DATETIME').hour == c)
    df = df[index]

    # Do time-averaging on the data
    df, df_std = loi.tavg(df, level='PLATFORM')

    if exclude is not None:
        if platform:
            print('Excluding the following platforms:')
            exclude = map(int, exclude)
        else:
            print('Excluding the following platforms:')
            if 'reference' in exclude:
                pref = loi.RefPlatform('full')
                pcenter = df.index.get_level_values('PLATFORM').unique()
                exclude = list(set(pcenter) - set(pref))
        print(", ".join('%s' % x for x in exclude))
        df.drop(exclude, inplace=True)
        df_std.drop(exclude, inplace=True)

    df = loi.summarymetrics(df)

    for qty in ['TotImp', 'ImpPerOb', 'FracBenObs', 'FracNeuObs', 'FracImp', 'ObCnt']:
        try:
            plot_options = loi.getPlotOpt(
                qty,
                cycle=cycle,
                center=center,
                savefigure=savefig,
                platform=platform,
                domain='Global'
            )
            plot_options['figure_name'] = '%s/plots/summary/%s/%s_%s' % (
                rootdir, center, plot_options.get('figure_name'), cyclestr)
            matplotlibsummaryplot(df, qty=qty, plot_options=plot_options, std=df_std)
        except Exception as e:
            log.error('Failed to create summary plot for %s' % qty, e)

    if savefig:
        plt.close('all')
    else:
        plt.show()


def matplotlibsummaryplot(df, qty='TotImp', plot_options=None, std=None):
    """
    Create a summary plot with matplotlib
    :param df:
    :param qty:
    :param plot_options:
    :param std:
    :return:
    """
    if plot_options is None:
        plot_options = {}

    if plot_options['finite']:
        df = df[numpy.isfinite(df[qty])]

    sort_by = qty if qty != 'FracBenNeuObs' else 'FracBenObs'
    df.sort_values(by=sort_by, ascending=plot_options['sortAscending'], inplace=True, na_position='first')

    fig = plt.figure(figsize=(10, 8))
    fig.add_subplot(111, facecolor='w')

    alpha = plot_options['alpha']
    logscale = plot_options['logscale']
    cmax = plot_options['cmax']
    cmin = plot_options['cmin']
    cmap = cm.get_cmap(plot_options['cmap'])

    barcolors = loi.getbarcolors(df['ObCnt'], logscale, cmax, cmin, cmap)
    norm = matplotlib.colors.LogNorm() if logscale else matplotlib.colors.Normalize()

    # dummy plot for keeping colorbar on a bar plot
    x = numpy.array([0, 1, 2, 3, 4, 5, 6])
    y = numpy.array([1e0, 1e1, 1e2, 1e3, 1e4, 1e5, 1e6])
    tmp = plt.scatter(x, y, c=y, alpha=alpha, cmap=cmap, norm=norm, vmin=cmin, vmax=cmax)
    plt.clf()
    cbar = plt.colorbar(tmp, aspect=30, ticks=y, format='%.0e', alpha=alpha)

    width = 1.0
    bax = None
    if qty == 'FracBenNeuObs':
        left = df['FracBenObs'].values
        df['FracBenObs'].plot.barh(width=width, color=barcolors, alpha=alpha, edgecolor='k',
                                   linewidth=1.25)
        bax = df['FracNeuObs'].plot.barh(left=left, width=width, color=barcolors, alpha=alpha,
                                         edgecolor='k', linewidth=1.25)
    elif qty == 'TotImp':
        df[qty].plot.barh(width=width, color=barcolors, alpha=alpha, edgecolor='k', linewidth=1.25,
                          xerr=std[qty], capsize=2.0, ecolor='#FF6103')
    else:
        df[qty].plot.barh(width=width, color=barcolors, alpha=alpha, edgecolor='k', linewidth=1.25)

    # For FracBenObs/FracBenNeuObs, draw a vline at 50% and hatch for FracBenNeuObs
    if qty in ['FracBenObs', 'FracBenNeuObs']:
        plt.axvline(50., color='k', linestyle='--', linewidth=1.25)
        if qty in ['FracBenNeuObs']:
            if bax is not None:
                bars = bax.patches
                for b, bar in enumerate(bars):
                    if b >= len(bars) / 2:
                        if numpy.mod(b, 2):
                            bar.set_hatch('//')
                        else:
                            bar.set_hatch('\\\\')

    # Get a handle on the plot axis
    ax = plt.gca()

    # Set title
    ax.set_title(plot_options['title'], fontsize=18)

    # Set x-limits on the plot
    if qty in ['FracBenNeuObs']:
        xmin, xmax = df['FracBenObs'].min(), (df['FracBenObs'] + df['FracNeuObs']).max()
    else:
        df = df[qty]
        xmin, xmax = df.min(), df.max()
    dx = xmax - xmin
    xmin, xmax = xmin - 0.1 * dx, xmax + 0.1 * dx
    plt.xlim(xmin, xmax)

    # xticks = _np.arange(-3,0.1,0.5)
    # ax.set_xticks(xticks)
    # x.set_xticklabels(_np.ndarray.tolist(xticks),fontsize=12)
    ax.set_xlabel(plot_options['xlabel'], fontsize=14)
    ax.get_xaxis().get_offset_text().set_x(0)
    xfmt = ScalarFormatter()
    xfmt.set_powerlimits((-3, 3))
    ax.xaxis.set_major_formatter(xfmt)

    ax.set_ylabel('', visible=False)
    ax.set_yticklabels(df.index, fontsize=12)

    ax.autoscale(enable=True, axis='y', tight=True)
    ax.grid(False)

    # Colorbar properties
    cbar.solids.set_edgecolor("face")
    cbar.outline.set_visible(True)
    cbar.outline.set_linewidth(1.25)
    cbar.ax.tick_params(labelsize=12)

    cbar.set_label('Observation Count per Analysis',
                   rotation=90, fontsize=14, labelpad=20)
    cbarytks = plt.getp(cbar.ax.axes, 'yticklines')
    plt.setp(cbarytks, visible=True, alpha=alpha)

    plt.tight_layout()

    if plot_options['savefigure']:
        lib_utils.savefigure(fname=plot_options['figure_name'])

    return fig


def bokehsummaryplot(df, qty='TotImp', plot_options=None, std=None):
    """
    Create a summary plot with Bokeh libraries
    :param df: {pandas.DataFrame} The data to plot
    :param qty: {str} The quantity to plot (e.g. TotImp)
    :param plot_options: {dict} A dictionary of plot options
    :param std: {pandas.DataFrame} (optional) A data frame containing standard deviation values for df
    :return: None
    """
    # create the data source
    if plot_options is None:
        plot_options = {}

    if plot_options['finite']:
        df = df[numpy.isfinite(df[qty])]
    sort_by = qty if qty != 'FracBenNeuObs' else 'FracBenObs'
    df1 = pandas.DataFrame(index=df.index)
    df1[qty] = df[qty]
    df1['PLATFORMS'] = df1.index
    if std is not None and qty in std:
        df1['std'] = std[qty]
    df1.sort_values(by=sort_by, ascending=plot_options['sortAscending'], inplace=True, na_position='first')

    # extract the plot options
    logscale = plot_options['logscale']
    cmax = df['ObCnt'].max()  # plot_options['cmax']
    cmin = df['ObCnt'].min()  # plot_options['cmin']
    if cmax == cmin:
        cmin = 0
        if cmax == 0:
            cmax = 1
    color_map = cm.get_cmap(plot_options['cmap'])

    # create the list of bar colors
    df1['ObCnt'] = df['ObCnt']
    color_bars = loi.getbarcolors(df1['ObCnt'], logscale, cmax, cmin, color_map)
    df1['colors'] = ['#%02x%02x%02x' % (int(c[0] * 255), int(c[1] * 255), int(c[2] * 255)) for c in color_bars]

    # define the tooltips
    tooltips = [
        ('Platform', '@PLATFORMS'),
        ('Value', '@%s' % qty),
        ('Units', plot_options['xlabel']),
        ('Obs Count', '@ObCnt')
    ]
    if std is not None:
        tooltips.append(('Sigma', '@std'))

    # create the figure
    x_range = (min(df[qty].min(), 0), max(df[qty].max(), 0))

    plot = figure(
        id='%s,%s' % (plot_options['center'], qty),
        plot_width=800,
        plot_height=800,
        y_range=list(df1.index.unique()),
        x_range=x_range,
        tools='pan,hover,wheel_zoom,xwheel_zoom,box_zoom,save,reset',
        toolbar_location='right',
        tooltips=tooltips
    )

    # add the bar plot
    source = ColumnDataSource(df1)
    plot.hbar(source=source, right=qty, y='PLATFORMS', height=0.9, line_color='#000000', fill_color='colors')

    # maybe add error bars
    if qty == 'TotImp':
        xs = []
        ys = []
        for i in range(len(df1.index)):
            if not math.isnan(df1['std'][i]):
                xs.append([df1[qty][i] - df1['std'][i], df1[qty][i] + df1['std'][i]])
                ys.append([df1.index[i], df1.index[i]])
        plot.multi_line(xs=xs, ys=ys, color='#f1631f', line_width=3, line_cap='square')

    # add the labels
    plot.xaxis.axis_label = plot_options['xlabel']
    title_lines = plot_options['title'].split('\n')
    title_lines.reverse()
    for line in title_lines:
        plot.add_layout(Title(text=line, text_font_size='1.5em', align='center'), 'above')

    # legend
    palette_blues = bokeh.palettes.brewer[plot_options['cmap']][256]
    palette_blues.reverse()
    color_map = LinearColorMapper(palette=palette_blues, low=cmin, high=cmax)
    color_bar = ColorBar(
        color_mapper=color_map,
        ticker=BasicTicker(),
        label_standoff=12,
        border_line_color=None,
        location=(20, 0)
    )
    plot.add_layout(color_bar, 'right')

    # write the json object to a file
    with open('%s.json' % plot_options['figure_name'], 'w') as f:
        f.write(json.dumps(json_item(plot)))
        f.close()

    # write the png file
    try:
        export_png(plot, '%s.png' % plot_options['figure_name'])
    except ValueError as ve:
        print(ve)


if __name__ == '__main__':
    summary_fsoi_main()
