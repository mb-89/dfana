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
    def __init__(self, startposrel):
        super().__init__(angle=90,movable=True)
        self.setVisible(False)
        self.startposrel = startposrel
        self.currposrel = startposrel
    def toggle(self):
        willbevisible = not self.isVisible()
        if willbevisible:
            self.setRelPos(self.startposrel)
        self.setVisible(willbevisible)
    def setPos(self,pos):
        try:
            x0,x1 = self.getViewBox().viewRange()[0]
            dx = x1-x0
            self.currposrel = (pos-x0)/dx
        except AttributeError:
            pass

        super().setPos(pos)

    def setRelPos(self, relpos=None):
        if relpos is None: relpos = self.currposrel
        x0,x1 = self.getViewBox().viewRange()[0]
        dx = x1-x0
        self.setValue(x0+relpos*dx)

    def viewTransformChanged(self):
        self.setRelPos()
        return super().viewTransformChanged()

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

    def toggle(self, becomeVisible=None):
        if becomeVisible is None: becomeVisible = self.isHidden()
        if becomeVisible:
            self.buildMeasTable()
        self.c1.toggle()
        self.c2.toggle()
        self.setHidden(not becomeVisible)

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