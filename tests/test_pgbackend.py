import pyqtgraph as pg
from dfana import dfana
from functools import partial

QtDeltaTimeMS = 100


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

    zoombtn = plt.btns["zoom"]

    lambdas = [
        partial(plt.cursBtn.mouseClickEvent, plt.cursBtn),  # display the cursors
        partial(zoombtn.mouseClickEvent, zoombtn),  # display the zoom plot
        partial(plt.roi.setRelRegion, (0.2, 0.8)),
        partial(plt.roi.setRelRegion, (0.3, 0.3)),  # test div/0
        partial(assertZoomPlot, plts[0], failureContainer),  # check that it worked
        partial(zoombtn.mouseClickEvent, zoombtn),  # hide the zoom plot
        partial(plt.roi.setRelRegion, (0.3, 0.7)),
        partial(plt.cursBtn.mouseClickEvent, plt.cursBtn),  # hide the cursors
        app.quit,
    ]
    for idx, L in enumerate(lambdas):
        ss(idx * QtDeltaTimeMS, L)
    dfana.showPlots(plots=plts)
    assert not any(failureContainer)


def test_lineplot_pg_fftplt():
    ss = pg.QtCore.QTimer.singleShot
    plts = dfana.plot("example_stepresponses1")
    app = pg.mkQApp()
    plt = plts[0].plt

    failureContainer = []

    def assertFFTPlot(fig, failureContainer):
        try:
            assert fig.subPlt.isVisible()
            assert fig.subPlt.titleLabel.text.startswith("FFT")
        except Exception as e:
            failureContainer.append(e)

    btn = plt.btns["fft"]

    lambdas = [
        partial(plt.cursBtn.mouseClickEvent, plt.cursBtn),  # display the cursors
        partial(btn.mouseClickEvent, btn),  # display the zoom plot
        partial(plt.roi.setRelRegion, (0.2, 0.8)),
        partial(plt.roi.setRelRegion, (0.3, 0.3)),  # test div/0
        partial(assertFFTPlot, plts[0], failureContainer),  # check that it worked
        app.quit,
    ]
    for idx, L in enumerate(lambdas):
        ss(idx * QtDeltaTimeMS, L)
    dfana.showPlots(plots=plts)
    assert not any(failureContainer)


def test_lineplot_pg_switchPlugins():
    ss = pg.QtCore.QTimer.singleShot
    plts = dfana.plot("example_stepresponses1")
    app = pg.mkQApp()
    plt = plts[0].plt

    failureContainer = []

    def assertFFTPlot(fig, failureContainer):
        try:
            assert fig.subPlt.isVisible()
            assert fig.subPlt.titleLabel.text.startswith("FFT")
        except Exception as e:
            failureContainer.append(e)

    btn = plt.btns["fft"]
    zoombtn = plt.btns["zoom"]

    lambdas = [
        partial(btn.mouseClickEvent, btn),  # display the fft plot
        partial(zoombtn.mouseClickEvent, zoombtn),  # display the zoom plot
        app.quit,
    ]
    for idx, L in enumerate(lambdas):
        ss(idx * QtDeltaTimeMS, L)
    dfana.showPlots(plots=plts)
    assert not any(failureContainer)


def test_lineplot_pg_spec():
    ss = pg.QtCore.QTimer.singleShot
    plts = dfana.plot("example_spectral1")
    # app = pg.mkQApp()
    plt = plts[0].plt

    failureContainer = []
    btn = plt.btns["spec"]

    lambdas = [
        partial(btn.mouseClickEvent, btn),  # display the spec plot
        # app.quit,
    ]
    for idx, L in enumerate(lambdas):
        ss(idx * QtDeltaTimeMS, L)
    dfana.showPlots(plots=plts)
    assert not any(failureContainer)
