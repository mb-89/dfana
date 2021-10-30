import pyqtgraph as pg
import numpy as np
from functools import partial
from dfana import icons


class PltItemWithCursors(pg.PlotItem):
    cursorVisChanged = pg.QtCore.Signal(bool)

    def __init__(self, xname, **kargs):
        super().__init__(**kargs)
        A = 65
        self.customlegend = LegendWithVals(
            xname,
            pen=pg.mkPen(255, 255, 255, A),
            brush=pg.mkBrush(0, 0, 255, A),
            offset=(70, 20),
        )
        self.customlegend.setParentItem(self)
        self.addCursors()
        self.cursorVisChanged.connect(self.toggleCursorVis)

    def addCursors(self):
        self.cursBtn = pg.ButtonItem(icons.getIcon("cursor"), width=14, parentItem=self)

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
        self.cursBtn.clicked.connect(self.setCursorsVisible)

    def setCursorsVisible(self, vis=None):
        vis = vis if vis is not None else (not self.c1.isVisible())
        for k, v in self.cursors.items():
            v.setVisible(vis)
        self.cursorVisChanged.emit(vis)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if self.autoBtn is None:  # pragma: no cover # already closed down
            return
        btnRect = self.mapRectFromItem(self.autoBtn, self.autoBtn.boundingRect())
        y = self.size().height() - btnRect.height()
        self.cursBtn.setPos(btnRect.width(), y)

    def updateCursorVals(self, c):
        if not self.customlegend.expanded:
            return
        c = c[0]
        xval = c.pos()[0]
        tmp = [xval]
        for cuidx, cu in enumerate(self.curves):
            idx = np.searchsorted(cu.xDisp, xval, side="left")
            yval = cu.yDisp[idx]
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


class Plt(pg.GraphicsLayoutWidget):
    def __init__(self, data, **kwargs):
        super().__init__()
        if data.empty:
            return
        xdata = data.index.values
        xname = data.index.name if data.index.name else "idx"
        self.plt = PltItemWithCursors(xname)
        self.addItem(self.plt, row=0, col=0, colspan=4)
        self.plt.showGrid(1, 1, int(0.75 * 255))
        L = len(data.columns)
        self.plt.setLabel("bottom", xname)
        for idx, yname in enumerate(data.columns):
            self.plt.plot(x=xdata, y=data[yname], name=yname, pen=(idx + 1, L))


class LegendWithVals(pg.LegendItem):
    def __init__(self, xname, *args, **kwargs):
        kwargs["colCount"] = 1
        super().__init__(*args, **kwargs)
        self.layout.addItem(pg.LabelItem("Name"), 0, 1)
        self.layout.addItem(pg.LabelItem(xname), 1, 1)
        self.expanded = False
        self.w0 = None
        self.w1 = None
        self.valLen = 8

    def setVals(self, cursorIdx, vals):
        for vidx, v in enumerate(vals):
            targetItem = self.layout.itemAt(vidx + 1, cursorIdx + 2)
            targetItem._val = v

            targetItem.setText(self.getFixedLenString(v, self.valLen))
        if (
            self.layout.itemAt(1, 2)._val is not None
            and self.layout.itemAt(1, 3)._val is not None
        ):
            self.calcDerivativeVals()

    def getFixedLenString(self, flt, L):

        s = np.format_float_scientific(flt, precision=L - 5, trim="-")
        return s

    def calcDerivativeVals(self):
        for row in range(1, self.layout.rowCount()):
            v0 = self.layout.itemAt(row, 2)._val
            v1 = self.layout.itemAt(row, 3)._val
            delta = v1 - v0
            deltainv = 0 if delta == 0 else 1 / delta
            t = self.layout.itemAt(row, 4)
            t._val = delta
            t.setText(self.getFixedLenString(delta, self.valLen))
            t = self.layout.itemAt(row, 5)
            t._val = deltainv
            t.setText(self.getFixedLenString(deltainv, self.valLen))

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
            self.layout.setColumnMaximumWidth(col, self.valLen * 7)
            self.layout.setColumnMinimumWidth(col, self.valLen * 7)

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
