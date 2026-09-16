from playwright.sync_api import sync_playwright
import time
import json
import random
from datetime import datetime

def send_message(page, message, message_id):
    input_selector = 'div[contenteditable="true"]'  # 输入框
    button_selector = 'button.p-8px.rounded-6px'  # 发送按钮
    reply_selector = 'div.msg-item.msg-item-robot div.msg-item-content p'  # 模型回复

    # 输入消息
    try:
        input_element = page.query_selector(input_selector)
        input_element.fill(message)
        input_element.evaluate('el => el.dispatchEvent(new Event("input", { bubbles: true }))')
        time.sleep(random.uniform(0.5, 1.5))
    except:
        print(f"输入框选择器 '{input_selector}' 失败")
        return False

    # 等待发送按钮启用并点击
    try:
        page.wait_for_selector(f'{button_selector}:not([disabled])', timeout=10000)
        page.click(button_selector)
    except:
        print(f"发送按钮选择器 '{button_selector}' 失败")
        return False

    # 等待新回复
    try:
        initial_count = len(page.query_selector_all(reply_selector))
        start_time = time.time()
        timeout = 60
        while time.time() - start_time < timeout:
            responses = page.query_selector_all(reply_selector)
            current_count = len(responses)
            if current_count > initial_count:
                reply_text = responses[-1].inner_text().strip()
                if reply_text and reply_text != message.strip():
                    # 检查内容稳定性
                    for _ in range(3):  # 连续3秒检查
                        time.sleep(1)
                        new_reply_text = responses[-1].inner_text().strip()
                        if new_reply_text == reply_text:
                            return True
                        reply_text = new_reply_text
            time.sleep(1)
        print("未检测到新回复")
        return False
    except Exception as e:
        print(f"未检测到回复：{e}")
        return False

def sender_main():
    url = "https://chat.360.com/chat/496698f8fa811273"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
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
            return

        page.goto(url)
        time.sleep(5)

        try:
            page.wait_for_selector('div[contenteditable="true"]', timeout=10000)
            print("已进入聊天界面！")
        except:
            print("登录状态无效，请重新运行save_cookies.py")
            return

        message_id = 1
        while True:
            message = input("请输入要发送的消息（输入'exit'退出）：")
            if message.lower() == "exit":
                print("退出发送端")
                break

            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[消息 {message_id}] {timestamp}")
                print(f"发送：{message}")
                if send_message(page, message, message_id):
                    print("可以发送新消息")
                else:
                    print("消息发送失败，请检查网络或选择器")
                message_id += 1
            except Exception as e:
                print(f"消息 {message_id} 发送失败：{e}")

        browser.close()

if __name__ == "__main__":
    sender_main()