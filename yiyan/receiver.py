from playwright.sync_api import sync_playwright
import time
import json
from datetime import datetime
import signal
import threading

class Receiver:
    def __init__(self):
        self.url = "https://yiyan.baidu.com/chat/MzU5MDA1MDk1Mzo0OTQyNjAwMjIx"
        self.output_messages = set()  # 记录已输出的消息内容
        self.running = True  # 控制循环运行状态

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

    def fetch_messages(self, page):
        """获取用户发送的消息"""
        send_messages = page.query_selector_all('div[class*="message"][class*="user"] div[class*="content"]')
        messages = []
        for message in send_messages:
            message_text = message.inner_text().strip()
            messages.append(message_text)
        return messages

    def main(self):
        # 设置信号处理（捕获Ctrl+C）
        signal.signal(signal.SIGINT, self.signal_handler)

        # 启动退出命令监测线程
        exit_thread = threading.Thread(target=self.check_exit_command, daemon=True)
        exit_thread.start()

        # 主循环
        while self.running:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
                    break

                # 访问聊天页面
                try:
                    page.goto(self.url)
                    time.sleep(5)
                    page.wait_for_selector('div[class*="message"][class*="user"]', timeout=10000)
                    if not self.output_messages:
                        print("已进入聊天界面，开始监测新消息...")
                    else:
                        pass  # 不输出，用 pass 占位
                except:
                    print("登录状态无效或页面加载失败，请检查cookies.json或网络")
                    browser.close()
                    break

                # 获取消息
                try:
                    messages = self.fetch_messages(page)
                    # 对比新旧消息
                    for message in messages:
                        if message not in self.output_messages:
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            print(f"\n[新消息] {timestamp}")
                            print(f"接收到发送消息：{message}")
                            self.output_messages.add(message)
                except Exception as e:
                    print(f"消息获取失败：{e}")

                # 关闭浏览器
                browser.close()

            # 等待2秒后重新运行
            if self.running:
                time.sleep(2)

if __name__ == "__main__":
    receiver = Receiver()
    receiver.main()