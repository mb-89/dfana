from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
class Ana(QtWidgets.QPushButton):
    name = "analysis placeholder"
    def __init__(self,parent):
        super().__init__(self.name)
        self.ana_widget = None
        self.ana_parent = parent
        self.setCheckable(True)
        self.shouldShowMeas = False
        self.clicked.connect(self.ana_show)

    def ana_show(self, show):
        setHidden = not show
        self.ana_widget.setHidden(setHidden)
        showmeas = self.shouldShowMeas
        self.ana_showMeas(showmeas)

    def ana_showMeas(self, show):
        self.shouldShowMeas = show
        try: self.ana_widget.showcursorsfun(self.shouldShowMeas and self.ana_widget.isVisible())
        except AttributeError:pass

    def ana_getWidget(self):
        if not self.ana_widget:
            self.ana_widget = QtWidgets.QLabel("plt",parent=self)
            self.ana_widget.setHidden(True)
        self.ana_showMeas(False)
        return self.ana_widget