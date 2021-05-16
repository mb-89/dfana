from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import re

class MdlRowSelector(QtWidgets.QWidget):
    def __init__(self, targetview):
        super().__init__()
        l = QtWidgets.QHBoxLayout()
        l.setSpacing(0)
        l.setContentsMargins(0,0,0,0)
        self.setLayout(l)
        self.sel = QtWidgets.QLineEdit()
        self.sel.setPlaceholderText("<selector expr>")
        self.selresult = QtWidgets.QLabel("0/0 selected")
        self.selresult.setMaximumWidth(150)
        l.addWidget(self.sel)
        l.addWidget(self.selresult)
        self.ignoreSelChanges = False
        self.sel.textEdited.connect(self.setSelected)
        self.targetview = targetview
        try:self.targetview.updated.connect(self.updateSelRes)
        except AttributeError:pass
        self.targetview.selectionModel().selectionChanged.connect(self.updateSelRes)

    def setSelected(self,regexp):
        root = self.targetview.mdl.invisibleRootItem()
        allElems = dict((root.child(row,0).text(),root.child(row,1).text()) for row in range(root.rowCount()))
        def matchNotEmpty(regexp,str):
            try:
                match = re.findall(regexp,str,flags=re.IGNORECASE)
                return match and match[0]
            except:
                return False
        dfs = set(k for k,v in allElems.items() if (matchNotEmpty(regexp,k) or matchNotEmpty(regexp,v)) )
        
        selection = self.targetview.selectionModel()
        self.ignoreSelChanges=True
        selection.clear()
        for row in range(root.rowCount()):
            ch = root.child(row)
            if ch.data(0) in dfs:
                selection.select(ch.index(), QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows)
        self.ignoreSelChanges=False

    def getSelected(self):
        idxs = [x for x in self.targetview.selectedIndexes() if x.column()==0]
        return idxs

    def updateSelRes(self):
        L = self.targetview.mdl.rowCount()
        sel = self.getSelected()
        self.selresult.setText(f"{len(sel)}/{L} selected")
        if not self.ignoreSelChanges:
            regexp = "(" + "|".join(sorted(x.data(0) for x in sel))+")"
            if sel:self.sel.setText(regexp)
            else:self.sel.setText("")