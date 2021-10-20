import numpy as np
import pyqtgraph as pg


from pandas.plotting._matplotlib.boxplot import (  # noqa:F401
    BoxPlot,
    boxplot,
    boxplot_frame,
    boxplot_frame_groupby,
)
from pandas.plotting._matplotlib.converter import (  # noqa:F401
    deregister,
    register,
)


from pandas.plotting._matplotlib.tools import table  # noqa:F401

from pandas.plotting._matplotlib.hist import (  # noqa:F401
    HistPlot,
    KdePlot,
    hist_frame,
    hist_series,
)

from pandas.plotting._matplotlib.misc import (  # noqa:F401
    andrews_curves,
    autocorrelation_plot,
    bootstrap_plot,
    lag_plot,
    parallel_coordinates,
    radviz,
    scatter_matrix,
)


class LinePlot(pg.GraphicsLayoutWidget):
    def __init__(self, data, **kwargs):
        super().__init__()
        data = np.random.normal(size=1000)
        p1 = self.addPlot()
        p1.plot(data, title="Simplest possible plotting example")


class BarPlot(LinePlot):
    pass


class BarhPlot(LinePlot):
    pass


class AreaPlot(LinePlot):
    pass


class PiePlot(LinePlot):
    pass


class ScatterPlot(LinePlot):
    pass


class HexBinPlot(LinePlot):
    pass


PLOT_CLASSES = {
    "line": LinePlot,
    "bar": BarPlot,
    "barh": BarhPlot,
    "box": BoxPlot,
    "hist": HistPlot,
    "kde": KdePlot,
    "area": AreaPlot,
    "pie": PiePlot,
    "scatter": ScatterPlot,
    "hexbin": HexBinPlot,
}


def plot(data, kind, **kwargs):
    return PLOT_CLASSES[kind](data, **kwargs)


# we add the entry point dynamically, so it also works in editable mode:
# https://stackoverflow.com/a/48666503
def _addEntryPoint():
    import pkg_resources

    d = pkg_resources.Distribution(__file__)
    ep = pkg_resources.EntryPoint.parse("dfana = dfana:pyqtgraphbackend", dist=d)
    d._ep_map = {"pandas_plotting_backends": {"dfana": ep}}
    pkg_resources.working_set.add(d, "dfana")


_addEntryPoint()
