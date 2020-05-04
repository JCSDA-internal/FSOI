"""
compare_fsoi.py contains functions for FSOI project
Some functions can be used elsewhere
"""

from fsoi.stats import lib_utils
import json


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
    export_png(plot, filename='%s.png' % plot_options['figure_name'])

    return
