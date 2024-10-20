from PyQt5 import QtGui

from PyQtUI import MainWindow, DownloadButton
from Modle import *


class DownloadButtonUI(QtWidgets.QMainWindow, DownloadButton.Ui_MainWindow):
    def __init__(self, app):
        super().__init__()

        # 加载主窗体
        self.main_window = MainWindowUI()

        # 初始化UI
        self.setObjectName("MainWindow")

        # 「UI，启动！（bushi）」
        self.setupUi(self)

        self.filename = resource_path(os.path.join("res/icon.png"))  # 加载窗体图标

        # 加载任务栏小图标
        # 「这部分代码还是来自某四字网站，反正能跑」
        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        self.tray_icon.setIcon(QtGui.QIcon(self.filename))
        self.tray_menu = QtWidgets.QMenu()
        self.tray_action = []
        self.add_action('打开主界面', self.main_window.show)
        self.add_action('退出', app.exit)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

        # 链接按钮消息
        self.menuBut.clicked.connect(self.main_window.show)
        self.downloadBut.clicked.connect(self.download_action)

        self.setWindowTitle("cloud_music_down")  # 设置标题

        # 设置窗不在任务栏中显示、体始终在上和透明
        self.setWindowFlags(QtCore.Qt.WindowType.SplashScreen |
                            QtCore.Qt.WindowType.WindowStaysOnTopHint |
                            QtCore.Qt.WindowType.FramelessWindowHint)
        # 设置透明背景
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        # 隐藏所有按键
        self.downloadBut.hide()
        self.menuBut.hide()
        # 初始化线程
        self.visible_and_move = VisibleAndMove()
        self.clipboard = Clipboard()
        self.visible_and_move.start()
        self.clipboard.start()
        # 绑定各种消息
        self.visible_and_move.menuBut_show.connect(self.menuBut.show)
        self.visible_and_move.menuBut_hide.connect(self.menuBut.hide)
        self.visible_and_move.downloadBut_show.connect(self.downloadBut.show)
        self.visible_and_move.downloadBut_hide.connect(self.downloadBut.hide)
        self.visible_and_move.move.connect(lambda pos: self.move(pos[0], pos[1]))
        self.clipboard.update.connect(self.update_clipboard)

    def download_action(self):
        self.main_window.show_with_data(self.clipboard.data)

    def update_clipboard(self, data):
        self.visible_and_move.clipboard = data

    def add_action(self, text='empty', callback=None):
        action = QtWidgets.QAction(text, self)
        # noinspection PyUnresolvedReferences
        # 「每日connect报错（1/无限）」
        action.triggered.connect(callback)
        self.tray_menu.addAction(action)


class MainWindowUI(QtWidgets.QMainWindow, MainWindow.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.filename = resource_path(os.path.join("res/icon.png"))
        # 「UI，启动！（梅开二度）」
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(self.filename))
        self.setWindowTitle("网易云音乐歌曲本地化助手")
        self.GET_URL = GetUrl("")
        self.temp_urls = []
        self.urls = []

        self.pushButton.clicked.connect(lambda: self.get_url(self.lineEdit.text()))

    def show(self):
        self.pushButton.setDisabled(False)
        self.pushButton_2.setDisabled(False)
        super().show()

        self.urls = []
        self.reload()
        self.label_3.setText("")
        self.GET_URL.stop = True
        self.GET_URL.wait()

    def show_with_data(self, data):
        self.urls = []
        self.get_url(data)
        super().show()

    def get_url(self, data):
        self.lineEdit.setText("")
        self.temp_urls = []
        self.reload()

        self.label_3.setText("")
        self.label_3.show()  # 显示加载中标签
        self.pushButton.setDisabled(True)
        self.pushButton_2.setDisabled(True)

        self.GET_URL.stop = True
        self.GET_URL.wait()  # 退出上一个获取名称线程
        self.GET_URL = GetUrl(data)  # 初始化获取名称线程

        # 绑定获取完毕信号
        self.GET_URL.finnish.connect(self.finnish_getting_urls)
        # 绑定加载中标签更新信号
        self.GET_URL.loading.connect(self.loading_urls)

        # 启动线程
        self.GET_URL.start()

    def loading_urls(self, string, urls):
        self.label_3.setText(string)
        self.temp_urls = self.urls + urls
        self.reload(True)

    def finnish_getting_urls(self, urls):
        self.label_3.hide()  # 隐藏加载中标签
        self.pushButton.setDisabled(False)
        self.pushButton_2.setDisabled(False)

        self.urls = self.urls + urls
        self.reload()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def reload(self, disabled=False):

        if disabled:
            urls = self.temp_urls
        else:
            urls = self.urls

        self.tableWidget.setRowCount(len(urls))
        self.tableWidget.setColumnCount(3)

        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self.tableWidget.horizontalHeader().setVisible(False)
        self.tableWidget.setShowGrid(False)

        width = self.tableWidget.width()
        self.tableWidget.setColumnWidth(0, int(width * 0.25))
        self.tableWidget.setColumnWidth(1, int(width * 0.6))
        self.tableWidget.setColumnWidth(2, int(width * 0.075))

        self.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior(1))

        for i in range(len(urls)):
            item = QtWidgets.QTableWidgetItem(urls[i][1])
            item.setToolTip(urls[i][1])
            self.tableWidget.setItem(i, 0, item)
            item = QtWidgets.QTableWidgetItem(f"https://music.163.com/song?id={urls[i][0]}")
            item.setToolTip(f"https://music.163.com/song?id={urls[i][0]}")
            self.tableWidget.setItem(i, 1, item)
            self.tableWidget.setCellWidget(i, 2, SmartButton("删除", self.delete, i, disabled))

    def delete(self, task_id):
        self.urls.pop(task_id)
        self.reload()
