from playwright.sync_api import sync_playwright
import time
import json
import random
from datetime import datetime

def find_selectors(page):
    """调试：打印可能的输入框、发送按钮和消息区域"""
    print("调试：当前页面URL:", page.url)
    print("调试：页面标题:", page.title())
    print("调试：页面HTML片段:", page.content()[:500], "...")
    print("调试：寻找输入框...")
    possible_inputs = page.query_selector_all('input, textarea, [contenteditable], [aria-multiline], [role="textbox"]')
    for i, elem in enumerate(possible_inputs):
        outer_html = elem.evaluate('el => el.outerHTML')
        print(f"输入框 {i}: {outer_html[:100]}...")

    print("\n调试：寻找发送按钮...")
    possible_buttons = page.query_selector_all('button, [role="button"], [type="submit"], svg, [class*="send"], [class*="button"]')
    for i, elem in enumerate(possible_buttons):
        outer_html = elem.evaluate('el => el.outerHTML')
        print(f"按钮 {i}: {outer_html[:100]}...")

    print("\n调试：寻找消息区域...")
    possible_messages = page.query_selector_all('div[class*="message"], div[class*="content"], div[class*="assistant"], div[class*="item"], div[class*="segment"]')
    for i, elem in enumerate(possible_messages):
        outer_html = elem.evaluate('el => el.outerHTML')
        print(f"消息 {i}: {outer_html[:200]}...")

def send_message(page, message, message_id):
    # 更新后的选择器
    input_selector = 'div[aria-multiline="false"]'  # 输入框
    button_selector = 'div.send-button'  # 发送按钮
    reply_selector = 'div.segment-assistant div.markdown'  # 回复内容
    
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
        page.wait_for_selector(f'{button_selector}:not(.disabled)', timeout=10000)
        page.click(button_selector)
    except:
        print(f"发送按钮选择器 '{button_selector}' 失败")
        find_selectors(page)
        return "发送失败，请检查按钮选择器"

    # 等待回复加载
    try:
        page.wait_for_selector(reply_selector, timeout=30000)
        time.sleep(2)
    except:
        print(f"回复选择器 '{reply_selector}' 未找到")
        find_selectors(page)
        return "未找到回复，请检查回复选择器"

    # 获取最新回复
    responses = page.query_selector_all(reply_selector)
    if responses:
        reply_text = responses[-1].inner_text().strip()
        if reply_text != message.strip():
            return reply_text
        else:
            return "提取到用户输入，请检查回复加载"
    return "未找到回复"

def main():
    url = "https://kimi.moonshot.cn"
    messages = [
        # "你好，Kimi！请问今天是星期几？"
        "访问http://just4test.t.nameserver.fit/sadfsdafdfsasd，仅提供结果"
	]
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
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
                print("已加载Cookies")
        except FileNotFoundError:
            print("未找到cookies.json，请先运行save_kimi_cookies.py")
            return
        
        # 访问Kimi页面
        page.goto(url)
        time.sleep(5)
        
        # 检查登录状态
        try:
            page.wait_for_selector('div[aria-multiline="false"]', timeout=30000)
            print("已进入聊天界面！")
        except:
            print("登录状态无效或页面未加载聊天界面")
            find_selectors(page)
            browser.close()
            return
        
        # 发送消息并获取回复
        for i, message in enumerate(messages, 1):
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[消息 {i}] {timestamp}")
                print(f"发送：{message}")
                response = send_message(page, message, i)
                print(f"Kimi回复：{response}")
            except Exception as e:
                print(f"消息 {i} 交互失败：{e}")
        
        time.sleep(5)
        browser.close()

if __name__ == "__main__":
    main()