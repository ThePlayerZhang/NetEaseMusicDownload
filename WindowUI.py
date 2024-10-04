import os
import sys

from PyQt5 import QtGui

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
        self.visible_and_move.menuBut_show.connect(self.menuBut.show)
        self.visible_and_move.menuBut_hide.connect(self.menuBut.hide)
        self.visible_and_move.downloadBut_show.connect(self.downloadBut.show)
        self.visible_and_move.downloadBut_hide.connect(self.downloadBut.hide)
        self.visible_and_move.move.connect(self.move_to)
        self.clipboard.update.connect(self.update_clipboard)

    def download_action(self):
        self.main_window.show_with_data(self.clipboard.data)

    def update_clipboard(self, data):
        self.visible_and_move.clipboard = data

    def add_action(self, text='empty', callback=None):
        action = QtWidgets.QAction(text, self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(callback)
        self.tray_menu.addAction(action)

    def move_to(self, pos):
        self.move(pos[0], pos[1])


class MainWindowUI(QtWidgets.QMainWindow, MainWindow.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.filename = resource_path(os.path.join("res/icon.png"))

        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(self.filename))
        self.setWindowTitle("网易云音乐歌曲本地化助手")
        self.url = GetUrl("")
        self.urls = []

    def show_with_data(self, url):
        self.urls = []
        self.reload()
        self.label_3.setText("")
        self.label_3.show()  # 显示加载中标签
        self.url.quit()  # 退出上一个获取名称线程
        self.url = GetUrl(url)  # 初始化获取名称线程

        # 绑定获取完毕信号
        self.url.finnish.connect(self.get_urls)
        # 绑定加载中标签更新信号
        self.url.loading.connect(lambda string: self.label_3.setText(string))

        # 启动线程
        self.url.start()
        self.show()

    def get_urls(self, urls):
        self.label_3.hide()  # 隐藏加载中标签
        self.urls = urls
        self.reload()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def reload(self):
        self.tableWidget.setRowCount(len(self.urls))
        self.tableWidget.setColumnCount(3)

        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self.tableWidget.horizontalHeader().setVisible(False)
        self.tableWidget.setShowGrid(False)

        width = self.tableWidget.width()
        self.tableWidget.setColumnWidth(0, int(width * 0.25))
        self.tableWidget.setColumnWidth(1, int(width * 0.6))
        self.tableWidget.setColumnWidth(2, int(width * 0.075))

        self.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior(1))

        for i in range(len(self.urls)):
            item = QtWidgets.QTableWidgetItem(self.urls[i][1])
            item.setToolTip(self.urls[i][1])
            self.tableWidget.setItem(i, 0, item)
            item = QtWidgets.QTableWidgetItem(f"https://music.163.com/song?id={self.urls[i][0]}")
            item.setToolTip(f"https://music.163.com/song?id={self.urls[i][0]}")
            self.tableWidget.setItem(i, 1, item)
            self.tableWidget.setCellWidget(i, 2, SmartButton("删除", self.delete, i))

    def delete(self, task_id):
        self.urls.pop(task_id)
        self.reload()


# class DownloadWindowUI(QtWidgets.QMainWindow, MainWindow.Ui_MainWindow):
#     def __init__(self):
#         super().__init__()
#         self.filename = resource_path(os.path.join("res/icon.png"))
#         self.setupUi(self)
#         self.setWindowIcon(QtGui.QIcon(self.filename))
#         self.setWindowTitle("网易云音乐歌曲本地化助手")
#         self.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
#
#         self.pushButton.hide()
#         self.lineEdit.hide()
#         self.label.hide()
#
#         self.download = None
#         self.downloading = False
#         self.download_window = DownloadingUI()
#         self.pushButton.clicked.connect(self.start_download)
#
#     def start(self, download_url):
#         self.pushButton.show()
#         self.toolButton.show()
#         self.lineEdit.show()
#         self.progressBar.hide()
#         self.download = Download(download_url)
#         urls, names = self.download.get_urls()
#         print(urls, names)
#         self.link.setText(" ".join(urls))
#         self.name.setText(" ".join(names))
#         self.download.finish.connect(self.finnish_download)
#         self.show()
#
#     def finnish_download(self):
#         self.downloading = False
#
#     def start_download(self):
#         self.downloading = True
#         self.pushButton.hide()
#         self.toolButton.hide()
#         self.lineEdit.hide()
#         self.progressBar.show()
#         self.download.start()
#
#     def closeEvent(self, event):
#         event.ignore()
#         if not self.downloading:
#             self.hide()
