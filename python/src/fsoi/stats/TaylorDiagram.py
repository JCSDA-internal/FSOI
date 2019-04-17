#!/usr/bin/env python

'''
Taylor Diagram (Taylor, 2001)

http://www-pcmdi.llnl.gov/about/staff/Taylor/CV/Taylor_diagram_primer.htm

Adapted from:
https://gist.github.com/ycopin/3342888

Modifications:
    0. Cosmetic updates, e.g. numpy is imported as _np, etc.
    1. Removed the test function
    2. Added the ability to create Full Taylor
'''

import numpy as _np
from matplotlib import pyplot as _plt


class TaylorDiagram(object):
    """Taylor diagram: plot model standard deviation and correlation
    to reference (data) sample in a polar plot, with
    r=stddev and theta=arccos(correlation).
    """

    def __init__(self, refstd, fig=None, rect=111, label='_', norm=False, full=False, grid=True):
        """Set up Taylor diagram axes, i.e. polar plot,
        using mpl_toolkits.axisartist.floating_axes. refstd is
        the reference standard deviation to be compared to.
        norm : flag to normalize with respect to refstd.
        full : flag to create single quadrant or semi-circle
        """

        from matplotlib.projections import PolarAxes as _PolarAxes
        import mpl_toolkits.axisartist.floating_axes as _FA
        import mpl_toolkits.axisartist.grid_finder as _GF

        self.refstd = refstd  # Reference standard deviation
        self.norm = norm  # Normalized or Absolute
        self.full = full  # Full or Single-quadrant Taylor
        self.grid = grid  # Cyan grid-lines at correlation theta

        tr = _PolarAxes.PolarTransform()

        # Correlation labels
        rlocs = _np.concatenate((_np.arange(10) / 10., [0.95, 0.99]))
        if self.full:
            rlocs = _np.concatenate([-1. * _np.flipud(rlocs)[:-1], rlocs])
        tlocs = _np.arccos(rlocs)  # Conversion to polar angles
        gl1 = _GF.FixedLocator(tlocs)  # Positions
        tf1 = _GF.DictFormatter(dict(zip(tlocs, map(str, rlocs))))

        # Standard deviation axis extent and labels
        self.smin = 0
        if self.norm:
            self.smax = 1.5
            slocs = _np.arange(self.smax * 10)[::2] / 10.
            gl2 = _GF.FixedLocator(slocs)
            tf2 = _GF.DictFormatter(dict(zip(slocs, map(str, slocs))))
        else:
            self.smax = 1.5 * self.refstd
            gl2 = None
            tf2 = None

        self.ext_max = _np.pi if self.full else _np.pi / 2.
        ghelper = _FA.GridHelperCurveLinear(tr,
                                            extremes=(0., self.ext_max,
                                                      self.smin, self.smax),
                                            grid_locator1=gl1,
                                            tick_formatter1=tf1,
                                            grid_locator2=gl2,
                                            tick_formatter2=tf2,
                                            )

        if fig is None:
            fig = _plt.figure()
        self.fig = fig

        ax = _FA.FloatingSubplot(fig, rect, grid_helper=ghelper)
        fig.add_subplot(ax)

        # Adjust axes
        ax.axis["top"].set_axis_direction("bottom")  # "Angle axis"
        ax.axis["top"].toggle(ticklabels=True, label=True)
        ax.axis["top"].major_ticklabels.set_axis_direction("top")
        ax.axis["top"].label.set_axis_direction("top")
        ax.axis["top"].label.set_text("Correlation")
        ax.axis["top"].label.set_fontsize(12)
        ax.axis["top"].label.set_fontweight("normal")

        ax.axis["left"].set_axis_direction("bottom")  # "X axis"
        ax.axis["left"].label.set_text(
            "Normalized Standard Deviation" if self.norm else "Standard Deviation")
        ax.axis["left"].label.set_fontsize(12)
        ax.axis["left"].label.set_fontweight("normal")

        ax.axis["right"].set_axis_direction("top")  # "Y axis"
        ax.axis["right"].toggle(ticklabels=True)

        if self.full:
            ax.axis["right"].major_ticklabels.set_axis_direction("bottom")
            ax.axis["bottom"].toggle(ticklabels=False)
            ax.axis["bottom"].set_axis_direction("bottom")
        else:
            ax.axis["right"].major_ticklabels.set_axis_direction("left")
            ax.axis["bottom"].set_visible(False)  # Useless

        # Contours along standard deviations
        ax.grid(False)

        self._ax = ax  # Graphical axes
        self.ax = ax.get_aux_axes(tr)  # Polar coordinates

        # Add reference point and stddev contour
        # print "Reference std:", self.refstd
        l, = self.ax.plot([0], 1.0 if self.norm else self.refstd, 'k*',
                          ls='', ms=10, label=label)
        t = _np.linspace(0, self.ext_max)
        r = _np.zeros_like(t) + (1.0 if self.norm else self.refstd)
        self.ax.plot(t, r, 'k--', label='_')

        # Collect sample points for latter use (e.g. legend)
        self.samplePoints = [l]

        # Add 0 line if full Taylor
        if self.full:
            r = _np.linspace(0., self.smax)
            t = _np.zeros_like(r) + _np.pi / 2.
            self.ax.plot(t, r, 'k--', label='_')

        # Add cyan radii at all correlations:
        if self.grid:
            r = _np.linspace(0., self.smax)
            for th in tlocs:
                th_deg = 180. * th / _np.pi
                if not (20. < th_deg < 160. and th_deg != 90.): continue
                t = _np.zeros_like(r) + th
                self.ax.plot(t, r, 'c-', label='_')

        return

    def add_sample(self, stddev, corrcoef, *args, **kwargs):
        """Add sample (stddev,corrcoeff) to the Taylor diagram. args
        and kwargs are directly propagated to the Figure.plot
        command."""

        l, = self.ax.plot(_np.arccos(corrcoef), stddev / (self.refstd if self.norm else 1.0),
                          *args, **kwargs)  # (theta,radius)
        self.samplePoints.append(l)

        return l

    def add_contours(self, levels=5, **kwargs):
        """Add constant centered RMS difference contours."""

        rs, ts = _np.meshgrid(_np.linspace(self.smin, self.smax),
                              _np.linspace(0, self.ext_max))
        # Compute centered RMS difference
        rms = _np.sqrt((self.refstd / (self.refstd if self.norm else 1.0)) ** 2 + rs ** 2 - 2 * (
                    self.refstd / (self.refstd if self.norm else 1.0)) * rs * _np.cos(ts))

        contours = self.ax.contour(ts, rs, rms, levels, **kwargs)

        return contours
