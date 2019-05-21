from pandas import DataFrame
from fsoi.plots import Plot
from fsoi import log


class SummaryPlot(Plot):
    """
    Create an abstract class to help create plots of type "SummaryPlot"
    """

    def __init__(self, options=None):
        """
        Initialize the object with optional plot options
        :param options: {dict|None} A dictionary used by sub-classes to make plots
        """
        self.df = None
        self.df_std = None

        super(SummaryPlot, self).__init__(options, defaults='summary_plot')
        self.__update_options(options)

    def set_data(self, df, df_std):
        """
        Set the pandas DataFrame that should be plotted
        :param df: {DataFrame} The DataFrame to plot
        :param df_std: {DataFrame} The standard deviation for the DataFrame
        :return: None
        """
        if not isinstance(df, DataFrame):
            log.error('Data must be of type DataFrame: %s' % type(df))
            raise TypeError('Data must be of type DataFrame: %s' % type(df))
        self.df = df

        if not isinstance(df_std, DataFrame):
            log.error('Data must be of type DataFrame: %s' % type(df_std))
            raise TypeError('Data must be of type DataFrame: %s' % type(df_std))
        self.df_std = df_std

    def __update_options(self, options):
        """
        a rather ugly method that updates certain default option values using other option values
        if they have not been overridden by the calling method
        :param options: {dict} Options specified by the calling method
        :return: None
        """
        # update certain option values
        center = self.options['center']
        domain = self.options['domain']
        cycles = self.options['cycles']

        # translate the center abbreviation into a full name
        if not 'center_name' in options:
            self.options['center_name'] = self.center_names[center]

        # create the x-axis label and sort order
        if 'x_axis_label' not in options:
            metric_info = self.metric_defaults[self.options['metric']]
            self.options['x_axis_label'] = '%s %s' % (metric_info['name'], metric_info['units'])
            if 'sort_ascending' not in options:
                self.options['sort_ascending'] = metric_info['sort_ascending']

        # transform a list of cycle hours to a string
        if isinstance(cycles, list):
            cycles = ','.join('%02dZ' % int(c) for c in cycles)
            self.options['cycle_str'] = cycles

        # update the title from the default if not specified
        if 'title' not in options:
            cycle_str = self.options['cycle_str']
            self.options['title'] = self.options['title'] % (center, domain, cycle_str)


class MatplotlibSummaryPlot(SummaryPlot):
    """
    This class will use matplotlib to create a plot from a DataFrame
    """

    def __init__(self, options=None):
        """
        Initialize the object with the optional plot options
        :param options: {dict|None} A dictionary used to make plots
        """
        super(MatplotlibSummaryPlot, self).__init__(options)

    def create_plot(self, df=None, df_std=None, output_path=None):
        """
        Create a summary plot with the provided or already set data, path, and options
        :param df: {DataFrame|None} The data, which may have already been set with set_data
        :param output_path: {str} Full path to output file, which may have already been set
        :return: {bool} True if plot was created successfully
        """
        from matplotlib import pyplot as mpl_pyplot
        import numpy
        from matplotlib import cm as mpl_color_map
        from matplotlib import colors as mpl_colors
        from matplotlib.ticker import ScalarFormatter

        # set data on this object if it was provided
        if df is not None and df_std is not None:
            self.set_data(df, df_std)
        df = self.df
        df_std = self.df_std

        # set the output path on this object if it was provided
        if output_path is not None:
            self.set_output_file(output_path)

        # apply options to the data frame
        self.__apply_options()

        # extract options into local variables
        alpha = self.options['alpha']
        title = self.options['title']
        width = self.options['width']
        center = self.options['center']
        metric = self.options['metric']
        color_min = self.options['color_min']
        color_max = self.options['color_max']
        log_scale = self.options['log_scale']
        x_axis_label = self.options['x_axis_label']
        ob_count_name = self.options['ob_count_name']
        color_map_name = self.options['color_map_name']
        color_bar_label = self.options['color_bar_label']
        error_bar_color = self.options['error_bar_color']
        title_font_size = self.options['title_font_size']
        axis_label_font_size = self.options['axis_label_font_size']
        tick_labels_font_size = self.options['tick_labels_font_size']

        # get the color map from matplotlib
        color_map = mpl_color_map.get_cmap(color_map_name)
        bar_colors = self.__get_bar_colors(df[ob_count_name], log_scale, color_max, color_min, color_map)
        norm = mpl_colors.LogNorm() if log_scale else mpl_colors.Normalize()

        # clear the current figure
        mpl_pyplot.clf()

        # create the color bar, which requires creating a dummy plot
        x = numpy.array([0, 1, 2, 3, 4, 5, 6])
        y = numpy.array([1e0, 1e1, 1e2, 1e3, 1e4, 1e5, 1e6])
        dummy_plot = mpl_pyplot.scatter(x, y, c=y, alpha=alpha, cmap=color_map, norm=norm, vmin=color_min, vmax=color_max)
        color_bar = mpl_pyplot.colorbar(dummy_plot, aspect=30, ticks=y, format='%.0e', alpha=alpha)

        # create the horizontal bar plot
        if metric == 'TotImp':
            # TotImp has error bars to show the standard deviation values
            df[metric].plot.barh(width=width,
                                 color=bar_colors,
                                 alpha=alpha,
                                 edgecolor='k',
                                 linewidth=1.25,
                                 xerr=df_std[metric],
                                 capsize=2.0,
                                 ecolor=error_bar_color)
        else:
            # Other metrics do not have error bars with standard deviation values
            df[metric].plot.barh(width=width,
                                 color=bar_colors,
                                 alpha=alpha,
                                 edgecolor='k',
                                 linewidth=1.25)

        # FracBenObs has a vertical line drawn at 50%
        if metric in ['FracBenObs']:
            mpl_pyplot.axvline(50., color='k', linestyle='--', linewidth=1.25)

        # get a reference the plot axis
        axes = mpl_pyplot.gca()

        # set title
        axes.set_title(title, fontsize=title_font_size)

        # calculate the min and max values in the data set
        df = df[metric]
        xmin = df.min()
        xmax = df.max()
        dx = xmax - xmin
        xmin = xmin - 0.1 * dx
        xmax = xmax + 0.1 * dx
        mpl_pyplot.xlim(xmin, xmax)

        # set x-axis labels and formatting
        axes.set_xlabel(x_axis_label, fontsize=axis_label_font_size)
        axes.get_xaxis().get_offset_text().set_x(0)
        xfmt = ScalarFormatter()
        xfmt.set_powerlimits((-3, 3))
        axes.xaxis.set_major_formatter(xfmt)

        # set y-axis labels and formatting
        axes.set_ylabel('', visible=False)
        axes.set_yticklabels(df.index, fontsize=tick_labels_font_size)
        axes.autoscale(enable=True, axis='y', tight=True)
        axes.grid(False)

        # color bar properties
        color_bar.solids.set_edgecolor('face')
        color_bar.outline.set_visible(True)
        color_bar.outline.set_linewidth(1.25)
        color_bar.ax.tick_params(labelsize=12)
        color_bar.set_label(color_bar_label,
                       rotation=90, fontsize=14, labelpad=20)
        color_bar_y_ticks = mpl_pyplot.getp(color_bar.ax.axes, property='yticklines')
        mpl_pyplot.setp(color_bar_y_ticks, visible=True, alpha=alpha)

        # automatically adjust subplot parameters to give specified padding
        mpl_pyplot.tight_layout()

        # save the figure to a file
        file_name = self.output_file % (center, metric)
        saved = self.__save_figure(mpl_pyplot, file_name=file_name)

        # return a value to indicate success or failure
        if not saved:
            log.error('Error saving summary plot with matplotlib: %s' % file_name)
        return saved

    def __save_figure(self, mpl_pyplot, file_name):
        """
        Save the plot to a file
        :param mpl_pyplot:
        :param file_name:
        :return:
        """
        dpi = self.options['dpi']
        orientation = self.options['orientation']
        if 'png' in format:
            mpl_pyplot.savefig('%s.png' % file_name,
                               format='png', dpi=1 * dpi,
                               orientation=orientation)
        if 'eps' in format:
            mpl_pyplot.savefig('%s.eps' % file_name,
                               format='eps', dpi=2 * dpi,
                               orientation=orientation)
        if 'pdf' in format:
            mpl_pyplot.savefig('%s.pdf' % file_name,
                               format='pdf', dpi=2 * dpi,
                               orientation=orientation)

        return

    def __apply_options(self):
        """
        Apply options to the data frame
        :return: None
        """
        import numpy

        # pull out options into local variables
        metric = self.options['metric']
        finite = self.options['finite']
        platform = self.options['platform']
        sort_ascending = self.options['sort_ascending']

        # apply the options
        if finite:
            self.df = self.df[numpy.isfinite(self.df[metric])]

        if platform:
            self.df.sort_index(ascending=False, inplace=True)
        else:
            self.df.sort_values(by=metric, ascending=sort_ascending, inplace=True, na_position='first')

    def __get_bar_colors(self, data, log_scale, cmax, cmin, cmap):
        """

        :param data:
        :param log_scale:
        :param cmax:
        :param cmin:
        :param cmap:
        :return:
        """
        from numpy import log10, int

        log_min = log10(cmin)
        log_max = log10(cmax)
        barcolors = []
        for count in data:
            if count <= cmin:
                cindex = 0
            elif count >= cmax:
                cindex = cmap.N - 1
            else:
                if log_scale:  # linear in log-space
                    log_count = log10(count)
                    cindex = (log_count - log_min) / (log_max - log_min) * (cmap.N - 1)
                else:
                    cindex = (count - cmin) / (cmax - cmin) * (cmap.N - 1)
            cindex = int(cindex)
            barcolors.append(cmap(cindex))

        return barcolors
