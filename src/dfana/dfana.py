import logging
import argparse
from x2df import x2df
from x2df.examples import examples
from .__metadata__ import __version__
import pandas as pd

import matplotlib.pyplot as plt
import pandas_bokeh  # noqa:F401
import functools
from dfana import pyqtgraphbackend  # noqa:F401
import pyqtgraph as pg


log = logging.getLogger("dfana")


@functools.cache
def getAvailableBackends():
    beL = ["pandas_bokeh", "matplotlib", "dfana"]
    df = pd.DataFrame()
    for be in beL:  # we need to do this so all the bes are found in _core._backends
        try:
            df.plot(backend=be)
        except (IndexError, TypeError, ValueError):
            continue
    return sorted(list(pd.plotting._core._backends))


getAvailableBackends()


def main(argv):
    parser = argparse.ArgumentParser(
        "parses given glob-style paths and extracts dataframes."
        + " Plots all the given dataframes"
    )
    parser.add_argument("srcs", nargs="*", help="glob-style paths that will be parsed")
    parser.add_argument(
        "-?", action="store_true", help="show this help message and exit"
    )
    parser.add_argument(
        "--nonblock",
        action="store_true",
        help="set to true to open figures in nonblocking mode for debugging "
        + "or batch exports.",
    )
    parser.add_argument("-v", "--version", action="store_true", help="prints version")
    args = argv[1:]
    args = vars(parser.parse_args(args))

    if args["version"]:
        print(__version__)
        return 0
    if args["?"] or not args["srcs"]:
        parser.print_help()
        return 0

    plots = []
    for src in args["srcs"]:
        plots.extend(plot(src))
    showPlots(block=not args["nonblock"], plots=plots)
    return 0


def showPlots(backend=pd.options.plotting.backend, block=True, plots=[]):
    if backend == "matplotlib":
        plt.show(block=block)
    elif backend == "pandas_bokeh":
        pass
    elif backend == "dfana":
        for x in plots:
            x.show()
        app = pg.mkQApp()
        if not block:
            pg.QtCore.QTimer.singleShot(0, app.quit)
        app.exec_()


def getExampleNames():
    return tuple(sorted(("example_" + x for x in examples.getClassDict().keys())))


def getAvailableBackends():
    return sorted(list(pd.plotting._core._backends))


def load(src):
    return x2df.load(src)


def plot(df, backend=None, show=False, block=False):
    plotbuffer = []
    if isinstance(df, pd.DataFrame):
        dfs = [df]
    else:
        dfs = load(df)
    for df in dfs:
        plotbuffer.append(df.plot(backend=backend))
    if show:
        showPlots(block=block, backend=backend, plots=plotbuffer)
    return plotbuffer
