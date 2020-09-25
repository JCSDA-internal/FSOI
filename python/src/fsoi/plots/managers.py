import os
import tempfile
import numpy
import pandas
from datetime import datetime
from fsoi import log
from fsoi.data.datastore import ThreadedDataStore
from fsoi.data.s3_datastore import FsoiS3DataStore, S3DataStore
from fsoi.stats import lib_utils, lib_obimpact
from fsoi.plots.summary_fsoi import bokehsummaryplot, matplotlibsummaryplot
from fsoi.plots.compare_fsoi import bokehcomparesummaryplot, matplotlibcomparesummaryplot


class PlotGenerator:
    """
    A class to manage the creation of plots
    """
    def __init__(self):
        """
        Create an object to manage a set of plots
        """
        self.work_dir = None
        self.warns = []
        self.errors = []
        self.plots = []

    def create_plot_set(self):
        """
        Create a chart as a PNG based on the input parameters
        :return: JSON response
        """
        raise RuntimeError('Not implemented')

    def clean_up(self, remove_dir=None):
        """
        Clean up the temporary workspace including plots
        :return: None
        """
        if remove_dir is None:
            remove_dir = self.work_dir

        items = os.listdir(remove_dir)
        for item in items:
            item = '%s/%s' % (remove_dir, item)
            if os.path.isdir(item):
                self.clean_up(remove_dir=item)
            elif os.path.isfile(item):
                os.remove(item)
        if os.path.exists(remove_dir):
            os.removedirs(remove_dir)

    def _prepare_working_dir(self, centers):
        """
        Create all of the necessary empty directories
        :return: {bool} True=success; False=failure
        """
        try:
            # create a new temporary directory
            self.work_dir = tempfile.mkdtemp(prefix='SUM')

            # list the necessary subdirectories
            subdirs = ['work',
                       'data',
                       'plots/compare/full',
                       'plots/compare/rad',
                       'plots/compare/conv']
            subdirs += ['plots/summary/%s' % center for center in centers]

            # create the subdirectories
            for subdir in subdirs:
                full_path = '%s/%s' % (self.work_dir, subdir)
                os.makedirs(full_path, exist_ok=True)

            return True
        except Exception as e:
            self.errors.append('Error preparing working directory')
            print(e)
            return False

    @staticmethod
    def _filter_platforms_from_data(df, platforms):
        """
        Filter out platforms that were not requested by the user
        :param df: The summary metrics data frame
        :param platforms: {str} A comma-separated list of platforms that should be included
        :return: None - 'df' object is modified
        """
        # create a list of all upper case platform present in the request
        included_platforms = []
        for platform in platforms.split(','):
            included_platforms.append(platform.upper())

        # create a list of all platforms present in the data frame, but not the request
        excluded_platforms = []
        case_sensitive_included_platforms = []
        for platform in df.index:
            if platform.upper() not in included_platforms:
                excluded_platforms.append(platform)
            else:
                case_sensitive_included_platforms.append(platform)

        # drop platforms from the data frame that were not in the request
        df.drop(excluded_platforms, inplace=True)

        # update the index (i.e., list of platforms) in the data frame
        df.reindex(case_sensitive_included_platforms)


class SummaryPlotGenerator(PlotGenerator):
    """
    A class to manage the creation of plots
    """
    def __init__(self, start_date, end_date, center, norm, cycles, platforms, plot_util):
        """
        Create an object to manage a set of plots for one center
        :param start_date: {str} Start date in format YYYYMMDD
        :param end_date: {str} End date in format YYYYMMDD
        :param center: {str} Name of the center
        :param norm: {str} May be 'dry', 'moist', or 'both'
        :param cycles: {list} List of integers may include 0, 6, 12, and 18
        :param platforms: {list} List of platform strings
        :param plot_util: {str} May be 'bokeh' or 'matplotlib'
        """
        # call super constructor
        super().__init__()

        # store parameters
        self.start_date = start_date
        self.end_date = end_date
        self.center = center
        self.norm = norm
        self.cycles = cycles
        self.platforms = platforms
        self.plot_util = plot_util

        # additional empty fields
        self.descriptors = []
        self.json_data = []
        self.pickles = []

    def create_plot_set(self):
        """
        Create a chart as a PNG based on the input parameters
        :return: JSON response
        """
        # create the requested plots
        self._prepare_working_dir([self.center])
        self._create_data_descriptors()
        self._download_data()
        self._create_plots()

    def _download_data(self):
        """
        Download all required objects from S3
        :return: {list} A list of lists, where each item in the main list is an object that was expected
                        to be downloaded.  The sub lists contain [s3_key, center, norm, date, cycle,
                        downloaded_boolean, local_file]
        """
        data_dir = '%s/data/%s' % (self.work_dir, self.center)

        # create the S3 data store
        datastore = ThreadedDataStore(FsoiS3DataStore(), 5)

        # download all the objects using the data store
        for descriptor in self.descriptors:
            # create the local file name
            descriptor['local_path'] = '%s%s' % (data_dir, descriptor['local_path'])

            # start the download
            datastore.load_to_local_file(descriptor, descriptor['local_path'])

        # wait for downloads to finish
        datastore.join()

        # check that files were downloaded and prepare a response message
        for descriptor in self.descriptors:
            if not os.path.exists(descriptor['local_path']):
                descriptor['downloaded'] = False
                message = 'Missing data: %s' % S3DataStore.descriptor_to_string(descriptor)
                self.warns.append(message)
            else:
                descriptor['downloaded'] = True

    def _create_data_descriptors(self):
        """
        Create a list of data descriptors needed for these plots and stored in member variable
        :return: None
        """
        # create a list of norm values
        norms = ['dry', 'moist'] if self.norm == 'both' else [self.norm]

        for date in self._dates_in_range(self.start_date, self.end_date):
            for cycle in self.cycles:
                for norm in norms:
                    descriptor = FsoiS3DataStore.create_descriptor(
                        type='groupbulk',
                        center=self.center,
                        norm=norm,
                        date=date,
                        hour=('%02d' % int(cycle))
                    )
                    descriptor['local_path'] = FsoiS3DataStore.get_suggested_file_name(descriptor)
                    self.descriptors.append(descriptor)

    def _create_plots(self):
        """
        Run the fsoi_summary.py script on the groupbulk statistics
        :return: None
        """
        # create a list of downloaded files for this center
        files = []
        for descriptor in self.descriptors:
            if descriptor['downloaded']:
                files.append(descriptor['local_path'])

        # read all of the files
        ddf = {}
        for (i, file) in enumerate(files):
            try:
                ddf[i] = self._aggregate_by_platform(lib_utils.readHDF(file, 'df'))
            except Exception as e:
                log.error('Failed to aggregate by platform: %s' % file, e)

        # finish if we have no data
        if not ddf:
            self.warns.append('No data available for %s' % self.center)
            return

        # concatenate the group bulk data and save to a pickle
        concatenated = pandas.concat(ddf, axis=0)
        pickle_dir = '%s/work/%s/%s' % (self.work_dir, self.center, self.norm)
        pickle_file = '%s/%s_group_stats.pkl' % (pickle_dir, self.center)
        os.makedirs(pickle_dir, exist_ok=True)
        if os.path.exists(pickle_file):
            os.remove(pickle_file)
        lib_utils.pickle(pickle_file, concatenated)
        self.pickles.append(pickle_file)

        # time-average the data frames
        df, df_std = lib_obimpact.tavg(concatenated, 'PLATFORM')
        df = lib_obimpact.summarymetrics(df)

        # filter out the platforms that were not in the request
        self._filter_platforms_from_data(df, self.platforms)

        # do not continue if all platforms have been removed
        if len(df) == 0:
            self.warns.append('Selected platforms are unavailable for %s' % self.center)
            return

        # create the cycle identifier
        cycle_id = ''
        cycle_ints = []
        for c in self.cycles:
            cycle_id += '%02dZ' % int(c)
            cycle_ints.append(int(c))

        # create the plots
        for qty in ['TotImp', 'ImpPerOb', 'FracBenObs', 'FracNeuObs', 'FracImp', 'ObCnt']:
            try:
                # create the plot options
                platforms = lib_obimpact.Platforms('OnePlatform')
                plot_options = lib_obimpact.getPlotOpt(
                    qty,
                    cycle=cycle_ints,
                    center=self.center,
                    savefigure=True,
                    platform=platforms,
                    domain='Global'
                )
                plot_file = '%s/plots/summary/%s/%s_%s_%s' % (self.work_dir, self.center, self.center, qty, cycle_id)
                plot_options['figure_name'] = plot_file
                if 'bokeh' == self.plot_util:
                    bokehsummaryplot(df, qty=qty, plot_options=plot_options, std=df_std)
                elif 'matplotlib' == self.plot_util:
                    matplotlibsummaryplot(df, qty=qty, plot_options=plot_options, std=df_std)

                # store the output file locations
                self.plots.append('%s.png' % plot_file)
                if 'bokeh' == self.plot_util:
                    self.json_data.append('%s.json' % plot_file)

            except Exception as e:
                log.error('Failed to generate summary plots for %s' % qty, e)

    @staticmethod
    def _dates_in_range(start_date, end_date):
        """
        Get a list of dates in the range
        :param start_date: {str} yyyyMMdd
        :param end_date:  {str} yyyyMMdd
        :return: {list} List of dates in the given range (inclusive)
        """
        start_year = int(start_date[0:4])
        start_month = int(start_date[4:6])
        start_day = int(start_date[6:8])
        start = datetime(start_year, start_month, start_day)
        s = int(start.timestamp())

        end_year = int(end_date[0:4])
        end_month = int(end_date[4:6])
        end_day = int(end_date[6:8])
        end = datetime(end_year, end_month, end_day)
        e = int(end.timestamp())

        dates = []
        for ts in range(s, e + 1, 86400):
            d = datetime.utcfromtimestamp(ts)
            dates.append('%04d%02d%02d' % (d.year, d.month, d.day))

        return dates

    @staticmethod
    def _aggregate_by_platform(df):
        """
        Aggregate all of the data by platform using the unified platform list (e.g. [MODIS_Wind and
        AMV-MODIS] go under a single index called MODIS Wind).
        :param df: The original data frame, which will be deleted upon successful completion
        :return: {pandas.DataFrame} A new data frame with data aggregated by unified platform list
        """
        # turn the unified platform list inside-out for quick look up
        platform_to_aggregate_map = {}
        unified_platforms = lib_obimpact.Platforms('OnePlatform')
        for common_platform in unified_platforms:
            for specific_platform in unified_platforms[common_platform]:
                platform_to_aggregate_map[specific_platform] = common_platform
            platform_to_aggregate_map[common_platform] = common_platform

        # iterate through the rows of the data frame and make a new data array
        columns = ['TotImp', 'ObCnt', 'ObCntBen', 'ObCntNeu']
        common_row_map = {}
        for index, row in df.iterrows():
            # get the date/time and specific platform from the index
            dt, specific_platform = index

            # get the common platform name for this row
            if specific_platform in platform_to_aggregate_map:
                common_platform = platform_to_aggregate_map[specific_platform]
            else:
                common_platform = 'Unknown'
                log.warn('Unknown platform: %s' % specific_platform)

            # create the common index
            common_index = (dt, common_platform)

            # get (or create a new) data row for the common platform name
            if common_index not in common_row_map:
                common_row_map[common_index] = [dt, common_platform] + [0] * len(columns)
            common_row = common_row_map[common_index]

            # sum the values from the row with the new common row
            for i in range(len(row)):
                common_row[i+2] += row[i]

        # put the new values into a new values array
        common_values = [common_row_map[common_index][2:] for common_index in common_row_map]

        # create the new index for the common data frame
        common_platform_list = [common_index[1] for common_index in common_row_map]
        levels = [[list(common_row_map)[0][0]], common_platform_list]
        codes = [[0] * len(common_platform_list), list(range(len(common_platform_list)))]
        new_index = pandas.MultiIndex(levels=levels, codes=codes, names=['DATETIME', 'PLATFORM'])
        common_df = pandas.DataFrame(
            common_values,
            index=new_index,
            columns=columns
        )

        return common_df


class ComparisonPlotGenerator(PlotGenerator):
    """
    A class to manage the creation of plots
    """
    def __init__(self, centers, norm, cycles, platforms, plot_util, pickles):
        """
        Create an object to manage a set of inter-center comparison plots
        :param centers: {list} List of strings of center names
        :param norm: {str} May be 'dry', 'moist', or 'both'
        :param cycles: {list} List of integers may include 0, 6, 12, and 18
        :param platforms: {list} List of platform strings
        :param plot_util: {str} May be 'bokeh' or 'matplotlib'
        :param pickles: {list} List of pickle files for all centers
        """
        # call the super constructor
        super().__init__()

        # save parameters
        self.centers = centers
        self.norm = norm
        self.cycles = cycles
        self.platforms = platforms
        self.plot_util = plot_util
        self.pickles = pickles

        self.json_data = []

    def create_plot_set(self):
        """
        Create a set of comparison plots
        :return: None
        """
        self._prepare_working_dir(self.centers)
        self._create_plots()

    def _create_plots(self):
        """
        Create the comparison plots
        :return:
        """
        # get the palette for the selected centers
        palette = lib_obimpact.getcomparesummarypalette(self.centers)

        # create a string with all the cycles listed
        cycle_str = ''.join('%02dZ' % c for c in self.cycles)

        # output file name
        data_frame_list = self._load_centers()
        full_df, platforms = self.sort_centers(data_frame_list)

        for qty in ['TotImp', 'ImpPerOb', 'FracBenObs', 'FracNeuObs', 'FracImp', 'ObCnt']:
            try:
                plot_options = lib_obimpact.getPlotOpt(qty, savefigure='compare', center=None, cycle=self.cycles)
                plot_file = '%s/plots/compare/%s/comparefull_%s_%s' % \
                            (self.work_dir, 'full', plot_options.get('figure_name'), cycle_str)
                plot_options['figure_name'] = plot_file
                tmp_df = []
                for c, center in enumerate(self.centers):
                    tmp = full_df[c][qty]
                    tmp.name = center
                    index = []
                    for single_platform in tmp.index:
                        index.append((single_platform.upper()))
                    tmp.index = pandas.CategoricalIndex(data=index, name='PLATFORM')
                    self._filter_platforms_from_data(tmp, self.platforms)
                    tmp = tmp.reindex(platforms)
                    tmp_df.append(tmp)

                # finish if we have no data
                if not tmp_df:
                    self.errors.append('No data found for request.')
                    return

                df = pandas.concat(tmp_df, axis=1, sort=True)
                platforms.reverse()
                df = df.reindex(platforms)
                self._filter_platforms_from_data(df, self.platforms)

                # create the plot with the selected plotting utility
                if 'bokeh' == self.plot_util:
                    bokehcomparesummaryplot(df, palette, qty=qty, plot_options=plot_options)
                elif 'matplotlib' == self.plot_util:
                    matplotlibcomparesummaryplot(df, palette, plot_options)

                # append the plot file
                self.plots.append('%s.png' % plot_file)
                if self.plot_util == 'bokeh':
                    self.json_data.append('%s.json' % plot_file)

            except Exception as e:
                log.error('Failed to generate comparison plots for %s' % qty, e)

    def _load_centers(self):
        """
        Load data for specified centers
        :return: {list<pandas.DataFrame>} The loaded data as a list of data frames
        """
        data_frame_list = []
        for pickle in self.pickles:
            df = lib_utils.unpickle(pickle)
            dt_filter = df.index.get_level_values('DATETIME').hour == -1
            for c in self.cycles:
                dt_filter = numpy.ma.logical_or(dt_filter, df.index.get_level_values('DATETIME').hour == c)
            df = df[dt_filter]

            df, df_std = lib_obimpact.tavg(df, level='PLATFORM')
            df = lib_obimpact.summarymetrics(df)

            data_frame_list.append(df)

        return data_frame_list

    @staticmethod
    def sort_centers(data_frame_list):
        """
        Sort centers
        :param data_frame_list: {list<pandas.DataFrame>} A list of data frames
        :return: {pandas.DataFrame, list} A sorted data frame and list of platforms included by at least 1 center
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
            if platform_count[key] >= 1:
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

    @staticmethod
    def _filter_platforms_from_data(df, platforms):
        """
        Filter out platforms that were not requested by the user
        :param df: The summary metrics data frame
        :param platforms: {str} A comma-separated list of platforms that should be included
        :return: None - 'df' object is modified
        """
        # create a list of all upper case platform present in the request
        included_platforms = []
        for platform in platforms.split(','):
            included_platforms.append(platform.upper())

        # create a list of all platforms present in the data frame, but not the request
        excluded_platforms = []
        case_sensitive_included_platforms = []
        for platform in df.index:
            if platform.upper() not in included_platforms:
                excluded_platforms.append(platform)
            else:
                case_sensitive_included_platforms.append(platform)

        # drop platforms from the data frame that were not in the request
        df.drop(excluded_platforms, inplace=True)

        # update the index (i.e., list of platforms) in the data frame
        df.reindex(case_sensitive_included_platforms)
