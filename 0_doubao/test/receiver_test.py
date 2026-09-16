from playwright.sync_api import sync_playwright
import json
import time
from datetime import datetime
import os
import requests
from urllib.parse import urlparse, parse_qs
import signal
import sys
import threading

class Receiver:
    def __init__(self):
        self.url = "https://www.doubao.com/chat/3937750985769474"
        self.output_messages = set()
        self.received_messages = []
        self.running = True
        self.download_dir = "downloaded_files"
        self.n = 10
        self.prompt = "不用思考，仅回复这是第几个消息，输出少于5个字"

    def signal_handler(self, sig, frame):
        self.running = False

    def check_exit_command(self):
        while self.running:
            try:
                command = input().strip().lower()
                if command == "exit":
                    self.running = False
                    break
            except:
                pass
            time.sleep(0.1)

    def download_file(self, page, file_message, file_name):
        try:
            file_name = "".join(c for c in file_name if c.isalnum() or c in ('.', '_', '-')).strip() or f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            base_name, ext = os.path.splitext(file_name)
            save_path = os.path.join(self.download_dir, file_name)
            counter = 1
            while os.path.exists(save_path):
                save_path = os.path.join(self.download_dir, f"{base_name}_{counter}{ext}")
                counter += 1

            file_message.hover()
            file_message.focus()
            download_button = file_message.query_selector('div.container-bVzDc1 div.scale-up-rpd_mD:nth-child(2)')
            if not download_button:
                return False

            with page.context.expect_page(timeout=15000) as popup_info:
                download_button.click(force=True)
            popup_page = popup_info.value
            navigation_url = popup_page.url

            target_url = navigation_url
            if 'link.wtturl.cn' in navigation_url:
                parsed_url = urlparse(navigation_url)
                target_url = parse_qs(parsed_url.query).get('target', [None])[0]
                if not target_url:
                    popup_page.close()
                    return False

            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
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
                popup_page.close()
                print(f"文件已下载：{save_path}")
                return True
            else:
                popup_page.close()
                return False
        except:
            return False

    def fetch_messages(self, page):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
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
                        print("已加载Cookies")
                except FileNotFoundError:
                    print("未找到cookies.json，请先运行save_cookies.py")
                    break

                try:
                    page.goto(self.url)
                    page.wait_for_selector('div[data-testid="send_message"]', timeout=15000)
                    print("已进入聊天界面")
                except:
                    print("登录状态无效或页面加载失败")
                    browser.close()
                    break

                try:
                    messages = self.fetch_messages(page)
                    for message in messages:
                        message_key = f"{message['type']}:{message['index']}:{message['content'] if message['type'] == 'text' else message['name']}"
                        if message_key not in self.output_messages:
                            if len(self.received_messages) == 0 or self.prompt in message['content'] if message['type'] == 'text' else True:
                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                content = message['content'] if message['type'] == 'text' else message['name']
                                actual_content = content.replace(f"\n{self.prompt}", "").strip() if self.prompt in content else content
                                self.received_messages.append({"message": actual_content, "timestamp": timestamp})
                                print(f"收到新消息：{actual_content}")
                                if message['type'] == 'file':
                                    self.download_file(page, message['element'], message['name'])
                                self.output_messages.add(message_key)
                except Exception as e:
                    print(f"消息获取失败：{e}")

                browser.close()

                if len(self.received_messages) >= self.n + 1:
                    break

                time.sleep(0.1)

        with open("received_messages.json", "w", encoding="utf-8") as f:
            json.dump(self.received_messages, f, ensure_ascii=False, indent=2)
        print("消息记录已保存至 received_messages.json")

if __name__ == "__main__":
    receiver = Receiver()
    receiver.main()