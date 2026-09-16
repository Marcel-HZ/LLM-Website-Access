from playwright.sync_api import sync_playwright
import time
import json
from datetime import datetime
import signal
import threading

class Receiver:
    def __init__(self):
        self.url = "https://tongyi.aliyun.com/?sessionId=9b8ebfc3ff3f4cef961e0b63db15f443"
        self.output_messages = set()
        self.running = True
        self.first_run = True

    def signal_handler(self, sig, frame):
        print("\n接收到退出信号，关闭接收端...")
        self.running = False

    def check_exit_command(self):
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

    def fetch_messages(self, page):
        send_messages = page.query_selector_all('div[class*="contentBox"] div[class*="bubble"]')
        messages = []
        for message in send_messages:
            message_text = message.inner_text().strip()
            if message_text:
                messages.append(message_text)
        return messages

    def check_login_status(self, page):
        chat_input_selector = 'textarea[placeholder="遇事不决问通义"]'
        login_selector = 'div[class*="loginContent"]'
        
        try:
            page.wait_for_selector(chat_input_selector, timeout=10000)
            if self.first_run:
                print("已进入聊天界面，开始监测新消息...")
                self.first_run = False
            return True
        except:
            if page.query_selector(login_selector):
                print("检测到登录页面，请重新登录或更新Cookies")
            else:
                print("未检测到聊天界面，检查URL或Cookies")
            return False

    def main(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        exit_thread = threading.Thread(target=self.check_exit_command, daemon=True)
        exit_thread.start()

        while self.running:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 720},
                    locale="zh-CN",
                    timezone_id="Asia/Shanghai"
                )
                page = context.new_page()

                try:
                    with open("cookies.json", "r") as f:
                        cookies = json.load(f)
                        context.add_cookies(cookies)
                except FileNotFoundError:
                    print("未找到cookies.json，请先运行save_cookies.py")
                    self.running = False
                    break

                try:
                    page.goto(self.url, wait_until="domcontentloaded")
                    time.sleep(3)
                    if not self.check_login_status(page):
                        browser.close()
                        break
                except Exception as e:
                    print(f"页面加载失败：{e}")
                    browser.close()
                    break

                try:
                    messages = self.fetch_messages(page)
                    for message in messages:
                        if message not in self.output_messages:
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            print(f"\n[新消息] {timestamp}")
                            print(f"接收到发送消息：{message}")
                            self.output_messages.add(message)
                except Exception as e:
                    print(f"消息获取失败：{e}")

                browser.close()

            if self.running:
                time.sleep(2)

if __name__ == "__main__":
    receiver = Receiver()
    receiver.main()