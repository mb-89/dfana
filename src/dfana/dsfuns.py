from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
from defines import *
import pyqtgraph.dockarea as da
import logging
log = logging.getLogger()

class DataSeriesDock(da.Dock):
    def __init__(self):
        super().__init__("DataSeries", size=(DEFAULT_W/3,DEFAULT_H/5))
        self.setStretch(x=DEFAULT_W/3,y=DEFAULT_H/5)
        self.list = QtWidgets.QTreeView()
        self.filt = QtWidgets.QLineEdit()
        self.filt.setPlaceholderText("<ds filter expr>")
        self.addWidget(self.list,row=0,col=0)
        self.addWidget(self.filt,row=1,col=0)