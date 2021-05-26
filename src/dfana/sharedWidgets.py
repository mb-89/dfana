from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import re
from defines import *
from functools import partial
import numpy as np

class DelegateWithSelectorMarker(QtWidgets.QStyledItemDelegate):
    def __init__(self):
        super().__init__()

    def paint(self, painter, option, index):
        sel = index.data(DATA_ISSELECTED)
        option.font.setUnderline(bool(sel))
        super().paint(painter, option, index)

class MdlRowSelector(QtWidgets.QWidget):
    groupCnt = 1
    def __init__(self, targetview, toggleSel=False):
        super().__init__()
        self.setLayout(self.buildSelRegexpLayout())
        self.targetview = targetview
        #if toggle sel is false, everytime the selection changes
        #all elements in the selection are cleared, and then the current
        #selection is applied
        #if toggle sel is true, elements are toggled in or out of the current selection
        self.toggleSel=toggleSel 
        self.setMaximumHeight(QtWidgets.QLineEdit().sizeHint().height()*min(self.groupCnt,5))
        try:self.targetview.updated.connect(self.updateSelRes)
        except AttributeError:pass
        self.setSelectionTrigger()

    def buildSelRegexpLayout(self):
        self.sels = []
        self.selresults = []
        l = QtWidgets.QVBoxLayout()
        l.setSpacing(0)
        l.setContentsMargins(0,0,0,0)
        w1 = QtWidgets.QScrollArea()
        self.scroller = w1
        w2 = QtWidgets.QWidget()
        w1.setWidget(w2)
        w1.setWidgetResizable(True)
        w1.setMaximumHeight(DEFAULT_H/3)
        l.addWidget(w1)
        l1 = QtWidgets.QVBoxLayout()
        l1.setSpacing(0)
        l1.setContentsMargins(0,0,0,0)
        w2.setLayout(l1)
        for idx in range(self.groupCnt):
            l2 = QtWidgets.QHBoxLayout()
            l2.setSpacing(0)
            l2.setContentsMargins(0,0,0,0)
            sel = QtWidgets.QLineEdit()
            sel.setPlaceholderText(f"<selector expr grp{idx}>")
            selresult = QtWidgets.QLabel("0/0 selected")
            selresult.setMaximumWidth(150)
            l2.addWidget(sel)
            l2.addWidget(selresult)
            fn = partial(self.setSelected,None,None,targetGrp=idx)
            sel.textEdited.connect(fn)
            self.sels.append(sel)
            self.selresults.append(selresult)
            l1.addLayout(l2)
        return l

    def setSelRegexp(self,regexp=None,targetGrp=0):
        if regexp is None:
            idxs = [x for x in self.targetview.selectedIndexes() if x.column()==0]
            self.scroller.ensureWidgetVisible(self.sels[targetGrp])
            tmp = []
            for idx in idxs:
                currentsel = idx.data(DATA_ISSELECTED)
                if currentsel is None:
                    currentsel = set()
                if (targetGrp not in currentsel) or not self.toggleSel:
                    tmp.append(idx.data(0))
                elif (targetGrp in currentsel) and self.toggleSel:
                    tmp.append(idx.data(0))
            if tmp: regexp = "(" + "|".join(sorted(x for x in tmp))+")"
            else: regexp=""
        self.sels[targetGrp].setText(regexp)

    def getSelRegexp(self,targetGrp):
        return self.sels[targetGrp].text()

    def parseSelRegexp(self, targetGrp=0):
        regexp = self.getSelRegexp(targetGrp)
        root = self.targetview.mdl.invisibleRootItem()
        allElems = dict((root.child(row,0).text(),root.child(row,1).text()) for row in range(root.rowCount()))
        def matchNotEmpty(regexp,str):
            try:
                match = re.findall(regexp,str,flags=re.IGNORECASE)
                return match and match[0]
            except:
                return False
        dfs = set(k for k,v in allElems.items() if (matchNotEmpty(regexp,k) or matchNotEmpty(regexp,v)) )
        for idx,(c0,c1,c2) in enumerate(self.elems()):
            selected = c0.text() in dfs

            if self.toggleSel:
                currentsel = c0.data(DATA_ISSELECTED)
                if currentsel is None:
                    currentsel = set()
                currentsel.discard(targetGrp)
            else:
                currentsel = set()
            if selected:
                currentsel.add(targetGrp)
            if c2:
                if currentsel:  c2.setText(str(sorted(tuple(currentsel))))
                else:           c2.setText("")
            c0.setData(currentsel,DATA_ISSELECTED)
            c1.setData(currentsel,DATA_ISSELECTED)
            if c2:c2.setData(currentsel,DATA_ISSELECTED)
        self.updateSelRes(targetGrp)

    def setSelectionTrigger(self):
        self.targetview.selectionModel().selectionChanged.connect(self.setSelected)

    def setSelected(self, selected=None, deselected=None, regexp=None, targetGrp=0):
        self.setSelRegexp(regexp,targetGrp=targetGrp)
        self.parseSelRegexp(targetGrp)

    def unselect(self,targetGrp=0):
        pass #TODO (maybe later)
    def elems(self):
        root = self.targetview.mdl.invisibleRootItem()
        for row in range(root.rowCount()):
            yield (root.child(row,0),root.child(row,1),root.child(row,2))

    def getSelected(self, targetGrp=0):
        idxs = [x for x,_,_ in self.elems() if x.data(DATA_ISSELECTED) and targetGrp in x.data(DATA_ISSELECTED)]
        return idxs

    def getSelectedIdxs(self):
        dct = {}
        idxs = [x for x,_,_ in self.elems() if x.data(DATA_ISSELECTED)]
        for idx in idxs:
            dct[idx.data(0)] = idx.data(DATA_ISSELECTED)
        return dct


    def updateSelRes(self, targetGrp=None):
        if targetGrp is None:
            for idx in range(self.groupCnt):
                self.updateSelRes(idx)
            return
        L = self.targetview.mdl.rowCount()
        sel = self.getSelected(targetGrp)
        self.selresults[targetGrp].setText(f"{len(sel)}/{L} selected")
        self.targetview.repaint()

class MdlRowMultiSelector(MdlRowSelector):
    groupCnt = 10
    def setSelectionTrigger(self):
        self.targetview._keyPressEvent = self.targetview.keyPressEvent
        self.targetview.keyPressEvent = lambda x: self.keyPressOverride(x)

    def keyPressOverride(self, event):
        key=event.key()
        ctrl = (event.modifiers() == QtCore.Qt.ControlModifier)
        if key >= QtCore.Qt.Key_0 and key <= QtCore.Qt.Key_9:
            if ctrl: self.unselect(targetGrp=key-QtCore.Qt.Key_0)
            else: self.setSelected(targetGrp=key-QtCore.Qt.Key_0)
        self.targetview._keyPressEvent(event)

# https://learndataanalysis.org/display-pandas-dataframe-with-pyqt5-qtableview-widget/
class DFview(QtWidgets.QTableView):
    def __init__(self, df):
        super().__init__()
        mdl=pandasModel(df)
        self.setModel(mdl)
        self.resize(1000, 600)
        self.resizeColumnsToContents()
        self.horizontalHeader().setStretchLastSection(1)

class pandasModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        QtCore.QAbstractTableModel.__init__(self)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parnet=None):
        return self._data.shape[1]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._data.columns[col]
        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return self._data.index[col]
        return None

class RelPosCursor(pg.InfiniteLine):
    def __init__(self, startposrel, vertical = False):
        super().__init__(angle=90 if not vertical else 0,movable=True)
        self.setVisible(False)
        self.startposrel = startposrel
        self.currposrel = startposrel
        self.vertical = vertical
    def setVisible(self, vis):
        if vis:self.setRelPos(self.startposrel)
        super().setVisible(vis)
    def setPos(self,pos):
        try:
            range = self.getViewBox().viewRange()
            x0,x1 = range[0] if not self.vertical else range[1]
            dx = x1-x0
            self.currposrel = (pos-x0)/dx
        except AttributeError:
            pass
        super().setPos(pos)

    def setRelPos(self, relpos=None):
        if relpos is None: relpos = self.currposrel
        range = self.getViewBox().viewRange()
        x0,x1 = range[0] if not self.vertical else range[1]
        dx = x1-x0
        self.setValue(x0+relpos*dx)

    def viewTransformChanged(self):
        self.setRelPos()
        return super().viewTransformChanged()
        
class RelPosLinearRegion(pg.LinearRegionItem):
    def __init__(self,parent,updatefun):
        super().__init__()
        self.currRelRegion = [.25,.75]
        self.updatefun = updatefun
        self.plt = parent
        self.setVisible(False)
        parent.addItem(self)
        self.sigRegionChanged.connect(updatefun)
        self.sigRegionChanged.connect(self.updateRelRegion)
        
    def setVisible(self, vis):
        if vis and not self.isVisible():
            ((x0,x1),(y0,y1)) = self.plt.viewRange()
            self.setRelRegion([.25,.75])
        super().setVisible(vis)

    def updateRelRegion(self,_):
        reg = self.getRegion()
        x0,x1 = self.getViewBox().viewRange()[0]
        dx = x1-x0
        self.currRelRegion = [(reg[0]-x0)/dx, (reg[1]-x0)/dx]

    def setRelRegion(self, relRegion=None):
        if relRegion is None: relRegion = self.currRelRegion
        x0,x1 = self.plt.viewRange()[0]
        dx = x1-x0
        self.setRegion([x0+dx*relRegion[0], x0+dx*relRegion[1]])

    def setRegion(self, reg):
        x0,x1 = self.getViewBox().viewRange()[0]
        dx = x1-x0
        self.currRelRegion = [(reg[0]-x0)/dx, (reg[1]-x0)/dx]
        super().setRegion(reg)

    def viewTransformChanged(self):
        self.setRelRegion()
        fn = partial(self.updatefun, self)
        QtCore.QTimer.singleShot(0, fn)
        return super().viewTransformChanged()

class PlotWithMeasWidget(QtWidgets.QWidget):
    def __init__(self,parent=None):
        super().__init__(parent=parent)
        self.pw = pg.PlotWidget()
        self.pi = self.getPlotItem()
        self.meas = MeasWidget(self.pi)
        self.pw.showcursorsfun = lambda s: self.showcursorsfun(s)

        l = QtWidgets.QGridLayout()
        l.setSpacing(0)
        l.setContentsMargins(0,0,0,0)
        self.setLayout(l)
        l.addWidget(self.pw,0,0)
        l.addWidget(self.meas,0,1)
        l.setColumnStretch(0,39)
        l.setColumnStretch(1,0)
        self.showCursors = False
        self.l = l

    def showcursorsfun(self, show):
        self.showCursors = show
        if self.showCursors:    self.l.setColumnStretch(1,10)
        else:                   self.l.setColumnStretch(1,0)
        self.meas.setHidden(not self.showCursors)

    def getPlotItem(self):
        return self.pw.getPlotItem()


class MeasWidget(QtWidgets.QTableWidget):
    def __init__(self, plt, name = "meas"):
        super().__init__()
        self.plt = plt
        self.wname = name
        f = self.font()
        f.setPointSize(10)
        self.setFont(f)
        self.c1 = RelPosCursor(1/3)
        self.c2 = RelPosCursor(2/3)
        self.plt.addItem(self.c1)
        self.plt.addItem(self.c2)
        self.cursors=dict((idx,c) for idx,c in enumerate([self.c1,self.c2]))
        self.setHidden(True)
        self.proxies = [pg.SignalProxy(c.sigPositionChanged, rateLimit=30, slot=self.updateVals) for c in self.cursors.values()]
        self.values = dict((x,tuple()) for x,_ in enumerate(self.cursors))
        for k,v in self.cursors.items():
            v.idx = k

    def setHidden(self, hidden):
        vis = not hidden
        if vis:self.buildMeasTable()
        self.c1.setVisible(vis)
        self.c2.setVisible(vis)
        super().setHidden(hidden)

    def buildMeasTable(self):
        if self.plt.curves and self.rowCount(): return
        rows = len(self.plt.curves)+1
        cols = 4
        self.setRowCount(rows)
        self.setColumnCount(cols)
        for row in range(rows):
            for col in range(cols):
                item = QtWidgets.QTableWidgetItem()
                self.setItem(row,col,item)
        for col in range(cols):
            self.setColumnWidth(col,75)
        self.setHorizontalHeaderLabels(["c1","c2","Δ","1/Δ"])
        self.setVerticalHeaderLabels(["x"]+[f"y{idx}" for idx in range(rows-1)])

    def updateVals(self,c):
        if self.isHidden():return
        c = c[-1]
        xval = c.pos()[0]
        yvals = tuple(curve.yData[np.searchsorted(curve.xData, xval, side="left")] for curve in self.plt.curves)
        self.values[c.idx] = (xval,*yvals)
        if self.values[0] and self.values[1]:
            self.values["delta"] = np.array(self.values[1])-np.array(self.values[0])
            with np.errstate(divide='ignore'):
                tmp = np.ones_like(self.values["delta"])/self.values["delta"]
            self.values["deltainv"] = np.nan_to_num(tmp)
        else:
            self.values["delta"] = (0,0)
            self.values["deltainv"] = (0,0)
        self.updateText()
    def updateText(self):
            for col,colvals in enumerate(self.values.values()):
                for row,val in enumerate(colvals):
                    self.item(row,col).setText(f"{val:.2e}")

class ImageMeasWidget(QtWidgets.QWidget):
    def __init__(self, plt, name = "meas"):
        super().__init__()
        self.plt = plt
        self.wname = name
        f = self.font()
        f.setPointSize(10)
        self.setFont(f)
        self.c1 = RelPosCursor(0.5)
        self.c2 = RelPosCursor(0.5, vertical=True)
        self.plt.addItem(self.c1)
        self.plt.addItem(self.c2)
        self.cursors=dict((idx,c) for idx,c in enumerate([self.c1,self.c2]))
        self.setHidden(True)
        self.values = dict((x,tuple()) for x,_ in enumerate(self.cursors))
        for k,v in self.cursors.items():
            v.idx = k
        self.proxy = pg.SignalProxy(self.plt.scene().sigMouseMoved, rateLimit=30, slot=self.mouseMoved)
        self.l = QtWidgets.QVBoxLayout()
        self.table = QtWidgets.QTableWidget()
        self.table.setMinimumHeight(75)
        self.l.addWidget(self.table)
        self.buildMeasTable()
        self.xplt = pg.PlotWidget(labels={"bottom":"x","left":"z"})
        self.yplt = pg.PlotWidget(labels={"bottom":"y","left":"z"})
        self.l.addWidget(self.yplt)
        self.l.addWidget(self.xplt)
        self.l.setSpacing(20)
        self.l.setContentsMargins(0,0,0,0)
        self.setLayout(self.l)

    def buildMeasTable(self):
        rows=1
        cols=3
        t = self.table
        t.setRowCount(rows)
        t.setColumnCount(cols)
        for row in range(rows):
            for col in range(cols):
                item = QtWidgets.QTableWidgetItem()
                t.setItem(row,col,item)
        for col in range(cols):
            t.setColumnWidth(col,75)
        t.setHorizontalHeaderLabels(["x","y","z"])
        t.setVerticalHeaderLabels(["val"])

    def mouseMoved(self,evt):
        if not self.isVisible():return
        pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        if not self.plt.sceneBoundingRect().contains(pos):return
        mousePoint = self.plt.vb.mapSceneToView(pos)
        self.c1.setPos(mousePoint.x())
        self.c2.setPos(mousePoint.y())
        scenePos = self.plt.items[0].mapFromScene(pos)
        data = self.plt.items[0].image
        nRows, nCols = data.shape 
        row, col = int(scenePos.y()), int(scenePos.x())
        if (0 <= row < nRows) and (0 <= col < nCols):
                x = mousePoint.x()
                y = mousePoint.y()
                z = data[row, col]
                self.table.item(0,0).setText(f"{x:.2e}")
                self.table.item(0,1).setText(f"{y:.2e}")
                self.table.item(0,2).setText(f"{z:.2e}")
                self.xplt.clear()
                self.yplt.clear()
                self.xplt.plot(data[row, :])
                self.xplt.addItem(pg.InfiniteLine(col))
                self.yplt.plot(data[:, col])
                self.yplt.addItem(pg.InfiniteLine(row))

    def setHidden(self, hidden):
        vis = not hidden
        self.c1.setVisible(vis)
        self.c2.setVisible(vis)
        super().setHidden(hidden)
