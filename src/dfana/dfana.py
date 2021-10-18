import logging
import argparse
from x2df import x2df
from dfana import examples
from .__metadata__ import __version__
import pandas as pd

log = logging.getLogger("dfana")


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
    showPlots(not args["nonblock"])
    return 0


def showPlots(block=True):
    be = pd.options.plotting.backend
    if be == "matplotlib":
        import matplotlib.pyplot as plt

        plt.show(block=block)


def getExampleNames():
    return tuple(sorted(("example_" + x for x in examples.getClassDict().keys())))


def load(src):
    return x2df.load(src)


def plot(df):
    plotbuffer = []
    if isinstance(df, pd.DataFrame):
        dfs = [df]
    else:
        dfs = load(df)
    for df in dfs:
        plotbuffer.append(df.plot())
    return plotbuffer
