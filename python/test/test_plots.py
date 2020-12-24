import os
from fsoi.plots.managers import SummaryPlotGenerator, ComparisonPlotGenerator


def test_bokeh_plots():
    platforms = 'IASI,Aircraft'
    centers = ['NRL', 'GMAO']
    spgs = {}
    pickles = []

    # create the summary plots
    for center in centers:
        spg = SummaryPlotGenerator('20200301', '20200331', center, 'both', [0], platforms, 'bokeh')
        spg.create_plot_set()
        spgs[center] = spg
        pickles += spg.pickles

    # create the comparison plots
    cpg = ComparisonPlotGenerator(centers, 'both', [0], platforms, 'bokeh', pickles)
    spgs['COMP'] = cpg
    cpg.create_plot_set()

    # check the results
    for key in spgs:
        print('Checking %s...' % key)
        pg = spgs[key]
        if key == 'COMP':
            nplots = 6
        else:
            nplots = 12
        assert len(pg.plots) == nplots
        assert len(pg.json_data) == nplots
        for plot in pg.plots:
            assert os.path.isfile(plot)
        for json_datum in pg.json_data:
            assert os.path.isfile(json_datum)
        pg.clean_up()
        assert not os.path.exists(pg.work_dir)
