from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
class Ana(QtWidgets.QPushButton):
    name = "analysis placeholder"
    def __init__(self,parent):
        super().__init__(self.name)
        self.ana_pltw = None
        self.ana_parent = parent
        self.ana_measw = None
        self.clicked.connect(self.ana_toggle)
    def ana_toggle(self):
        setHidden = not self.ana_pltw.isHidden()
        self.ana_pltw.setHidden(setHidden)
        self.ana_measw.setHidden(setHidden)
    def ana_toggleMeas(self):
        self.ana_measw.toggle(self.ana_pltw.isVisible() and not self.ana_measw.isVisible())

    def ana_getPlotWidget(self):
        if not self.ana_pltw:
            self.ana_pltw = QtWidgets.QLabel("plt",parent=self)
            self.ana_pltw.setHidden(True)
        return self.ana_pltw
    def ana_getMeasWidget(self):
        if not self.ana_measw:
            self.ana_measw = QtWidgets.QLabel("meas",parent=self)
            self.ana_measw.setHidden(True)
        return self.ana_measw