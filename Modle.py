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
    def __init__(self):
        super().__init__()
        self.data = ""

    def run(self):
        while True:
            try:
                win32clipboard.OpenClipboard()
                self.data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
            except pywintypes.error:
                continue

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
    finish = QtCore.pyqtSignal()

    def __init__(self, download_url):
        super().__init__()
        self.download_url = download_url
        self.download_urls = []

    def run(self):
        self.download("./")

    def get_urls(self):
        download_urls = []
        single = re.findall(r"(https://)?music\.163\.com(/#)?(/song\?id=\d+)", self.download_url)
        single_songs = [i[2] for i in single]
        download_urls += single_songs

        playlist_songs = []
        playlist = re.findall(r"(https://)?music\.163\.com/(#/)?playlist\?id=(\d+)", self.download_url)
        playlist = [i[2] for i in playlist]
        for i in playlist:
            ret = requests.get(f"https://music.163.com/playlist?id={i}", headers={
                "User-Agent": random.choice(useragent)}, cookies={'os': 'pc'}).text
            ret_html = html.fromstring(ret)
            playlist_songs += ret_html.xpath('//div[@id="song-list-pre-cache"]/ul/li/a/@href')
        download_urls += playlist_songs

        album_songs = []
        album = re.findall(r"(https://)?music\.163\.com/(#/)?album\?id=(\d+)", self.download_url)
        album = [i[2] for i in album]
        for i in album:
            ret = requests.get(f"https://music.163.com/album?id={i}", headers={
                "User-Agent": random.choice(useragent)}, cookies={'os': 'pc'}).text
            ret_html = html.fromstring(ret)
            album_songs += ret_html.xpath('//div[@id="song-list-pre-cache"]/ul/li/a/@href')
        download_urls += album_songs

        download_urls = [f"https://music.163.com{i}" for i in download_urls]

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
        urls = [[re.sub(r"https://music.163.com/song\?id=",
                        "https://music.163.com/song/media/outer/url?id=", i[0]),
                 i[1]] for i in self.download_urls]
        for i in urls:
            url = f"{i[0]}.mp3"
            res = requests.get(url, headers={"User-Agent": random.choice(useragent)})
            if res.status_code == 200 and not res.text.startswith("<!DOCTYPE html>"):
                print("成功！（200）")
                with open(f"{save_dir}/{i[1]}.mp3", "wb") as f:
                    f.write(res.content)
            else:
                print("失败，本音乐无法下载，跳过本歌曲！")
        self.finish.emit()
