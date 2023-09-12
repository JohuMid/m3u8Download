# m3u8Download
m3u8视频下载器，支持定义并发数量，刷新任务频率，合并为mp4视频。

![](https://raw.githubusercontent.com/JohuMid/m3u8Download/main/logo.ico)


## 使用
1. 下载[懒人包](https://github.com/JohuMid/m3u8Download/releases/tag/package1.0.0)，双击运行main.exe
2. 找到合适的m3u8地址
3. 填入找到的下载链接
4. 点击下载，等待下载合并完毕
5. 在output下找下载完成的视频

## 如何找合适的m3u8地址
### 正常流程
在想要下载的视频页面按下F12键，打开控制台，点击网络标签页，输入m3u8过滤网络请求，刷新页面。
![](https://raw.githubusercontent.com/JohuMid/m3u8Download/main/images/image%201.png)


就会筛选出m3u8的视频地址，在筛选出的网络请求中点击查看预览，我们需要找到后缀为ts的网络请求。
![](https://raw.githubusercontent.com/JohuMid/m3u8Download/main/images/image%202.png)


找到后切换到标头内，请求URL中便是我们要找的m3u8链接。
![](https://raw.githubusercontent.com/JohuMid/m3u8Download/main/images/image%203.png)





## 开发者
开发环境python3.10.6。
```shell
// 安装依赖包
pip install
// 打包
python -m nuitka --onefile --windows-icon-from-ico=logo.ico --enable-plugin=pyqt6 main.py
```
