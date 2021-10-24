import pyqtgraph as pg
import numpy as np
from functools import cache
from dfana import icons


class PltItemWithCursors(pg.PlotItem):
    cursorPosChanged = pg.QtCore.Signal(dict)
    cursorVisChanged = pg.QtCore.Signal(bool)

    def __init__(self, **kargs):
        super().__init__(**kargs)

        self.addCursors()

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
        self.cursBtn.clicked.connect(lambda x: self.setCursorsVisible())

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

    @cache
    def getValNameList(self):
        lst = [self.axes["bottom"]["item"].labelText] + [
            curve.name() for curve in self.curves
        ]
        return lst

    def updateCursorVals(self, c):
        if not self.isVisible():
            return
        c = c[-1]
        xval = c.pos()[0]
        try:
            yvals = tuple(
                curve.yData[np.searchsorted(curve.xData, xval, side="left")]
                for curve in self.curves
            )
            xy = (xval, *yvals)
        except IndexError:
            return
        dct = dict(zip(self.getValNameList(), xy))
        dct["#cidx"] = c.idx
        self.cursorPosChanged.emit(dct)


class Plt(pg.GraphicsLayoutWidget):
    def __init__(self, data, **kwargs):
        super().__init__()
        if data.empty:
            return
        xdata = data.index.values
        xname = data.index.name if data.index.name else "idx"
        self.plt = PltItemWithCursors()
        self.tbl = pg.LabelItem()
        self.tbl.setText("")
        self.tbl.datadict = {}
        self.tbl.dataready = False
        self.tbl.setAttr("justify", "left")
        plt = self.plt
        self.addItem(plt)
        self.addItem(self.tbl, row=1, col=0)
        self.tbl.setVisible(False)
        plt.cursorVisChanged.connect(self.toggleTableVis)
        plt.cursorPosChanged.connect(self.writeTable)

        plt.showGrid(1, 1, int(0.75 * 255))
        L = len(data.columns)
        plt.setLabel("bottom", xname)
        plt.addLegend()
        for idx, yname in enumerate(data.columns):
            plt.plot(x=xdata, y=data[yname], name=yname, pen=(idx + 1, L))

    def toggleTableVis(self, vis):
        self.tbl.setVisible(vis)

    def writeTable(self, data):
        cidx = data.pop("#cidx")
        self.tbl.datadict[cidx] = data
        if not self.tbl.dataready:
            self.tbl.dataready = len(self.tbl.datadict) > 1
            return
        html = (
            '<p align = "left"><table><tr><td style="padding-right:10px">'
            "</td><td>C1</td><td>C2</td><td>Δ</td><td>1/Δ</td></tr>"
        )

        for ((k1, v1), (k2, v2)) in zip(
            self.tbl.datadict[0].items(), self.tbl.datadict[1].items()
        ):
            delta = v2 - v1
            deltainv = 1.0 / delta if delta != 0.0 else 0.0
            html += "<tr>"
            html += f'<td style="padding-right:10px">{k1}</td>'
            html += f'<td style="padding-right:10px">{v1:.2f}</td>'
            html += f'<td style="padding-right:10px">{v2:.2f}</td>'
            html += f'<td style="padding-right:10px">{delta:.2f}</td>'
            html += f'<td style="padding-right:10px">{deltainv:.2f}</td>'
            html += "</tr>"

        html += "</table></p>"

        self.tbl.setText(html)


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
