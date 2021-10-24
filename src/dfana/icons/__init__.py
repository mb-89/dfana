from functools import cache
from pyqtgraph import QtGui
import os.path as op


@cache
def getIcon(name, size=(20, 20)):
    icon = QtGui.QIcon(op.join(op.dirname(__file__), name + ".png"))
    return icon.pixmap(*size)
