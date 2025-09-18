import time
import os
import re
import requests
import hashlib
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, JavascriptException

class WxImageDownloaderGUI:
    def __init__(self):
        # GUI 主窗口
        self.root = tk.Tk()
        self.root.title("微信图片下载器")
        self.root.geometry("500x400")

        # 保存目录
        tk.Label(self.root, text="图片保存目录:").pack(pady=5)
        self.save_dir_var = tk.StringVar()
        self.save_dir_entry = tk.Entry(self.root, textvariable=self.save_dir_var, width=50)
        self.save_dir_entry.pack()
        self.browse_btn = tk.Button(self.root, text="选择目录", command=self.select_dir)
        self.browse_btn.pack(pady=5)

        # 启动和停止按钮
        self.start_btn = tk.Button(self.root, text="开始抓图", command=self.start_downloader, width=20, height=2)
        self.start_btn.pack(pady=5)
        self.stop_btn = tk.Button(self.root, text="停止抓图", command=self.stop_downloader, state=tk.DISABLED, width=20, height=2)
        self.stop_btn.pack(pady=5)

        # 下载数量显示
        self.count_var = tk.StringVar(value="文件夹内图片数量: 0")
        self.count_label = tk.Label(self.root, textvariable=self.count_var)
        self.count_label.pack(pady=5)

        # 下载日志窗口
        tk.Label(self.root, text="下载日志:").pack()
        self.log_text = tk.Text(self.root, height=10, width=60, state=tk.DISABLED)
        self.log_text.pack(pady=5)

        # 内部状态
        self.stop_flag = False
        self.downloaded_md5 = set()
        self.seen_urls = set()
        self.session = requests.Session()
        self.driver = None
        self.total_count = 0
        self.downloader_thread = None

    def select_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.save_dir_var.set(directory)

    def start_downloader(self):
        save_dir = self.save_dir_var.get().strip()
        if not save_dir:
            messagebox.showwarning("警告", "请先选择保存目录")
            return
        os.makedirs(save_dir, exist_ok=True)
        self.save_dir = save_dir

              # 扫描已有图片，初始化已下载 md5 集合
        existing_files = os.listdir(self.save_dir)
        md5_pattern = re.compile(r'^([a-fA-F0-9]{32})\..+$')
        for fname in existing_files:
            m = md5_pattern.match(fname)
            if m:
                self.downloaded_md5.add(m.group(1))
        self.total_count = len(self.downloaded_md5)
        self.count_var.set(f"文件夹内图片数量: {self.total_count}")
        self.log(f"已扫描目录，发现 {self.total_count} 张图片")
        
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.downloader_thread = threading.Thread(target=self.run_downloader, daemon=True)
        self.downloader_thread.start()

    def stop_downloader(self):
        self.stop_flag = True
        self.stop_btn.config(state=tk.DISABLED)
        messagebox.showinfo("提示", "已停止抓取")

    def get_md5(self, content):
        md5 = hashlib.md5()
        md5.update(content)
        return md5.hexdigest()

    def log(self, msg):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def download_image(self, url):
        try:
            r = self.session.get(url, stream=True)
            if r.status_code == 200:
                content = r.content
                md5_hash = self.get_md5(content)
                if md5_hash in self.downloaded_md5:
                    return
                filename = os.path.join(self.save_dir, f"{md5_hash}.jpg")
                with open(filename, "wb") as f:
                    f.write(content)
                self.downloaded_md5.add(md5_hash)
                self.total_count += 1
                self.count_var.set(f"文件夹内图片数量: {self.total_count}")
                self.log(f"已保存: {filename}")
            else:
                self.log(f"下载失败: {url} 状态码 {r.status_code}")
        except Exception as e:
            self.log(f"下载异常: {url} 错误: {e}")

    def run_downloader(self):
        options = Options()
        options.add_argument("--start-maximized")
        self.driver = webdriver.Edge(service=Service(), options=options)
        self.driver.get("https://szfilehelper.weixin.qq.com/")

        # 等待登录
        self.log("请扫码登录微信网页版...")
        while True:
            try:
                self.driver.find_element(By.ID, "chatPanel")
                self.log("已登录，开始抓图")
                break
            except NoSuchElementException:
                if self.stop_flag:
                    return
                time.sleep(1)

        # 设置 cookies
        for cookie in self.driver.get_cookies():
            self.session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain'))

        # 注入 MutationObserver
        js_code = """
        window.newWxImages = [];
        const observer = new MutationObserver((mutationsList) => {
            for (const mutation of mutationsList) {
                for (const node of mutation.addedNodes) {
                    if (node.tagName === 'IMG' && node.src.includes('webwxgetmsgimg')) {
                        window.newWxImages.push(node.src);
                    } else if (node.querySelectorAll) {
                        const imgs = node.querySelectorAll('img');
                        imgs.forEach(img => {
                            if (img.src.includes('webwxgetmsgimg')) {
                                window.newWxImages.push(img.src);
                            }
                        });
                    }
                }
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
        """
        self.driver.execute_script(js_code)

        # 实时抓取
        while not self.stop_flag:
            try:
                new_imgs = self.driver.execute_script("return window.newWxImages.splice(0, window.newWxImages.length);")
                for url in new_imgs:
                    if url not in self.seen_urls:
                        self.download_image(url)
                        self.seen_urls.add(url)
            except JavascriptException:
                pass
            time.sleep(0.1)

        self.log("抓取已停止")

    def run(self):
        self.root.mainloop()


# ----------------- 程序入口 -----------------
if __name__ == "__main__":
    gui = WxImageDownloaderGUI()
    gui.run()
