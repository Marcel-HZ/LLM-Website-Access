from playwright.sync_api import sync_playwright
import time
import json
import random
from datetime import datetime
import os

def send_message(page, message=None, file_path=None, message_id=None):
    input_selector = 'textarea[data-testid="chat_input_input"]'
    button_selector = 'button[data-testid="chat_input_send_button"]'
    reply_selector = 'div[data-testid="receive_message"] div[data-testid="message_text_content"]'
    file_input_selector = 'input[type="file"]'  # 假设平台有隐藏的文件输入框

    if file_path:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"文件 {file_path} 不存在")
            return False

        # 上传文件
        try:
            file_input = page.query_selector(file_input_selector)
            if not file_input:
                print("未找到文件上传输入框，请检查选择器")
                return False
            file_input.set_input_files(file_path)
            print(f"已上传文件：{file_path}")
            time.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            print(f"文件上传失败：{e}")
            return False
    else:
        # 发送文本消息
        page.fill(input_selector, message)
        time.sleep(random.uniform(0.5, 1.5))

    # 等待发送按钮启用并点击
    try:
        page.wait_for_selector(f'{button_selector}:not([disabled])', timeout=10000)
        page.click(button_selector)
    except Exception as e:
        print(f"发送按钮点击失败：{e}")
        return False

    # 等待回复
    try:
        initial_count = len(page.query_selector_all(reply_selector))
        start_time = time.time()
        timeout = 60
        last_text = ""
        while time.time() - start_time < timeout:
            responses = page.query_selector_all(reply_selector)
            current_count = len(responses)
            if current_count > initial_count:
                reply_text = responses[-1].inner_text().strip()
                if reply_text and (not message or reply_text != message.strip()):
                    # 检查内容稳定性
                    for _ in range(3):
                        time.sleep(1)
                        new_reply_text = responses[-1].inner_text().strip()
                        if new_reply_text == reply_text:
                            print(f"回复：{reply_text}")
                            return True
                        reply_text = new_reply_text
            last_text = responses[-1].inner_text().strip() if responses else ""
            time.sleep(1)
        print("未收到回复")
        return False
    except Exception as e:
        print(f"未检测到回复：{e}")
        return False

def sender_main():
    url = "https://www.doubao.com/chat/3883015919088130"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # 加载 Cookies
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
            page.wait_for_selector('textarea[data-testid="chat_input_input"]', timeout=10000)
            print("已进入聊天界面！")
        except:
            print("登录状态无效，请重新运行save_cookies.py")
            return

        message_id = 1
        while True:
            print("\n选择操作：")
            print("1. 发送文本消息")
            print("2. 发送文件（通过上传按钮）")
            print("输入 'exit' 退出")
            choice = input("请输入选项（1/2/exit）：").strip().lower()

            if choice == "exit":
                print("退出发送端")
                break

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[消息 {message_id}] {timestamp}")

            try:
                if choice == "1":
                    message = input("请输入要发送的消息：")
                    print(f"发送：{message}")
                    if send_message(page, message=message, message_id=message_id):
                        print("可以发送新消息")
                    else:
                        print("消息发送失败，请检查网络或选择器")
                elif choice == "2":
                    file_path = input("请输入文件路径：")
                    print(f"发送文件：{file_path}")
                    if send_message(page, file_path=file_path, message_id=message_id):
                        print("文件发送成功")
                    else:
                        print("文件发送失败，请检查文件路径或网络")
                else:
                    print("无效选项，请输入 1、2 或 exit")
                    continue
                message_id += 1
            except Exception as e:
                print(f"消息 {message_id} 发送失败：{e}")

        browser.close()

if __name__ == "__main__":
    sender_main()