import sys
from PyQt6.QtWidgets import QMainWindow,QApplication,QDialog,QVBoxLayout,QLabel,QButtonGroup,QRadioButton,QPushButton 
from validators import url
from PyQt6.QtCore import Qt,QThread, pyqtSignal
import time
import re
import requests
import aria2p
import math
import subprocess
import shutil

from gui import Ui_MainWindow
from download import set_global, dialog_show

class DownloadThread(QThread):
    update_progress = pyqtSignal(int)
    update_text = pyqtSignal(str)
    rate_select = pyqtSignal(list)
    download_done = pyqtSignal()

    def run(self):
        """
        执行下载逻辑
        """
        print(self.ui.lineEdit.text(), self.ui.spinBox.text(), self.ui.spinBox_2.text())
        self.ui.pushButton.setEnabled(False)
        set_global(self, self.ui.lineEdit.text(), int(self.ui.spinBox.text()), int(self.ui.spinBox_2.text()), self.aria2)

class AriaThread(QThread):
    def run(self):
        proc = subprocess.run(['start.bat'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout = proc.stdout.decode('gbk')
        stderr = proc.stderr.decode('gbk')
        print(stdout)
        print(stderr)

# 弹出窗口
class PopupWindow(QDialog):

    def __init__(self, all_rate, main_self):
        super().__init__()
        # 隐藏关闭按钮
        # self.setWindowFlags(Qt.WindowType.Window | 
        #                    Qt.WindowType.WindowTitleHint |
        #                    Qt.WindowType.CustomizeWindowHint)

        # self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        self.main_self = main_self

        self.setModal(True)

        self.setWindowTitle('多码率选择')

        layout = QVBoxLayout()
          
        label = QLabel("检测到多个码率视频，请选择一个进行下载")
        layout.addWidget(label)
        btn_group = QButtonGroup(exclusive=True)

        for item in all_rate:
            rbtn = QRadioButton(item)
            btn_group.addButton(rbtn)
            layout.addWidget(rbtn)

        # 默认选中第一个
        btn_group.buttons()[0].setChecked(True)

        ok_button = QPushButton('确定')
        ok_button.clicked.connect(lambda: self.confirm_rate(btn_group))
        layout.addWidget(ok_button)

        self.setLayout(layout)

    def confirm_rate(self, btn_g):
        index = btn_g.buttons().index(btn_g.checkedButton())
        dialog_show(index)
        self.close()
    
    def closeEvent(self, event):
        # 添加关闭处理逻辑
        self.main_self.video_download_done()
    

class MyMainWindow(QMainWindow,Ui_MainWindow):
    def __init__(self,parent =None):
        super(MyMainWindow,self).__init__(parent)
        self.setupUi(self)

        aria2 = aria2p.API(
            aria2p.Client(
                host="http://localhost",
                port=6800,
                secret=""
            )
        )

        try:
            aria2.get_stats()
            print(aria2.get_stats())
        except:
            # 开启aria2进程
            self.threadAria = AriaThread()
            self.threadAria.start()

        try:
            aria2.get_stats()
            self.textBrowser.setText('aria2已启动')
        except:
            self.textBrowser.setText('aria2未启动')
            self.pushButton.setEnabled(False)

        # 点击下载按钮
        self.pushButton.clicked.connect(lambda: self.validate_url(aria2))

    def validate_url(self, aria2):
        if (url(self.lineEdit.text())):
            self.progressBar.setValue(0)
            self.textBrowser.setText('')
            self.thread = DownloadThread()
            self.thread.update_progress.connect(self.update_progress_bar)
            self.thread.update_text.connect(self.update_text_browser)
            self.thread.rate_select.connect(self.start_rate_select)
            self.thread.download_done.connect(self.video_download_done)
            self.thread.ui = self
            self.thread.aria2 = aria2
            self.thread.start()
            # download_m3u8(self.lineEdit.text(), self.spinBox.text(), self.spinBox_2.text())
            # print(self.lineEdit.text(), self.spinBox.text(), self.spinBox_2.text())
        else:
            self.textBrowser.setText('请输入正确的视频链接')
    
    def update_progress_bar(self, value):
        self.progressBar.setValue(value)
    def update_text_browser(self, value):
        self.textBrowser.append(value)
    def start_rate_select(self, value):
        print(value)
        window = PopupWindow(value, self) 
        window.exec()
    def video_download_done(self):
        self.pushButton.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWin = MyMainWindow()
    myWin.show()
    sys.exit(app.exec())  