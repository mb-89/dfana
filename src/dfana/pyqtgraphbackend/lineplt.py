import pyqtgraph as pg
import numpy as np
from functools import partial
from dfana import icons
from dfana.pyqtgraphbackend import zoomplt
from dfana.pyqtgraphbackend import fftplt
from dfana.sharedfuns import getFixedLenString, numValLen

import warnings

warnings.filterwarnings("error")


plugins = [zoomplt, fftplt]


class PltItemWithCursors(pg.PlotItem):
    cursorVisChanged = pg.QtCore.Signal(bool)
    showSubPlot = pg.QtCore.Signal(tuple)
    hideSubPlot = pg.QtCore.Signal()
    roiChangedSig = pg.QtCore.Signal(tuple)

    def __init__(self, xname, hasPlugins=True, **kargs):
        super().__init__(**kargs)
        self.initialized = False
        self.isSubPlot = not hasPlugins
        A = 65
        self.showGrid(1, 1, int(0.75 * 255))
        self.customlegend = LegendWithVals(
            xname,
            pen=pg.mkPen(255, 255, 255, A),
            brush=pg.mkBrush(0, 0, 255, A),
            offset=(70, 20),
        )
        self.customlegend.setParentItem(self)
        self.addCursors(hasPlugins)

        self.subplotData = {}
        self.openPlugin = None
        self.setTitle("")
        if hasPlugins:
            self.addROI()
            self.addPlugins()
        self.initialized = True

    def addCursors(self, hasPlugins):
        if hasPlugins:
            # if we have no plugins, the cursor btn is part of a different plot widget
            self.cursBtn = pg.ButtonItem(
                icons.getIcon("cursor"), width=14, parentItem=self
            )

        self.c1 = RelPosCursor(1 / 3, label="C1")
        self.c2 = RelPosCursor(2 / 3, label="C2")
        self.addItem(self.c1)
        self.addItem(self.c2)
        self.cursors = dict((idx, c) for idx, c in enumerate([self.c1, self.c2]))
        self.proxies = [
            pg.SignalProxy(
                c.sigPositionChanged, rateLimit=30, slot=self.updateCursorVals
            )
            for c in self.cursors.values()
        ]
        for k, v in self.cursors.items():
            v.idx = k
        if hasPlugins:
            self.cursBtn.clicked.connect(self.setCursorsVisible)
        self.cursorVisChanged.connect(self.toggleCursorVis)

    def setCursorsVisible(self, btn, vis=None):
        if vis is None:
            vis = not self.c1.isVisible()
        for k, v in self.cursors.items():
            v.setVisible(vis)
        self.cursorVisChanged.emit(vis)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if not self.initialized:  # pragma: no cover #this can only happen in debugger
            return
        if (
            self.autoBtn is None or self.isSubPlot
        ):  # pragma: no cover # already closed down
            return
        btnRect = self.mapRectFromItem(self.autoBtn, self.autoBtn.boundingRect())
        # y = self.size().height() - btnRect.height()
        y = -20
        self.cursBtn.setPos(btnRect.width(), y)
        for idx, b in enumerate(self.btns.values()):
            b.setPos(btnRect.width() * (2 + idx), y)

    def updateCursorVals(self, c):
        if not self.customlegend.expanded:
            return
        c = c[0]
        try:
            xval = c.pos()[0]
        except RuntimeError:  # pragma: no cover # can happen during debugging
            return
        tmp = [xval]
        for cuidx, cu in enumerate(self.curves):
            try:
                idx = np.searchsorted(cu.xDisp, xval, side="left")
            except (ValueError, IndexError):
                return
            try:
                yval = cu.yDisp[idx]
            except IndexError:
                return
            tmp.append(yval)
        self.customlegend.setVals(c.idx, tmp)

    def toggleCursorVis(self, vis):
        if vis:
            self.customlegend.addCursorCols()
            for idx, c in enumerate(self.cursors.values()):
                pg.QtCore.QTimer.singleShot(0, partial(self.updateCursorVals, [c]))
        else:
            self.customlegend.remCursorCols()

    def plot(self, *args, **kwargs):
        p = super().plot(*args, **kwargs)
        self.customlegend.addItem(p, kwargs["name"])
        return p

    def addROI(self):
        self.roi = RelPosLinearRegion(self, self.roiChanged)
        self.roi.setRelRegion((0.4, 0.6))
        self.roi.setVisible(False)

    def addPlugins(self):
        self.btns = {}
        for plugin in plugins:
            b = pg.ButtonItem(icons.getIcon(plugin.iconName), width=14, parentItem=self)
            b.clicked.connect(partial(self.setPluginVisible, plugin.name))
            self.btns[plugin.name] = b

    def setPluginVisible(self, pluginName):
        if self.openPlugin == pluginName:
            self.roi.setVisible(False)
            self.hideSubPlot.emit()
            self.openPlugin = None
            return

        if self.openPlugin:
            self.hideSubPlot.emit()
        else:
            self.roi.setVisible(True)
        pg.QtCore.QTimer.singleShot(
            0, partial(self.showSubPlot.emit, (pluginName, self))
        )
        self.openPlugin = pluginName

    def fillSubPlot(self, args):
        type, datasrc = args
        self.subplotData["type"] = type
        self.subplotData["datasrc"] = datasrc
        self.createSubPlot()

    def createSubPlot(self):
        for plugin in plugins:
            if self.subplotData["type"] == plugin.name:
                self.subplotData["handler"] = plugin.PltHandler(self.subplotData, self)
                break

        self.subplotData["handler"].initialize()
        self.setVisible(True)
        self.roiChanged(self.subplotData["datasrc"].roi.getRegion())
        self.subplotData["datasrc"].cursBtn.clicked.connect(self.setCursorsVisible)
        if self.subplotData["datasrc"].customlegend.expanded:
            self.setCursorsVisible(None, True)

    def roiChanged(self, reg):
        if not self.isSubPlot:
            self.roiChangedSig.emit(reg.getRegion())
            return
        if not self.isVisible():
            return
        hdl = self.subplotData.get("handler")
        if hdl:
            hdl.updateData(reg)


class Plt(pg.GraphicsLayoutWidget):
    def __init__(self, data, **kwargs):
        super().__init__()
        if data.empty:
            return
        xdata = data.index.values
        xname = data.index.name if data.index.name else "idx"
        self.plt = PltItemWithCursors(xname)
        self.spacer = pg.LabelItem("")
        self.subPlt = None

        self.addItem(self.spacer, row=0, col=0)
        self.addItem(self.plt, row=1, col=0)
        self.plt.showSubPlot.connect(self.createSubPlot)
        self.plt.hideSubPlot.connect(self.destroySubPlot)

        L = len(data.columns)
        self.plt.setLabel("bottom", xname)
        for idx, yname in enumerate(data.columns):
            self.plt.plot(x=xdata, y=data[yname], name=yname, pen=(idx + 1, L))

    def createSubPlot(self, args):
        self.subPlt = PltItemWithCursors("", hasPlugins=False)
        self.plt.roiChangedSig.connect(self.subPlt.roiChanged)
        self.subPlt.setVisible(False)
        self.addItem(self.subPlt, row=2, col=0)
        self.ci.layout.setRowStretchFactor(2, 2)
        pg.QtCore.QTimer.singleShot(0, partial(self.subPlt.fillSubPlot, args))

    def destroySubPlot(self):
        if not self.subPlt:  # pragma: no cover #this can only happen in debugger
            return
        self.subPlt.setVisible(False)
        self.subPlt.deleteLater()
        self.subPlt = None


class LegendWithVals(pg.LegendItem):
    def __init__(self, xname, *args, **kwargs):
        kwargs["colCount"] = 1
        super().__init__(*args, **kwargs)
        self.layout.addItem(pg.LabelItem("Name"), 0, 1)
        self.layout.addItem(pg.LabelItem(" X"), 1, 0)
        self.layout.addItem(pg.LabelItem(xname), 1, 1)
        self.expanded = False
        self.w0 = None
        self.w1 = None

    def setVals(self, cursorIdx, vals):
        for vidx, v in enumerate(vals):
            targetItem = self.layout.itemAt(vidx + 1, cursorIdx + 2)
            targetItem._val = v

            targetItem.setText(getFixedLenString(v))
        if (
            self.layout.itemAt(1, 2)._val is not None
            and self.layout.itemAt(1, 3)._val is not None
        ):
            self.calcDerivativeVals()

    def calcDerivativeVals(self):
        for row in range(1, self.layout.rowCount()):
            v0 = self.layout.itemAt(row, 2)._val
            v1 = self.layout.itemAt(row, 3)._val
            delta = v1 - v0
            deltainv = 0 if delta == 0 else 1 / delta
            t = self.layout.itemAt(row, 4)
            t._val = delta
            t.setText(getFixedLenString(delta))
            t = self.layout.itemAt(row, 5)
            t._val = deltainv
            t.setText(getFixedLenString(deltainv))

    def addCursorCols(self):
        if self.expanded:
            return
        self.expanded = True
        if self.w0 is None:
            self.w0 = self.layout.geometry().width()

        self.layout.addItem(pg.LabelItem("C1"), 0, 2)
        self.layout.addItem(pg.LabelItem("C2"), 0, 3)
        self.layout.addItem(pg.LabelItem("Δ"), 0, 4)
        self.layout.addItem(pg.LabelItem("1/Δ"), 0, 5)

        for col in range(2, 6):
            self.layout.setColumnMaximumWidth(col, numValLen * 7)
            self.layout.setColumnMinimumWidth(col, numValLen * 7)

        if self.w1 is not None:
            self.setMaximumWidth(self.w1)

        for row in range(1, self.layout.rowCount()):
            for col in range(2, 6):
                item = pg.LabelItem("")
                item._val = None
                self.layout.addItem(item, row, col)

    def remCursorCols(self):
        if not self.expanded:
            return
        self.expanded = False
        if self.w1 is None:
            self.w1 = self.layout.geometry().width()

        self.layout.removeItem(self.layout.itemAt(0, 2))
        self.layout.removeItem(self.layout.itemAt(0, 3))
        self.layout.removeItem(self.layout.itemAt(0, 4))
        self.layout.removeItem(self.layout.itemAt(0, 5))

        for row in range(1, self.layout.rowCount()):
            for col in range(2, 6):
                self.layout.removeItem(self.layout.itemAt(row, col))

        if self.w0 is not None:
            self.setMaximumWidth(self.w0)

    def _addItemToLayout(self, sample, label):
        col = self.layout.columnCount()
        row = self.layout.rowCount()
        # in the original code, the next two lines are not commented out
        # if row:
        #    row -= 1
        # we need this bc we injected more rows and cols than in the original code
        if row == 2:
            col = 0
        else:
            col = 2

        nCol = self.columnCount * 2

        for col in range(0, nCol, 2):
            # FIND RIGHT COLUMN
            # if i dont add the row>=...,  get QGraphicsGridLayout::itemAt errors
            if row >= self.layout.rowCount() or not self.layout.itemAt(row, col):
                break

        self.layout.addItem(sample, row, col)
        self.layout.addItem(label, row, col + 1)
        # Keep rowCount in sync with the number of rows if items are added
        self.rowCount = max(self.rowCount, row + 1)


class RelPosCursor(pg.InfiniteLine):
    def __init__(self, startposrel, vertical=False, label=None):
        super().__init__(
            angle=90 if not vertical else 0,
            movable=True,
            label=label,
            labelOpts={"position": 0.95},
        )
        self.setVisible(False)
        self.startposrel = startposrel
        self.currposrel = startposrel
        self.vertical = vertical

    def setVisible(self, vis):
        if vis:
            self.setRelPos(self.startposrel)
        super().setVisible(vis)

    def setPos(self, pos):
        try:
            range = self.getViewBox().viewRange()
            x0, x1 = range[0] if not self.vertical else range[1]
            dx = x1 - x0
            self.currposrel = (pos - x0) / dx
        except AttributeError:
            pass
        super().setPos(pos)

    def setRelPos(self, relpos=None):
        if relpos is None:
            relpos = self.currposrel
        range = self.getViewBox().viewRange()
        x0, x1 = range[0] if not self.vertical else range[1]
        dx = x1 - x0
        self.setValue(x0 + relpos * dx)

    def viewTransformChanged(self):
        self.setRelPos()
        return super().viewTransformChanged()


class RelPosLinearRegion(pg.LinearRegionItem):
    def __init__(self, parent, updatefun):
        super().__init__()
        self.currRelRegion = [0.25, 0.75]
        self.updatefun = updatefun
        self.plt = parent
        self.setVisible(False)
        parent.addItem(self)
        self.sigRegionChanged.connect(updatefun)
        self.sigRegionChanged.connect(self.updateRelRegion)

    def setVisible(self, vis):
        if vis and not self.isVisible():
            ((x0, x1), (y0, y1)) = self.plt.viewRange()
            self.setRelRegion([0.25, 0.75])
        super().setVisible(vis)

    def updateRelRegion(self, _):
        reg = self.getRegion()
        x0, x1 = self.getViewBox().viewRange()[0]
        dx = x1 - x0
        self.currRelRegion = [(reg[0] - x0) / dx, (reg[1] - x0) / dx]

    def setRelRegion(self, relRegion=None):
        if relRegion is None:
            relRegion = self.currRelRegion
        x0, x1 = self.plt.viewRange()[0]
        dx = x1 - x0
        self.setRegion([x0 + dx * relRegion[0], x0 + dx * relRegion[1]])

    def setRegion(self, reg):
        x0, x1 = self.getViewBox().viewRange()[0]
        dx = x1 - x0
        self.currRelRegion = [(reg[0] - x0) / dx, (reg[1] - x0) / dx]
        super().setRegion(reg)

    def viewTransformChanged(self):
        self.setRelRegion()
        fn = partial(self.updatefun, self)
        pg.QtCore.QTimer.singleShot(0, fn)
        return super().viewTransformChanged()
