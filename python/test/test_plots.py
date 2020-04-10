import os
import hashlib
from fsoi.plots.managers import SummaryPlotGenerator, ComparisonPlotGenerator


def test_bokeh_plots():
    platforms = 'IASI,Aircraft'
    centers = ['NRL', 'GMAO']
    spgs = {}
    pickles = []
    for center in centers:
        spg = SummaryPlotGenerator('20200301', '20200331', center, 'both', [0], platforms, 'bokeh')
        spg.create_plot_set()
        spgs[center] = spg
        pickles += spg.pickles
    cpg = ComparisonPlotGenerator(centers, 'both', [0], platforms, 'bokeh', pickles)
    cpg.create_plot_set()

    expected = {
        'NRL_FracBenObs_00Z.png': '215d0b1a83e0edb2faa348956ec49a535590632d1bcab5e87f6b2cfbf2863d61',
        'NRL_FracImp_00Z.png': 'f78593267f57c199390e34321c2650519c56e0024b3973349fe3661f23d66961',
        'NRL_FracNeuObs_00Z.png': '69c1f923becfba5415051d42b7795ac100e5599140960d80d69a5075a16509ad',
        'NRL_ImpPerOb_00Z.png': '26a98dc77e7c0a2985219d5f08275cc6f081f2475217ddf8fc0cac97af207bda',
        'NRL_ObCnt_00Z.png': '1bb6fb7e10cedb452d3e5c812540fd092f6bb7a8a66a6232e2a8eee2a575c2d1',
        'NRL_TotImp_00Z.png': 'b513a69ee769daa035e2ae2502e10ad8f9120516e1247842f4a7766be05606fa',
        'NRL_FracBenObs_00Z.json': '70d0f5de681f150742d3565d35b4eeb9c3c879dac3880b98293edfb3a70b1515',
        'NRL_FracImp_00Z.json': '4f56cfc67ab42ec1cfeb68f4ace20de146aebc2a8cb3f8da8a63f27778335e1b',
        'NRL_FracNeuObs_00Z.json': '5c5514ca3a16afb7d33ed7c171e7ce92cc3bbe1d54e9f8b3135a705870ab1b66',
        'NRL_ImpPerOb_00Z.json': '8d0277310f421ee27a448b2376f5614b9293772fd2d05c8638aac6b7f1e4a442',
        'NRL_ObCnt_00Z.json': '7f33bf5afc02534dc2954068c6b9f78a2266252369d5b21980c975c4ba57971e',
        'NRL_TotImp_00Z.json': '478647f3993d2182a526e4a832592f88bcbf62411de6b8553d65085656a0201c'
    }

    nrl_spg = spgs['NRL']
    assert len(nrl_spg.plots) == 6
    for plot in nrl_spg.plots:
        data = open(plot, 'rb').read()
        chksum = hashlib.sha256(data).hexdigest()
        file_key = plot.split('/')[-1]
        expected[file_key] = chksum
        # assert expected[file_key] == chksum

    assert len(nrl_spg.plots) == 6
    for json_data in nrl_spg.json_data:
        data = open(json_data, 'rb').read()
        chksum = hashlib.sha256(data).hexdigest()
        file_key = json_data.split('/')[-1]
        expected[file_key] = chksum
        # assert expected[file_key] == chksum

    print(expected)
    nrl_spg.clean_up()
    assert not os.path.exists(nrl_spg.work_dir)
