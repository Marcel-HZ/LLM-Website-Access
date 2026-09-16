from playwright.sync_api import sync_playwright
import time
import json
import random
from datetime import datetime

def check_login_status(page):
    login_selector = 'div[class*="loginContent"]'
    chat_input_selector = 'textarea[placeholder="遇事不决问通义"]'
    
    try:
        page.wait_for_selector(chat_input_selector, timeout=10000)
        print("已进入聊天界面！")
        return True
    except:
        if page.query_selector(login_selector):
            print("检测到登录页面，请重新登录或更新Cookies")
        else:
            print("未检测到聊天界面或登录页面，检查URL或Cookies")
        return False

def send_message(page, message, message_id):
    input_selector = 'textarea[placeholder="遇事不决问通义"]'
    send_button_selector = 'div[class*="chatInput"] span[class*="anticon"]'
    reply_selector = 'div[class*="contentBox"] div[class*="tongyi-markdown"]'

    page.mouse.move(random.randint(100, 500), random.randint(100, 500))
    time.sleep(random.uniform(0.5, 1))

    try:
        input_element = page.query_selector(input_selector)
        if not input_element:
            raise Exception("输入框未找到")
        input_element.fill("")
        for char in message:
            input_element.type(char, delay=random.uniform(50, 150))
        time.sleep(random.uniform(0.5, 1))
    except Exception as e:
        print(f"输入消息失败：{e}")
        return False

    try:
        page.press(input_selector, "Enter")
    except Exception as e:
        try:
            send_button = page.query_selector(send_button_selector)
            if not send_button:
                raise Exception("发送按钮未找到")
            send_button.click()
        except Exception as btn_e:
            print(f"发送消息失败：{btn_e}")
            return False

    try:
        page.wait_for_selector(reply_selector, timeout=30000)
        time.sleep(2)
        return True
    except Exception as e:
        print(f"未检测到回复：{e}")
        return False

def sender_main():
    url = "https://tongyi.aliyun.com/?sessionId=9b8ebfc3ff3f4cef961e0b63db15f443"

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
            browser.close()
            return

        try:
            page.goto(url, wait_until="domcontentloaded")
            time.sleep(random.uniform(3, 5))
        except Exception as e:
            print(f"页面加载失败：{e}")
            browser.close()
            return

        if not check_login_status(page):
            browser.close()
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
                    print("消息发送成功")
                    time.sleep(random.uniform(5, 10))
                else:
                    print("消息发送失败，请检查网络")
                message_id += 1
            except Exception as e:
                print(f"消息 {message_id} 发送失败：{e}")

        browser.close()

if __name__ == "__main__":
    sender_main()