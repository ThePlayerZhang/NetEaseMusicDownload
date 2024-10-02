import os
import sys

from PyQt5 import QtWidgets, QtGui

from PyQtUI import MainWindow, DownloadButton, DownloadWindow
from Modle import *


def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        # noinspection PyProtectedMember
        base_path = sys._MEIPASS
    else:
        base_path = "./"
    ret_path = os.path.join(base_path, relative_path)
    return ret_path


class DownloadingUI(QtWidgets.QMainWindow, DownloadWindow.Ui_MainWindow):
    def __init__(self):
        super().__init__()


class DownloadButtonUI(QtWidgets.QMainWindow, DownloadButton.Ui_MainWindow):
    def __init__(self, app):
        super().__init__()

        self.main_window = MainWindowUI()
        self.download_window = DownloadWindowUI()

        # 初始化UI
        self.setObjectName("MainWindow")

        self.setupUi(self)

        self.filename = resource_path(os.path.join("res/icon.png"))

        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        self.tray_icon.setIcon(QtGui.QIcon(self.filename))
        self.tray_menu = QtWidgets.QMenu()
        self.tray_action = []
        self.add_action('打开主界面', self.main_window.show)
        self.add_action('退出', app.exit)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

        self.menuBut.clicked.connect(self.main_window.show)
        self.downloadBut.clicked.connect(self.download_action)

        self.setWindowTitle("cloud_music_down")

        self.setWindowFlags(QtCore.Qt.WindowType.SplashScreen)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

        self.downloadBut.hide()
        self.menuBut.hide()
        # 初始化线程
        self.visible_and_move = VisibleAndMove()
        self.clipboard = Clipboard()
        self.visible_and_move.start()
        self.clipboard.start()

    def download_action(self):
        self.download_window.start(self.clipboard.data)

    def add_action(self, text='empty', callback=None):
        action = QtWidgets.QAction(text, self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(callback)
        self.tray_menu.addAction(action)


class MainWindowUI(QtWidgets.QMainWindow, MainWindow.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.filename = resource_path(os.path.join("res/icon.png"))

        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(self.filename))
        self.setWindowTitle("网易云音乐歌曲本地化助手")

    def closeEvent(self, event):
        event.ignore()
        self.hide()


class DownloadWindowUI(QtWidgets.QMainWindow, MainWindow.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.filename = resource_path(os.path.join("res/icon.png"))
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(self.filename))
        self.setWindowTitle("网易云音乐歌曲本地化助手")
        self.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)

        self.pushButton.hide()
        self.lineEdit.hide()
        self.label.hide()

        self.download = None
        self.downloading = False
        self.download_window = DownloadingUI()
        self.pushButton.clicked.connect(self.start_download)

    def start(self, download_url):
        self.pushButton.show()
        self.toolButton.show()
        self.lineEdit.show()
        self.progressBar.hide()
        self.download = Download(download_url)
        urls, names = self.download.get_urls()
        print(urls, names)
        self.link.setText(" ".join(urls))
        self.name.setText(" ".join(names))
        self.download.finish.connect(self.finnish_download)
        self.show()

    def finnish_download(self):
        self.downloading = False

    def start_download(self):
        self.downloading = True
        self.pushButton.hide()
        self.toolButton.hide()
        self.lineEdit.hide()
        self.progressBar.show()
        self.download.start()

    def closeEvent(self, event):
        event.ignore()
        if not self.downloading:
            self.hide()
