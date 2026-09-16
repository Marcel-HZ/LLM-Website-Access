from playwright.sync_api import sync_playwright
import time
import json
import random
from datetime import datetime

def find_selectors(page):
    """
    调试函数：打印可能的输入框、发送按钮和回复选择器
    """
    print("调试：寻找输入框...")
    possible_inputs = page.query_selector_all('input, textarea')
    for i, elem in enumerate(possible_inputs):
        outer_html = elem.evaluate('el => el.outerHTML')
        print(f"输入框 {i}: {outer_html[:100]}...")

    print("\n调试：寻找发送按钮...")
    possible_buttons = page.query_selector_all('button, [role="button"]')
    for i, elem in enumerate(possible_buttons):
        outer_html = elem.evaluate('el => el.outerHTML')
        print(f"按钮 {i}: {outer_html[:100]}...")

    print("\n调试：寻找消息区域...")
    possible_messages = page.query_selector_all('div[class*="message"], div[data-testid], div[class*="content"]')
    for i, elem in enumerate(possible_messages):
        outer_html = elem.evaluate('el => el.outerHTML')
        print(f"消息 {i}: {outer_html[:200]}...")

def send_message(page, message, message_id):
    # 选择器：基于聊天页面，替换为目标网站的实际选择器
    input_selector = 'textarea[data-testid="chat_input_input"]'  # 输入框
    button_selector = 'button[data-testid="chat_input_send_button"]'  # 发送按钮
    reply_selector = 'div[data-testid="receive_message"] div[data-testid="message_text_content"]'  # 回复内容
    
    # 输入消息
    try:
        page.fill(input_selector, message)
        time.sleep(random.uniform(0.5, 1.5))
    except:
        print(f"输入框选择器 '{input_selector}' 失败")
        find_selectors(page)
        return "输入失败，请检查输入框选择器"

    # 等待发送按钮启用并点击
    try:
        page.wait_for_selector(f'{button_selector}:not([disabled])', timeout=10000)
        page.click(button_selector)
    except:
        print(f"发送按钮选择器 '{button_selector}' 失败")
        find_selectors(page)
        return "发送失败，请检查按钮选择器"

    # 等待回复加载
    try:
        page.wait_for_selector(reply_selector, timeout=30000)
        time.sleep(2)  # 确保内容加载完成
    except:
        print(f"回复选择器 '{reply_selector}' 未找到")
        find_selectors(page)
        return "未找到回复，请检查回复选择器"

    # 获取最新回复
    responses = page.query_selector_all(reply_selector)
    if responses:
        reply_text = responses[-1].inner_text().strip()
        # 验证是否为用户输入
        if reply_text != message.strip():
            return reply_text
        else:
            return "提取到用户输入，请检查回复加载"
    return "未找到回复"

def main():
    url = "https://chatgpt.com/c/680741da-2ee0-8000-8c5f-9c92b7f8ed09"  # 替换为目标网站
    messages = [
        "今天几月几号？"
    ]
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # 显示浏览器，便于调试
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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
        
        # 访问目标页面
        page.goto(url)
        time.sleep(5)
        
        # 检查登录状态（基于输入框是否存在）
        try:
            page.wait_for_selector('textarea, input', timeout=10000)
            print("已进入目标界面！")
        except:
            print("登录状态无效或页面加载失败")
            find_selectors(page)
            return
        
        # 调试：首次运行可打印可能的元素
        find_selectors(page)
        
        # 发送消息并获取回复
        for i, message in enumerate(messages, 1):
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[消息 {i}] {timestamp}")
                print(f"发送：{message}")
                response = send_message(page, message, i)
                print(f"回复：{response}")
            except Exception as e:
                print(f"消息 {i} 交互失败：{e}")
        
        # 等待用户检查
        time.sleep(5)
        browser.close()

if __name__ == "__main__":
    main()