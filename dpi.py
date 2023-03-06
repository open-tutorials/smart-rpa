import sys
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)
screen = app.screens()[0]
dpi = screen.physicalDotsPerInch()
app.quit()
