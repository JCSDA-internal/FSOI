"""
summary_fsoi.py - create a summary figure of all platforms
"""

import os
import json
import pandas
import numpy
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter as ArgumentHelp
import fsoi.stats.lib_utils as lib_utils
import fsoi.stats.lib_obimpact as loi
from fsoi import log


def summary_fsoi_main():
    """

    :return:
    """
    centers = ['EMC', 'GMAO', 'NRL', 'JMA_adj', 'JMA_ens', 'MET', 'MeteoFr']
    cycles = [0, 6, 12, 18]
    parser = ArgumentParser(description='Create and Plot Observation Impacts Statistics', formatter_class=ArgumentHelp)
    parser.add_argument('--center', help='originating center', type=str, required=True, choices=centers)
    parser.add_argument('--norm', help='metric norm', type=str, default='dry', choices=['dry', 'moist'], required=False)
    parser.add_argument('--rootdir', help='root path to directory', type=str, required=False)
    parser.add_argument('--platform', help='platform to plot', type=str, default='', required=False)
    parser.add_argument('--savefigure', help='save figures', action='store_true', required=False)
    parser.add_argument('--exclude', help='exclude platforms', type=str, nargs='+', required=False)
    parser.add_argument('--cycle', help='cycle hour', nargs='+', type=int, default=[0], choices=cycles, required=False)

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
    fpkl = '%s/work/%s/%s/%s_group_stats.pkl' % (rootdir, center, norm, center)

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


def matplotlibsummaryplot(df, qty='TotImp', plot_options=None, std=None):
    """
    Create a summary plot with matplotlib
    :param df:
    :param qty:
    :param plot_options:
    :param std:
    :return:
    """
    from matplotlib import pyplot as plt
    from matplotlib import cm
    import matplotlib.colors
    from matplotlib.ticker import ScalarFormatter
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
    from bokeh.plotting import figure
    from bokeh.models import Title, ColorBar, LinearColorMapper, BasicTicker, Span, Whisker
    from bokeh.models.sources import ColumnDataSource
    from bokeh.embed import json_item
    from bokeh.io import export_png
    import bokeh.palettes
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
    # pylint wrongly believes Module 'bokeh.palettes' has no 'brewer' member (no-member)
    # pylint: disable=E1101
    palette_blues = bokeh.palettes.brewer[plot_options['cmap']][256]
    palette_blues.reverse()
    color_map = LinearColorMapper(palette=palette_blues, low=cmin, high=cmax)

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
    if qty == 'TotImp':
        tooltips.append(('Sigma', '@std'))

    # create the figure
    x_range = (min(df[qty].min(), 0), max(df[qty].max(), 0))

    plot = figure(
        id='%s,%s' % (plot_options['center'], qty),
        plot_width=800,
        plot_height=800,
        y_range=list(df1.index.unique()),
        x_range=x_range,
        tools='pan,hover,wheel_zoom,box_zoom,save,reset',
        toolbar_location='right',
        tooltips=tooltips
    )

    # add the bar plot
    source = ColumnDataSource(df1)
    plot.hbar(source=source, right=qty, y='PLATFORMS', height=0.9, line_color='#000000', fill_color='colors')

    # maybe add error bars
    if qty == 'TotImp':
        df1[qty+'_upper'] = df1[qty] + df1['std']
        df1[qty+'_lower'] = df1[qty] - df1['std']
        errbar = ColumnDataSource(df1)
        plot.add_layout(Whisker(source=errbar, dimension='width', base='PLATFORMS',
                                upper=qty+'_upper', lower=qty+'_lower', level='overlay',
                                line_color='#f1631f', line_width=3, line_cap='square',
                                lower_head=None, upper_head=None))

    # maybe add a vertical reference line
    if qty in ['FracBenObs', 'FracBenNeuObs']:
        plot.add_layout(Span(location=50.,
                             dimension='height', line_color='black',
                             line_dash='dashed', line_width=1))

    # add a vertical zero line
    plot.add_layout(Span(location=0.,
                         dimension='height', line_color='black',
                         line_dash='solid', line_width=1))

    # add the labels
    plot.xaxis.axis_label = plot_options['xlabel']
    title_lines = plot_options['title'].split('\n')
    title_lines.reverse()
    for line in title_lines:
        plot.add_layout(Title(text=line, text_font_size='1.5em', align='center'), 'above')

    # legend
    # pylint wrongly believes Module 'bokeh.palettes' has no 'brewer' member (no-member)
    # pylint: disable=E1101
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
        export_png(plot, filename='%s.png' % plot_options['figure_name'])
    except ValueError as ve:
        print(ve)


def bokehsummarytseriesplot(df, qty='TotImp', plot_options=None):
    """
    Create a summary time series plot with Bokeh libraries
    :param df: {pandas.DataFrame} The data to plot
    :param qty: {str} The quantity to plot (e.g. TotImp)
    :param plot_options: {dict} A dictionary of plot options
    :return: None
    """
    from bokeh.plotting import figure
    from bokeh.models import Title, HoverTool, Legend, Span
    from bokeh.models.sources import ColumnDataSource
    from bokeh.embed import json_item
    from bokeh.io import export_png
    import bokeh.palettes
    # create the data source
    if plot_options is None:
        plot_options = {}

    if plot_options['finite']:
        df = df[numpy.isfinite(df[qty])]

    df1 = df[qty].reset_index()
    df1.drop('level_0', axis=1, inplace=True)

    # define the tooltips
    tooltips = [
        ('Platform', '@PLATFORM'),
        ('Value', '@%s' % qty),
        ('Units', plot_options['xlabel']),
        ('Date', '@DATETIME{%Y-%m-%d %H:%M:%S}'),
    ]

    # add hover tool
    ht = HoverTool(tooltips=tooltips, formatters={'DATETIME': 'datetime'})

    # create the figure
    if len(df1['DATETIME'].unique()) > 1:
        x_range = (df1['DATETIME'].min(), df1['DATETIME'].max())
    else:
        x_range = None
    y_range = (df1[qty].min(), df1[qty].max())

    plot = figure(
        id='%s,%s' % (plot_options['center'], qty),
        plot_width=800,
        plot_height=800,
        x_axis_type='datetime',
        x_axis_label='Date',
        y_axis_label=plot_options['xlabel'],
        y_range=y_range,
        x_range=x_range,
        tools=['pan,wheel_zoom,box_zoom,save,reset',ht],
        toolbar_location='right',
        tooltips=tooltips
    )

    platforms = list(df1['PLATFORM'].unique())
    # pylint wrongly believes Module 'bokeh.palettes' has no 'viridis' member (no-member)
    # pylint: disable=E1101
    colors = bokeh.palettes.viridis(len(platforms))
    p_dict = dict()
    for platform, color in zip(platforms, colors):
        source = ColumnDataSource(df1[df1['PLATFORM'] == platform])
        p_dict[platform] = plot.line('DATETIME', qty, source=source, line_width=2, color=color)

    # legend
    legend = Legend(items=[(x, [p_dict[x]]) for x in p_dict],
                    border_line_color=None, margin=0, spacing=0, padding=0)
    plot.add_layout(legend, 'right')

    # maybe add a horizontal reference line
    if qty in ['FracBenObs', 'FracBenNeuObs']:
        plot.add_layout(Span(location=50.,
                             dimension='width', line_color='black',
                             line_dash='dashed', line_width=1))

    # add a horizontal zero line
    plot.add_layout(Span(location=0.,
                         dimension='width', line_color='black',
                         line_dash='solid', line_width=1))

    # add the labels
    title_lines = plot_options['title'].split('\n')
    title_lines[-1] += ' - Moving Average of %s Cycles' % plot_options['mavg']
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
    try:
        export_png(plot, filename='%s.png' % plot_options['figure_name'])
    except ValueError as ve:
        print(ve)


if __name__ == '__main__':
    summary_fsoi_main()
