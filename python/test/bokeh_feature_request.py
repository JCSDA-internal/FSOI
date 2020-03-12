"""
GitHub Feature Request Issue: https://github.com/bokeh/bokeh/issues/9774

An example horizontal stacked bar chart to work with for the dynamically positioned bar chart segments feature.
Slightly modified from: https://docs.bokeh.org/en/latest/docs/user_guide/categorical.html
"""

from bokeh.io import show
from bokeh.plotting import figure

fruits = ['Apples', 'Pears', 'Nectarines', 'Plums', 'Grapes', 'Strawberries']
years = ['2015', '2016', '2017']
colors = ['#c9d9d3', '#718dbf', '#e84d60']

data = {'fruits': fruits,
        '2015': [2, 1, 4, 3, 2, 4],
        '2016': [5, 3, 4, 2, 4, 6],
        '2017': [3, 2, 4, 4, 5, 3]}

p = figure(y_range=fruits, plot_height=250, title='Fruit Counts by Year', toolbar_location=None, tools='')

p.hbar_stack(years, y='fruits', height=0.9, color=colors, source=data, legend_label=years)

p.x_range.start = 0
p.y_range.range_padding = 0.1
p.ygrid.grid_line_color = None
p.axis.minor_tick_line_color = None
p.outline_line_color = None
p.legend.location = 'top_right'
p.legend.orientation = 'vertical'
p.legend.click_policy = 'hide'

show(p)
