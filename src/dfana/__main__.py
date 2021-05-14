import dfana
from qt_material import apply_stylesheet

app = dfana.pg.mkQApp("dfana")
win = dfana.QtGui.QMainWindow()
apply_stylesheet(app, theme='dark_teal.xml')
area = dfana.DockArea()
win.setCentralWidget(area)
win.resize(dfana.DEFAULT_W,dfana.DEFAULT_H)
area.addWidgets()
win.setWindowTitle('dfana')
win.show()
dfana.pg.mkQApp().exec()