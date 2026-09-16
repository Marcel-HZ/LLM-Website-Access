from playwright.sync_api import sync_playwright
import time
import json
import random
from datetime import datetime

def find_selectors(page):
    print("调试：当前页面URL:", page.url)
    print("调试：页面标题:", page.title())
    print("调试：页面HTML片段:", page.content()[:500], "...")
    print("调试：寻找输入框...")
    possible_inputs = page.query_selector_all('input, textarea, [contenteditable], [role="textbox"], div[class*="input"], div[class*="editor"]')
    for i, elem in enumerate(possible_inputs):
        outer_html = elem.evaluate('el => el.outerHTML')
        print(f"输入框 {i}: {outer_html[:100]}...")

    print("\n调试：寻找发送按钮...")
    possible_buttons = page.query_selector_all('button, [role="button"], svg, [class*="send"], [class*="submit"], [class*="icon"], div[class*="yc-editor-container"] > *')
    for i, elem in enumerate(possible_buttons):
        outer_html = elem.evaluate('el => el.outerHTML')
        print(f"按钮 {i}: {outer_html[:100]}...")

    print("\n调试：寻找消息区域...")
    possible_messages = page.query_selector_all('div[class*="message"], div[class*="chat"], div[class*="response"], div[class*="content"], div[class*="text"], div[class*="msg"]')
    for i, elem in enumerate(possible_messages):
        outer_html = elem.evaluate('el => el.outerHTML')
        print(f"消息 {i}: {outer_html[:200]}...")

def send_message(page, message, message_id):
    input_selector = 'div[placeholder*="通过shift+回车换行"]'
    reply_selector = 'div[class*="message"][class*="assistant"] div[class*="content"]'

    # 模拟鼠标移动
    page.mouse.move(random.randint(100, 500), random.randint(100, 500))
    time.sleep(random.uniform(0.5, 1))

    # 逐字输入消息
    try:
        input_element = page.query_selector(input_selector)
        for char in message:
            input_element.type(char, delay=random.uniform(50, 150))
        print(f"已输入消息：{message}")
        time.sleep(random.uniform(1, 2))
    except Exception as e:
        print(f"输入框选择器 '{input_selector}' 失败：{e}")
        find_selectors(page)
        return False

    # 模拟按下回车键
    try:
        print("模拟按下回车键...")
        page.press(input_selector, "Enter")
        print("已模拟回车键")
    except Exception as e:
        print(f"模拟回车键失败：{e}")
        find_selectors(page)
        return False

    # 等待大语言模型回复
    try:
        page.wait_for_selector(reply_selector, timeout=30000)
        time.sleep(2)
        print("检测到大语言模型回复")
        return True
    except Exception as e:
        print(f"未检测到回复：{e}")
        find_selectors(page)
        return False

def sender_main():
    url = "https://yiyan.baidu.com/chat/MzU5MDA1MDk1Mzo0OTQyNjAwMjIx"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            locale="zh-CN",
            timezone_id="Asia/Shanghai"
        )
        page = context.new_page()

        # 捕获网络响应
        page.on("response", lambda response: print(f"Response: {response.url} {response.status}"))

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
        page.goto(url)
        time.sleep(random.uniform(3, 5))

        # 检查登录状态
        try:
            page.wait_for_selector('div[placeholder*="通过shift+回车换行"]', timeout=10000)
            print("已进入聊天界面！")
        except:
            print("登录状态无效，请重新运行save_cookies.py")
            find_selectors(page)
            browser.close()
            return

        find_selectors(page)

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
                    time.sleep(random.uniform(5, 10))  # 增加间隔
                else:
                    print("消息发送失败，请检查网络或选择器")
                message_id += 1
            except Exception as e:
                print(f"消息 {message_id} 发送失败：{e}")

        browser.close()

if __name__ == "__main__":
    sender_main()

# 当前访问环境存在异常，请更换浏览器1分钟后再尝试提问