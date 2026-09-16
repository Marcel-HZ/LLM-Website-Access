from playwright.sync_api import sync_playwright
import time
import json
from datetime import datetime
import signal
import threading

class Receiver:
    def __init__(self):
        self.url = "https://chat.intern-ai.org.cn/internlm/chat/FecVsmuHUd0Aut1tdEqgxopPQh1Z89ONciSGUKmgFFA=//"
        self.output_messages = set()
        self.running = True

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
        message_selector = 'div[class*="chatItem-module_row__NocxR"]'
        messages = []
        for item in page.query_selector_all(message_selector):
            text = item.inner_text().strip()
            if text:
                messages.append(text)
        return messages

    def main(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        exit_thread = threading.Thread(target=self.check_exit_command, daemon=True)
        exit_thread.start()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            page = context.new_page()

            # 加载Cookies
            try:
                with open("cookies.json", "r") as f:
                    cookies = json.load(f)
                    context.add_cookies(cookies)
            except FileNotFoundError:
                print("未找到cookies.json，请先运行save_cookies.py")
                self.running = False
                return

            # 主循环
            while self.running:
                try:
                    page.goto(self.url, wait_until="domcontentloaded")
                    page.wait_for_selector('textarea[placeholder="输入 / 选择常用语"]', timeout=10000)
                    if not self.output_messages:
                        print("已进入聊天界面，开始监测新消息...")
                except Exception as e:
                    print(f"页面加载失败：{e}")
                    continue

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

                time.sleep(2)

            browser.close()

if __name__ == "__main__":
    receiver = Receiver()
    receiver.main()