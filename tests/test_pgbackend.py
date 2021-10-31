import pyqtgraph as pg
from dfana import dfana
from functools import partial

QtDeltaTimeMS = 50


def test_lineplot_pg_interactions():
    # in this test we open a plot via pyqtgraph and interact with it. when we are done,
    # we close it
    ss = pg.QtCore.QTimer.singleShot
    plts = dfana.plot("example_stepresponses1")
    app = pg.mkQApp()
    plt = plts[0].plt
    lambdas = [
        # we click the button multiple times to trigger all edge-cases
        partial(plt.cursBtn.mouseClickEvent, plt.cursBtn),
        partial(plt.setCursorsVisible, plt.cursBtn, True),
        partial(plt.setCursorsVisible, plt.cursBtn, False),
        partial(plt.setCursorsVisible, plt.cursBtn, False),
        partial(plt.setCursorsVisible, plt.cursBtn, True),
        partial(plt.cursors[0].setPos, 1000),
        partial(plt.updateCursorVals, plt.cursors[0]),
        partial(plts[0].invalidateScene),
        partial(plt.setVisible, False),
        app.quit,
    ]
    for idx, L in enumerate(lambdas):
        ss(idx * QtDeltaTimeMS, L)
    dfana.showPlots(plots=plts)


def test_lineplot_pg_zoomplt():
    ss = pg.QtCore.QTimer.singleShot
    plts = dfana.plot("example_stepresponses1")
    app = pg.mkQApp()
    plt = plts[0].plt

    failureContainer = []

    def assertZoomPlot(fig, failureContainer):
        try:
            assert fig.subPlt.isVisible()
            assert fig.subPlt.titleLabel.text.startswith("Zoom")
        except Exception as e:
            failureContainer.append(e)

    lambdas = [
        partial(plt.cursBtn.mouseClickEvent, plt.cursBtn),  # display the cursors
        partial(plt.zoomBtn.mouseClickEvent, plt.zoomBtn),  # display the zoom plot
        partial(plt.roi.setRelRegion, (0.2, 0.8)),
        partial(plt.roi.setRelRegion, (0.3, 0.3)),  # test div/0
        partial(assertZoomPlot, plts[0], failureContainer),  # check that it worked
        partial(plt.zoomBtn.mouseClickEvent, plt.zoomBtn),  # hide the zoom plot
        partial(plt.roi.setRelRegion, (0.3, 0.7)),
        app.quit,
    ]
    for idx, L in enumerate(lambdas):
        ss(idx * QtDeltaTimeMS, L)
    dfana.showPlots(plots=plts)
    assert not any(failureContainer)
