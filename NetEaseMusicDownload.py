from WindowUI import *
from PyQt5 import QtWidgets


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = DownloadButtonUI(app)
    window.show()
    sys.exit(app.exec_())
