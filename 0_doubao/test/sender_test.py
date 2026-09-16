from playwright.sync_api import sync_playwright
import json
import time
import random
import string
from datetime import datetime
import os

def generate_random_string(min_len=10, max_len=50):
    length = random.randint(min_len, max_len)
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

def send_message(page, message=None, file_path=None, message_id=None):
    input_selector = 'textarea[data-testid="chat_input_input"]'
    button_selector = 'button[data-testid="chat_input_send_button"]'
    reply_selector = 'div[data-testid="receive_message"] div[data-testid="message_text_content"]'
    file_input_selector = 'input[type="file"]'

    if file_path:
        if not os.path.exists(file_path):
            print(f"文件 {file_path} 不存在")
            return False
        try:
            file_input = page.query_selector(file_input_selector)
            if not file_input:
                print("未找到文件上传输入框")
                return False
            file_input.set_input_files(file_path)
            print(f"已上传文件：{file_path}")
        except Exception as e:
            print(f"文件上传失败：{e}")
            return False
    else:
        page.fill(input_selector, message)

    try:
        page.wait_for_selector(f'{button_selector}:not([disabled])', timeout=10000)
        page.click(button_selector)
        print(f"消息 {message_id} 发送成功")
    except Exception as e:
        print(f"发送按钮点击失败：{e}")
        return False

    try:
        initial_count = len(page.query_selector_all(reply_selector))
        start_time = time.time()
        timeout = 180
        sent_message = message.strip() if message else ""
        while time.time() - start_time < timeout:
            responses = page.query_selector_all(reply_selector)
            if len(responses) > initial_count:
                reply_text = responses[-1].inner_text().strip()
                if reply_text and reply_text != sent_message:
                    for _ in range(2):
                        new_reply_text = responses[-1].inner_text().strip()
                        if new_reply_text != reply_text:
                            reply_text = new_reply_text
                            continue
                        return True
            time.sleep(0.1)
        print("未收到新回复")
        return False
    except Exception as e:
        print(f"回复检测失败：{e}")
        return False

def sender_main():
    url = "https://www.doubao.com/chat/3937750985769474"
    sent_messages = []
    n = 10
    prompt = "不用思考，仅回复这是第几个消息，输出少于5个字"

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
            return

        page.goto(url)
        try:
            page.wait_for_selector('textarea[data-testid="chat_input_input"]', timeout=15000)
            print("已进入聊天界面")
        except:
            print("登录状态无效，请重新运行save_cookies.py")
            return

        print("\n选择操作：")
        print("1. 发送文本消息")
        print("2. 发送文件（通过上传按钮）")
        choice = input("请输入选项（1/2）：").strip().lower()
        if choice not in ["1", "2"]:
            print("无效选项")
            return

        for i in range(n):
            message_id = i + 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            content = generate_random_string()
            full_content = f"{content}\n{prompt}"
            sent_messages.append({"message": content, "timestamp": timestamp})

            if choice == "1":
                if not send_message(page, message=full_content, message_id=message_id):
                    print("消息发送失败")
                    break
            else:
                file_path = f"message_{message_id}.txt"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(full_content)
                if not send_message(page, file_path=file_path, message_id=message_id):
                    print("文件发送失败")
                    os.remove(file_path)
                    break
                os.remove(file_path)

        with open("sent_messages.json", "w", encoding="utf-8") as f:
            json.dump(sent_messages, f, ensure_ascii=False, indent=2)
        print("消息记录已保存至 sent_messages.json")

        browser.close()

if __name__ == "__main__":
    sender_main()