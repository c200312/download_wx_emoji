# 微信表情包下载

本项目是一个 **微信表情包下载工具**，可以实时抓取微信文件助手的图片消息，并保存到本地。

## 功能

* 实时抓取微信文件助手表情包
* 去重保存（基于图片 MD5）

### 下载 Edge WebDriver

1. 打开 [Microsoft Edge Driver 下载页](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/)
2. 下载与你的 Edge 浏览器版本一致的驱动
3. 将 `msedgedriver.exe` 放到项目目录或系统 PATH 下

---

## 使用方法



```bash
git clone --depth 1 https://github.com/c200312/wx_emoji_downloader.git
cd wx_emoji_downloader
uv sync
uv run download_img.py
```


3. 程序会弹出 GUI 界面：

   * 输入本地保存图片目录
   * 扫码登录微信网页版
   * 程序会实时抓取文件助手的图片并保存

4. 已下载图片会去重（基于 MD5），图片名称为图片的 MD5 值



---

## 注意事项

* 请确保 Edge 浏览器版本与 WebDriver 版本匹配
* 建议使用空文件夹，文件夹内若已有图片，图片名称要为图片的 MD5 值，否则不会已有图片进行去重
*

---


