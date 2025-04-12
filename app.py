import ctypes
import os
import sys

from main_window import MainWindow
from PySide6 import QtWidgets


os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=0"  # disable dark mode support
myAppID = u'awakedom.gapthicknessplotter.1.0'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myAppID)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())