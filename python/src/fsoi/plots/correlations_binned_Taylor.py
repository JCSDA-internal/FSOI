"""
correlations_binned_Taylor.py - make Taylor diagram of binned correlations
"""

from matplotlib import pyplot as plt
import fsoi.stats.lib_utils as lutils
from fsoi.stats.TaylorDiagram import TaylorDiagram


def main():
    """
    :return:
    """
    colors = ["#000000", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"]

    rootdir = '/scratch3/NCEPDEV/stmp2/Rahul.Mahajan/test/Thomas.Auligne/FSOI'
    norm = 'dry'
    platform = 'AMSUA_METOP-B'
    platform = 'Radiosonde'
    savefig = False

    fpkl = '%s/work/%s.%s.corr.pkl' % (rootdir, platform.lower(), norm)

    df_stdv, df_corr = lutils.unpickle(fpkl)

    centers = df_stdv.columns
    ref_center = centers[0]

    refstd = df_stdv[ref_center].mean()
    refstd = 1.0

    fig = plt.figure()

    # Taylor diagram
    full = True
    norm = True
    dia = TaylorDiagram(refstd, fig=fig, rect=111, label=ref_center, norm=norm, full=full)

    # Add samples to Taylor diagram
    for c, center in enumerate(centers[1:]):
        for i, (ref_stdv, stdv, corr) in enumerate(
                zip(df_stdv[ref_center], df_stdv[center], df_corr[center])):
            dia.add_sample(stdv / ref_stdv, corr, marker='o', ms=3, mec=colors[c], ls='', c=colors[c],
                           label=center, alpha=0.2)
            if i != 0: dia.samplePoints.pop()

    # Add RMS contours, and label them
    contours = dia.add_contours(colors='0.5')
    plt.clabel(contours, inline=1, fontsize=10)

    # Add a figure legend
    fig.legend(dia.samplePoints,
               [p.get_label() for p in dia.samplePoints],
               numpoints=1, prop=dict(size='small'), loc='upper right')

    if savefig:
        fname = 'Taylor-%s-%s' % (ref_center, platform)
        lutils.savefigure(fname=fname, format='pdf', fh=fig)
        plt.close('all')
    else:
        plt.show()
