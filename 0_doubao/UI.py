import tkinter as tk
from tkinter import filedialog, scrolledtext
from playwright.sync_api import sync_playwright
import time
import json
import random
from datetime import datetime
import os
import requests
from urllib.parse import urlparse, parse_qs
import threading

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Application")
        self.root.geometry("1000x600")

        # 接收端运行状态
        self.receiver_running = False
        self.receiver_thread = None
        self.browser = None
        self.context = None
        self.page = None

        # 初始化接收端和 download_dir
        self.receiver = Receiver(self.log_receiver)
        self.download_dir = self.receiver.download_dir

        # 初始化 UI
        self.setup_ui()

    def setup_ui(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        sender_frame = tk.LabelFrame(main_frame, text="发送端", padx=10, pady=10)
        sender_frame.grid(row=0, column=0, sticky="nsew", padx=5)

        tk.Label(sender_frame, text="消息:").pack(anchor="w")
        self.sender_message = tk.Entry(sender_frame, width=40)
        self.sender_message.pack(fill=tk.X, pady=5)

        self.file_path_var = tk.StringVar()
        tk.Label(sender_frame, text="文件:").pack(anchor="w")
        file_frame = tk.Frame(sender_frame)
        file_frame.pack(fill=tk.X, pady=5)
        tk.Entry(file_frame, textvariable=self.file_path_var, width=30, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(file_frame, text="选择文件", command=self.choose_file).pack(side=tk.LEFT, padx=5)

        tk.Button(sender_frame, text="发送", command=self.send_message).pack(pady=5)

        tk.Label(sender_frame, text="发送日志:").pack(anchor="w")
        self.sender_log = scrolledtext.ScrolledText(sender_frame, height=15, width=50, state="disabled")
        self.sender_log.pack(fill=tk.BOTH, expand=True)

        receiver_frame = tk.LabelFrame(main_frame, text="接收端", padx=10, pady=10)
        receiver_frame.grid(row=0, column=1, sticky="nsew", padx=5)

        tk.Label(receiver_frame, text=f"下载目录: {self.download_dir}").pack(anchor="w")
        tk.Label(receiver_frame, text="接收日志:").pack(anchor="w")
        self.receiver_log = scrolledtext.ScrolledText(receiver_frame, height=15, width=50, state="disabled")
        self.receiver_log.pack(fill=tk.BOTH, expand=True)

        self.receiver_button = tk.Button(receiver_frame, text="启动接收", command=self.toggle_receiver)
        self.receiver_button.pack(pady=5)

        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

    def log_sender(self, message):
        self.sender_log.config(state="normal")
        self.sender_log.insert(tk.END, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
        self.sender_log.see(tk.END)
        self.sender_log.config(state="disabled")

    def log_receiver(self, message):
        self.receiver_log.config(state="normal")
        self.receiver_log.insert(tk.END, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
        self.receiver_log.see(tk.END)
        self.receiver_log.config(state="disabled")

    def choose_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_path_var.set(file_path)

    def send_message(self):
        message = self.sender_message.get().strip()
        file_path = self.file_path_var.get().strip()

        if not message and not file_path:
            self.log_sender("错误：请输入消息或选择文件")
            return

        if not self.page:
            try:
                self.playwright = sync_playwright().start()
                self.browser = self.playwright.chromium.launch(headless=True)
                self.context = self.browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                self.page = self.context.new_page()

                try:
                    with open("cookies.json", "r") as f:
                        cookies = json.load(f)
                        self.context.add_cookies(cookies)
                    self.page.goto("https://www.doubao.com/chat/3883015919088130")
                    time.sleep(5)
                    self.page.wait_for_selector('textarea[data-testid="chat_input_input"]', timeout=10000)
                    self.log_sender("已进入聊天界面")
                except FileNotFoundError:
                    self.log_sender("未找到cookies.json，请先运行save_cookies.py")
                    self.cleanup_browser()
                    return
                except Exception as e:
                    self.log_sender(f"初始化失败：{e}")
                    self.cleanup_browser()
                    return
            except Exception as e:
                self.log_sender(f"Playwright 初始化失败：{e}")
                return

        try:
            if file_path:
                self.log_sender(f"发送文件：{file_path}")
                success = send_message(self.page, file_path=file_path, log_callback=self.log_sender)
                if success:
                    self.log_sender("文件发送成功")
                    self.file_path_var.set("")
                else:
                    self.log_sender("文件发送失败")
            else:
                self.log_sender(f"发送消息：{message}")
                success = send_message(self.page, message=message, log_callback=self.log_sender)
                if success:
                    self.log_sender("消息发送成功")
                    self.sender_message.delete(0, tk.END)
                else:
                    self.log_sender("消息发送失败")
        except Exception as e:
            self.log_sender(f"发送失败：{e}")
            self.cleanup_browser()

    def toggle_receiver(self):
        if not self.receiver_running:
            self.receiver_running = True
            self.receiver.running = True
            self.receiver_button.config(text="停止接收")
            self.receiver_thread = threading.Thread(target=self.receiver.main, daemon=True)
            self.receiver_thread.start()
            self.log_receiver("接收端已启动")
        else:
            self.receiver_running = False
            self.receiver.running = False
            self.receiver_button.config(text="启动接收")
            self.log_receiver("接收端已停止")

    def cleanup_browser(self):
        if self.page:
            try:
                self.page.close()
            except:
                pass
        if self.context:
            try:
                self.context.close()
            except:
                pass
        if self.browser:
            try:
                self.browser.close()
            except:
                pass
        if hasattr(self, 'playwright') and self.playwright:
            try:
                self.playwright.stop()
            except:
                pass
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None

    def on_closing(self):
        self.receiver_running = False
        self.receiver.running = False
        self.cleanup_browser()
        self.root.destroy()

class Receiver:
    def __init__(self, log_callback):
        self.url = "https://www.doubao.com/chat/3883015919088130"
        self.output_messages = set()
        self.running = True
        self.download_dir = "downloaded_files"
        self.log_callback = log_callback

        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            self.log_callback(f"创建下载目录：{self.download_dir}")

    def download_file(self, page, file_message, file_name):
        try:
            file_name = "".join(c for c in file_name if c.isalnum() or c in ('.', '_', '-')).strip()
            if not file_name:
                file_name = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            base_name, ext = os.path.splitext(file_name)
            save_path = os.path.join(self.download_dir, file_name)
            counter = 1
            while os.path.exists(save_path):
                save_path = os.path.join(self.download_dir, f"{base_name}_{counter}{ext}")
                counter += 1

            file_message.hover()
            file_message.focus()
            time.sleep(3)

            download_button = file_message.query_selector('div.container-bVzDc1 div.scale-up-rpd_mD:nth-child(2)')
            if not download_button:
                self.log_callback(f"未找到下载按钮，文件：{file_name}")
                return False

            try:
                with page.context.expect_page(timeout=15000) as popup_info:
                    download_button.dispatch_event('mousedown')
                    download_button.dispatch_event('mouseup')
                    download_button.click(force=True)
                popup_page = popup_info.value
                navigation_url = popup_page.url

                target_url = navigation_url
                if 'link.wtturl.cn' in navigation_url:
                    parsed_url = urlparse(navigation_url)
                    target_url = parse_qs(parsed_url.query).get('target', [None])[0]
                    if not target_url:
                        self.log_callback(f"未找到 target 参数，文件：{file_name}")
                        popup_page.close()
                        return False

                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                cookies = {c['name']: c['value'] for c in page.context.cookies()}
                response = requests.get(target_url, stream=True, headers=headers, cookies=cookies)

                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if 'application/pdf' in content_type and ext.lower() != '.pdf':
                        save_path = save_path.replace(ext, '.pdf')
                    elif 'image/jpeg' in content_type and ext.lower() != '.jpg':
                        save_path = save_path.replace(ext, '.jpg')
                    elif 'image/png' in content_type and ext.lower() != '.png':
                        save_path = save_path.replace(ext, '.png')

                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    self.log_callback(f"文件已下载并保存至：{save_path}")
                    popup_page.close()
                    return True
                else:
                    self.log_callback(f"下载失败，状态码：{response.status_code}，文件：{file_name}")
                    popup_page.close()
                    return False

            except Exception as e:
                self.log_callback(f"下载失败：{e}，文件：{file_name}")
                return False

        except Exception as e:
            self.log_callback(f"下载失败：{e}，文件：{file_name}")
            return False

    def fetch_messages(self, page):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)

        text_messages = page.query_selector_all('div[data-testid="send_message"] div[data-testid="message_text_content"]')
        file_messages = page.query_selector_all('div[data-testid="attachment_file_item"]')

        messages = []
        for i, message in enumerate(text_messages):
            text = message.inner_text().strip()
            if text:
                messages.append({"type": "text", "content": text, "index": i})

        for i, file_message in enumerate(file_messages):
            file_name_element = file_message.query_selector('div[data-testid="message_nested_content_file_name"]')
            file_name = file_name_element.inner_text().strip() if file_name_element else f"unknown_{i}"
            messages.append({"type": "file", "name": file_name, "element": file_message, "index": i})

        return messages

    def main(self):
        while self.running:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()

                try:
                    with open("cookies.json", "r") as f:
                        cookies = json.load(f)
                        context.add_cookies(cookies)
                except FileNotFoundError:
                    self.log_callback("未找到cookies.json，请先运行save_cookies.py")
                    break

                try:
                    page.goto(self.url)
                    time.sleep(5)
                    page.wait_for_selector('div[data-testid="send_message"]', timeout=10000)
                    if not self.output_messages:
                        self.log_callback("已进入聊天界面，开始监测新消息...")
                except Exception as e:
                    self.log_callback(f"登录状态无效或页面加载失败：{e}")
                    browser.close()
                    break

                try:
                    messages = self.fetch_messages(page)
                    for message in messages:
                        message_key = f"{message['type']}:{message['index']}:{message['content'] if message['type'] == 'text' else message['name']}"
                        if message_key not in self.output_messages:
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            self.log_callback(f"[新消息] {timestamp}")
                            if message["type"] == "text":
                                self.log_callback(f"接收到文本消息：{message['content']}")
                            else:
                                self.log_callback(f"接收到文件：{message['name']}")
                                self.download_file(page, message['element'], message['name'])
                            self.output_messages.add(message_key)
                except Exception as e:
                    self.log_callback(f"消息获取失败：{e}")

                browser.close()

            if self.running:
                time.sleep(2)

def send_message(page, message=None, file_path=None, log_callback=None):
    input_selector = 'textarea[data-testid="chat_input_input"]'
    button_selector = 'button[data-testid="chat_input_send_button"]'
    reply_selector = 'div[data-testid="receive_message"] div[data-testid="message_text_content"]'
    file_input_selector = 'input[type="file"]'

    if file_path:
        if not os.path.exists(file_path):
            if log_callback:
                log_callback(f"文件 {file_path} 不存在")
            return False

        try:
            file_input = page.query_selector(file_input_selector)
            if not file_input:
                if log_callback:
                    log_callback("未找到文件上传输入框，请检查选择器")
                return False
            file_input.set_input_files(file_path)
            if log_callback:
                log_callback(f"已上传文件：{file_path}")
            time.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            if log_callback:
                log_callback(f"文件上传失败：{e}")
            return False
    else:
        try:
            page.fill(input_selector, message)
            time.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            if log_callback:
                log_callback(f"消息输入失败：{e}")
            return False

    try:
        page.wait_for_selector(f'{button_selector}:not([disabled])', timeout=10000)
        page.click(button_selector)
    except Exception as e:
        if log_callback:
            log_callback(f"发送按钮点击失败：{e}")
        return False

    try:
        initial_count = len(page.query_selector_all(reply_selector))
        start_time = time.time()
        timeout = 60
        while time.time() - start_time < timeout:
            responses = page.query_selector_all(reply_selector)
            current_count = len(responses)
            if current_count > initial_count:
                reply_text = responses[-1].inner_text().strip()
                if reply_text and (not message or reply_text != message.strip()):
                    for _ in range(3):
                        time.sleep(1)
                        new_reply_text = responses[-1].inner_text().strip()
                        if new_reply_text == reply_text:
                            if log_callback:
                                log_callback(f"回复：{reply_text}")
                            return True
                        reply_text = new_reply_text
            time.sleep(1)
        if log_callback:
            log_callback("未收到回复")
        return False
    except Exception as e:
        if log_callback:
            log_callback(f"未检测到回复：{e}")
        return False

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()