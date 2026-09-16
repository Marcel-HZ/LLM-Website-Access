from playwright.sync_api import sync_playwright
import time
import json
from datetime import datetime
import signal
import sys
import threading
import os
import requests
from urllib.parse import urlparse, parse_qs

class Receiver:
    def __init__(self):
        self.url = "https://www.doubao.com/chat/3883015919088130"
        self.output_messages = set()  # 记录已输出的消息内容
        self.running = True  # 控制循环运行状态
        self.download_dir = "downloaded_files"  # 文件保存目录

        # 创建下载目录（如果不存在）
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            print(f"创建下载目录：{self.download_dir}")

    def signal_handler(self, sig, frame):
        print("\n接收到退出信号，关闭接收端...")
        self.running = False

    def check_exit_command(self):
        """线程函数：检查命令行输入'exit'"""
        while self.running:
            try:
                command = input().strip().lower()
                if command == "exit":
                    print("接收到'exit'命令，关闭接收端...")
                    self.running = False
                    break
            except:
                pass
            time.sleep(1)

    def download_file(self, page, file_message, file_name):
        """通过点击按钮捕获下载链接并保存文件"""
        try:
            # 清理文件名，避免非法字符
            file_name = "".join(c for c in file_name if c.isalnum() or c in ('.', '_', '-')).strip()
            if not file_name:
                file_name = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 处理文件名冲突
            base_name, ext = os.path.splitext(file_name)
            save_path = os.path.join(self.download_dir, file_name)
            counter = 1
            while os.path.exists(save_path):
                save_path = os.path.join(self.download_dir, f"{base_name}_{counter}{ext}")
                counter += 1

            # 模拟用户交互：悬停并聚焦
            file_message.hover()
            file_message.focus()
            time.sleep(3)  # 等待动态元素加载

            # 查找下载按钮
            download_button = file_message.query_selector('div.container-bVzDc1 div.scale-up-rpd_mD:nth-child(2)')
            if not download_button:
                print(f"未找到下载按钮，文件：{file_name}")
                return False

            # 捕获新窗口跳转
            try:
                with page.context.expect_page(timeout=15000) as popup_info:
                    download_button.dispatch_event('mousedown')
                    download_button.dispatch_event('mouseup')
                    download_button.click(force=True)
                popup_page = popup_info.value
                navigation_url = popup_page.url

                # 处理下载链接
                target_url = navigation_url
                if 'link.wtturl.cn' in navigation_url:
                    parsed_url = urlparse(navigation_url)
                    target_url = parse_qs(parsed_url.query).get('target', [None])[0]
                    if not target_url:
                        print(f"未找到 target 参数，文件：{file_name}")
                        popup_page.close()
                        return False

                # 使用 requests 下载文件
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                cookies = {c['name']: c['value'] for c in page.context.cookies()}
                response = requests.get(target_url, stream=True, headers=headers, cookies=cookies)

                if response.status_code == 200:
                    # 检查 Content-Type，动态调整扩展名
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
                    print(f"文件已下载并保存至：{save_path}")
                    popup_page.close()
                    return True
                else:
                    print(f"下载失败，状态码：{response.status_code}，文件：{file_name}")
                    popup_page.close()
                    return False

            except Exception as e:
                print(f"下载失败：{e}，文件：{file_name}")
                return False

        except Exception as e:
            print(f"下载失败：{e}，文件：{file_name}")
            return False

    def fetch_messages(self, page):
        """获取用户发送的消息，包括文本和文件"""
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
        signal.signal(signal.SIGINT, self.signal_handler)
        exit_thread = threading.Thread(target=self.check_exit_command, daemon=True)
        exit_thread.start()

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
                    print("未找到cookies.json，请先运行save_cookies.py")
                    break

                try:
                    page.goto(self.url)
                    time.sleep(5)
                    page.wait_for_selector('div[data-testid="send_message"]', timeout=10000)
                    if not self.output_messages:
                        print("已进入聊天界面，开始监测新消息...")
                except:
                    print("登录状态无效或页面加载失败，请检查cookies.json或网络")
                    browser.close()
                    break

                try:
                    messages = self.fetch_messages(page)
                    for message in messages:
                        # 使用索引和内容生成唯一 message_key
                        message_key = f"{message['type']}:{message['index']}:{message['content'] if message['type'] == 'text' else message['name']}"
                        if message_key not in self.output_messages:
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            print(f"\n[新消息] {timestamp}")
                            if message["type"] == "text":
                                print(f"接收到文本消息：{message['content']}")
                            else:
                                print(f"接收到文件：{message['name']}")
                                self.download_file(page, message['element'], message['name'])
                            self.output_messages.add(message_key)
                except Exception as e:
                    print(f"消息获取失败：{e}")

                browser.close()

            if self.running:
                time.sleep(2)

if __name__ == "__main__":
    receiver = Receiver()
    receiver.main()