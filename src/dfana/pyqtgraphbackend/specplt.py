from dfana.sharedfuns import getFixedLenString
import numpy as np
import pyqtgraph as pg
from functools import partial
from scipy import signal

name = "spec"
iconName = "spec"


class PltHandler:
    def __init__(self, data, dst):
        self.data = data
        self.dst = dst

    def initialize(self):
        plt = self.dst
        src = self.data["datasrc"]
        xname = src.axes["bottom"]["item"].label.toPlainText().strip()
        plt.setLabel("bottom", xname)
        plt.setTitle("Spectogram")
        plt.customlegend.layout.itemAt(1, 1).setText(xname)
        srccurves = src.curves
        L = len(srccurves)

        def monkeyPatchedMouseclick(item, event):
            L = plt.customlegend.layout
            for idx in range(L.rowCount() - 2):
                it = plt.customlegend.layout.itemAt(idx + 2, 0)
                if (it != item) and it.item.isVisible():
                    it.item.setVisible(False)
            res = pg.graphicsItems.LegendItem.ItemSample.mouseClickEvent(item, event)
            self.updateData(src.roi.getRegion())
            return res

        for idx, cu in enumerate(srccurves):
            plt.plot(x=[0, 0.01], y=[0, 0.01], name=cu.name(), pen=(idx + 1, L))
            it = plt.customlegend.layout.itemAt(idx + 2, 0)
            it.item.setVisible(
                idx < 1
            )  # this means all but the first plot are set to invisible
            it.mouseClickEvent = partial(monkeyPatchedMouseclick, it)

        self.img = pg.ImageItem()
        self.img.setOpts(axisOrder="row-major")
        self.dst.addItem(self.img)

    def updateData(self, reg):
        x0, x1 = reg
        plt = self.dst
        src = self.data["datasrc"]
        xname = src.axes["bottom"]["item"].label.toPlainText()
        s0 = getFixedLenString(x0)
        s1 = getFixedLenString(x1)
        plt.setTitle(f"Spectogram on {xname}: {s0} -- {s1}")

        data = None
        for idx, curve in enumerate(src.curves):
            vis = plt.customlegend.layout.itemAt(idx + 2, 0).item.isVisible()
            if not vis:
                continue
            data = curve
            break
        if data is None:
            self.img.clear()
            return

        x = curve.xData
        y = curve.yData
        mask = np.logical_and(x >= x0, x <= x1)
        x = x[mask]
        y = y[mask]
        N = len(x)

        f, t, Sxx = signal.spectrogram(
            y,
            1 / ((x[-1] - x[0]) / N),
            scaling="spectrum",
            mode="magnitude",
            nperseg=256,
        )
        Sxx *= 2.0

        for idx, curve in enumerate(plt.curves):
            curve.setData(x=[0, x[-1] * 1e-3], y=[0, 0])
            curve.setZValue(-1000)

        x0 = x[0]
        dx = x[-1] - x[0]
        y0 = 0
        dy = f[-1]
        rect = pg.QtCore.QRectF(x0, y0, dx, dy)

        self.img.setImage(Sxx)
        self.img.resetTransform()
        self.img.setRect(rect)
        for x in plt.axes:
            ax = plt.getAxis(x)
            ax.setZValue(1)
        plt.setLimits(yMin=y0, yMax=y0 + dy, xMin=x0, xMax=x0 + dx)
