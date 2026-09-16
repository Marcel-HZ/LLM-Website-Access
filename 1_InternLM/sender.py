from playwright.sync_api import sync_playwright
import time
import json
import random
from datetime import datetime

def send_message(page, message, message_id):
    input_selector = 'textarea[placeholder="输入 / 选择常用语"]'
    reply_selector = 'div[class*="chatItem-module_row__NocxR"]:not([class*="user"])'

    # 输入消息
    page.fill(input_selector, message)
    time.sleep(random.uniform(0.5, 1.5))

    # 发送消息（回车）
    try:
        page.press(input_selector, "Enter")
    except Exception as e:
        print(f"发送失败：{e}")
        return False

    # 等待新回复
    try:
        initial_count = len(page.query_selector_all(reply_selector))
        start_time = time.time()
        timeout = 60
        while time.time() - start_time < timeout:
            responses = page.query_selector_all(reply_selector)
            if len(responses) > initial_count:
                reply_text = responses[-1].inner_text().strip()
                if reply_text and reply_text != message.strip():
                    # 检查内容稳定性
                    for _ in range(3):
                        time.sleep(1)
                        new_reply_text = responses[-1].inner_text().strip()
                        if new_reply_text == reply_text:
                            print(f"回复：{reply_text}")
                            return True
                        reply_text = new_reply_text
            time.sleep(1)
        print("未检测到完整回复")
        return False
    except Exception as e:
        print(f"未检测到回复：{e}")
        return False

def sender_main():
    url = "https://chat.intern-ai.org.cn/internlm/chat/FecVsmuHUd0Aut1tdEqgxopPQh1Z89ONciSGUKmgFFA=//"

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
                print("已加载Cookies")
        except FileNotFoundError:
            print("未找到cookies.json，请先运行save_cookies.py")
            return

        # 访问页面
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(5)

        # 检查登录状态
        try:
            page.wait_for_selector('textarea[placeholder="输入 / 选择常用语"]', timeout=10000)
            print("已进入聊天界面！")
        except:
            print("登录状态无效，请重新运行save_cookies.py")
            return

        # 循环发送消息
        message_id = 1
        while True:
            message = input("请输入要发送的消息（输入'exit'退出）：")
            if message.lower() == "exit":
                print("退出发送端")
                break

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[消息 {message_id}] {timestamp}")
            print(f"发送：{message}")
            if send_message(page, message, message_id):
                print("可以发送新消息")
            else:
                print("消息发送失败，请检查网络或选择器")
            message_id += 1

        browser.close()

if __name__ == "__main__":
    sender_main()