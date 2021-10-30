import pyqtgraph as pg
from dfana import dfana
from functools import partial


def test_lineplot_pg_interactions():
    # in this test we open a plot via pyqtgraph and interact with it. when we are done,
    # we close it
    ss = pg.QtCore.QTimer.singleShot
    plts = dfana.plot("example_stepresponses1")
    app = pg.mkQApp()
    plt = plts[0].plt
    lambdas = [
        # we clicl k the button multiple times to trigger all edge-cases
        partial(plt.cursBtn.clicked.emit, True),
        partial(plt.cursBtn.clicked.emit, True),
        partial(plt.cursBtn.clicked.emit, False),
        partial(plt.cursBtn.clicked.emit, False),
        partial(plt.cursBtn.clicked.emit, True),
        partial(plt.cursors[0].setPos, 1000),
        partial(plt.updateCursorVals, plt.cursors[0]),
        partial(plts[0].invalidateScene),
        partial(plt.setVisible, False),
        app.quit,
    ]
    for idx, L in enumerate(lambdas):
        ss(idx * 50, L)
    dfana.showPlots(plots=plts)


def test_lineplot_pg_zoomplt():
    ss = pg.QtCore.QTimer.singleShot
    plts = dfana.plot("example_stepresponses1")
    app = pg.mkQApp()
    lambdas = [
        app.quit,
    ]
    for idx, L in enumerate(lambdas):
        ss(idx * 50, L)
    dfana.showPlots(plots=plts)
