import random
import re
import time

import psutil
import pywintypes
import requests
import win32clipboard
import win32con
import win32gui
import win32process
from PyQt5 import QtCore
from lxml import html

from Useragent import useragent


class Clipboard(QtCore.QThread):
    
    update = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # 剪贴板数据
        self.data = ""

    def run(self):
        while True:
            try:
                win32clipboard.OpenClipboard()  # 打开剪贴板
                self.data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)  # 读取剪贴板
                win32clipboard.CloseClipboard()  # 关闭剪贴板
            # 「有些时候读取剪贴板回报错，目前猜测可能是因为有其他进程正在使用剪贴板」
            # 「不管为何，反正不是致命性错误，就直接忽略就行了
            except pywintypes.error:
                continue
            self.update.emit(self.data)
            time.sleep(0.5)


class VisibleAndMove(QtCore.QThread):

    # 控制主菜单按钮显示/隐藏
    menuBut_show = QtCore.pyqtSignal()
    menuBut_hide = QtCore.pyqtSignal()
    # 控制从剪贴板下载按钮显示/隐藏
    downloadBut_show = QtCore.pyqtSignal()
    downloadBut_hide = QtCore.pyqtSignal()
    # 返回应移动的坐标
    move = QtCore.pyqtSignal(list)

    def __init__(self):
        super().__init__()
        # 剪贴板数据
        # 由「Clipboard」类提供数据
        self.clipboard = ""

    def run(self):
        while True:
            # 「网易云音乐的窗口为什么没有窗口名？要不然根本不用这么麻烦！」
            # 「这部分我早晚都得优化优化，但不是现在」

            # 获取当前焦点窗口句柄
            hwnd = win32gui.GetForegroundWindow()
            # 判断获取的句柄是否为窗口
            # 「如果不是窗口就无法获取exe名称，会报错。所以不是exe就直接continue好了~ awa」
            if not win32gui.IsWindow(hwnd):
                continue
            process = win32process.GetWindowThreadProcessId(hwnd)
            name = psutil.Process(process[1]).name()

            # 判断当前聚集窗口是否为网易云音乐，如果是就显示按钮并执行剪切板检测
            if name == "cloudmusic.exe":
                self.menuBut_show.emit()

                # 剪切板检测
                if "music.163.com" in self.clipboard:
                    self.downloadBut_show.emit()
                else:
                    self.downloadBut_hide.emit()

                # 获取网易云音乐右上坐标，并同步到自己的窗体
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                self.move.emit([right - 150, top + 50])
            # 判断是否聚焦在自己的窗体上
            # 「如果不判断，鼠标放在自己窗体按钮上时会造成窗体闪烁」
            # 「鼠标从网易云音乐窗体移动自己窗体后鼠标不在网易云音乐窗体上，故隐藏窗体」
            # 「隐藏自己窗体后，鼠标指针落回网易云音乐窗体上，故显示窗体」
            # 「显示自己窗体后，鼠标指针不再在网易云音乐窗体上，故再次隐藏窗体」
            # 「我们要相信闪烁的窗体是幸福的」
            elif win32gui.GetWindowText(hwnd) != "cloud_music_down":
                self.menuBut_hide.emit()
                self.downloadBut_hide.emit()

            # 如果窗体最小化（InIconic），则显示窗体
            # 「为解决有时窗体最小化无法弹出的Bug」
            hwnd = win32gui.FindWindow(None, "cloud_music_down")
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_SHOWMAXIMIZED)


class Download(QtCore.QThread):
    # 下载结束信号
    finish = QtCore.pyqtSignal()

    def __init__(self, download_url):
        super().__init__()
        # 包含一个或多个链接的文本的字符串
        self.download_url = download_url
        # 包含下载链接与歌曲名称的二维列表
        self.download_urls = []

    def run(self):
        # 『调试代码，早晚得改』
        self.download("./")

    def get_urls(self):
        download_urls = []  # 包含所有找到的url

        # 提取所有的单个音乐链接
        single = re.findall(r"(https://)?music\.163\.com(/#)?(/song\?id=\d+)", self.download_url)
        single_songs = [i[2] for i in single]
        download_urls += single_songs  # 将获取到的链接存入变量

        playlist_songs = []  # 记录所有找到的歌单链接
        # 提取所有的歌单链接
        playlist = re.findall(r"(https://)?music\.163\.com/(#/)?playlist\?id=(\d+)", self.download_url)
        playlist = [i[2] for i in playlist]
        for i in playlist:
            # 请求网易云音乐官网，获取每个歌单的包含的歌曲
            # 「请求时必须加上Cookie:os=pc,否则最多获得10/20个音乐」
            # 「太过分了！」
            ret = requests.get(f"https://music.163.com/playlist?id={i}", headers={"User-Agent": random.choice(useragent)}, cookies={'os': 'pc'}).text
            ret_html = html.fromstring(ret)
            playlist_songs += ret_html.xpath('//div[@id="song-list-pre-cache"]/ul/li/a/@href')
        download_urls += playlist_songs  # 将获取到的链接存入变量

        album_songs = []  # 记录所有的专辑链接
        # 获取所有的专辑链接
        album = re.findall(r"(https://)?music\.163\.com/(#/)?album\?id=(\d+)", self.download_url)
        album = [i[2] for i in album]
        for i in album:
            # 「虽然在这里现在没有必要写上Cookie，但以后就不好说了。所有先写着吧~」
            ret = requests.get(f"https://music.163.com/album?id={i}", headers={"User-Agent": random.choice(useragent)}, cookies={'os': 'pc'}).text
            ret_html = html.fromstring(ret)
            album_songs += ret_html.xpath('//div[@id="song-list-pre-cache"]/ul/li/a/@href')
        download_urls += album_songs  # 将获取到的链接存入变量

        # 将所有的歌曲ID转换为歌曲链接
        download_urls = [f"https://music.163.com{i}" for i in download_urls]

        # 分别获取每首歌的名称
        download_names = []
        for i in download_urls:
            ret = requests.get(i, headers={"User-Agent": random.choice(useragent)}).text
            ret_html = html.fromstring(ret)
            download_names += ret_html.xpath('/html/body/div[3]/div[1]/div/div/div[1]/div[1]/div[2]/div['
                                             '1]/div/em/text()')
        download_names = [re.sub(r"[/\\:*?\"<>|]", " ", i) for i in download_names]

        self.download_urls = list(zip(download_urls, download_names))

        return download_urls, download_names

    def download(self, save_dir):
        # 把歌曲链接转换为下载链接
        # 「我也不知道先把ID转为链接，再把链接转为下载链接有什么意义」
        urls = [[re.sub(r"https://music.163.com/song\?id=",
                        "https://music.163.com/song/media/outer/url?id=", i[0]),
                 i[1]] for i in self.download_urls]
        # 下载音乐
        for i in urls:
            res = requests.get(f"{i[0]}.mp3", headers={"User-Agent": random.choice(useragent)})
            # 判断获取到的内容 1.返回200 2.不是网页内容（VIP内容）
            if res.status_code == 200 and not res.text.startswith("<!DOCTYPE html>"):
                print("成功！（200）")
                with open(f"{save_dir}/{i[1]}.mp3", "wb") as f:
                    f.write(res.content)
            else:
                print("失败，本音乐无法下载，跳过本歌曲！")
        # 发送完成信号
        self.finish.emit()
