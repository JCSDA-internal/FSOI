"""
FSOI Plots
"""
__all__ = ['compare_fsoi', 'correlations_binned_map', 'correlations_binned_Taylor',
           'correlations_bulk_Taylor', 'summary_fsoi', 'summary_fsoi_map',
           'Plot', 'summary_plot']

import os
import copy
import yaml
import pkgutil
from fsoi import log


class Plot:
    """
    An abstract class to hold basic functions to support plot creation
    """

    def __init__(self, options=None, defaults=None):
        """
        Initialize the object with optional plot options
        :param options: {dict|None} A dictionary used by sub-classes to make plots
        """
        # create fields expected in this object
        self.options = {}
        self.center_names = {}
        self.metric_defaults = {}
        self.output_file = None

        # read the default options
        if defaults:
            resource = 'resources/fsoi/plots/%s.yaml' % defaults
            data = yaml.load(pkgutil.get_data('fsoi', resource))
            self.options = data['default_options']
            self.center_names = data['center_names']
            self.metric_defaults = data['metric_defaults']

        # override the default options with any options provided
        if options is not None:
            if isinstance(options, dict):
                for key in options:
                    self.options[key] = copy.deepcopy(options[key])
            else:
                msg = 'options parameter passed to Plot constructor must be a dictionary'
                log.error(msg)
                raise TypeError(msg)

    def set_option(self, name, value):
        """
        Set a single option value
        :param name: Option name
        :param value: Option value
        :return: None
        """
        self.options[name] = value

    def set_output_file(self, output_file):
        """
        Set the output file
        :param output_file: {str} Full path to the output file
        :return: None
        """
        if not isinstance(output_file, str):
            log.error('Invalid data type for output_file parameter')
            raise TypeError('Invalid type for output_file (%s), expecting str' % type(output_file))

        self.output_file = output_file

    def __prepare_output_path(self):
        """
        Create the directory if it does not already exist
        :return: None
        """
        path = '/'.join(self.output_file.split('/')[0:-1])

        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
