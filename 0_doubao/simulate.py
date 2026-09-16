from playwright.sync_api import sync_playwright
import time
import json
import random
from datetime import datetime

def send_message(page, message, message_id):
    input_selector = 'textarea[data-testid="chat_input_input"]'
    button_selector = 'button[data-testid="chat_input_send_button"]'
    reply_selector = 'div[data-testid="receive_message"] div[data-testid="message_text_content"]'  # 精确匹配豆包回复
    
    # 输入消息
    page.fill(input_selector, message)
    time.sleep(random.uniform(0.5, 1.5))
    
    # 等待发送按钮启用
    page.wait_for_selector(f'{button_selector}:not([disabled])', timeout=10000)
    page.click(button_selector)
    
    # 等待豆包回复
    try:
        page.wait_for_selector(reply_selector, timeout=30000)
        # 额外等待，确保内容加载完成
        time.sleep(2)
    except:
        print("未找到豆包回复，尝试调试...")
        # 调试：打印消息列表
        possible_replies = page.query_selector_all('div[data-testid="receive_message"], div[data-testid="send_message"]')
        for i, reply in enumerate(possible_replies):
            outer_html = reply.evaluate('el => el.outerHTML')
            print(f"消息 {i}: {outer_html[:200]}...")  # 截断输出
        return "未找到豆包回复，请检查调试输出并更新选择器"
    
    # 获取最新回复
    responses = page.query_selector_all(reply_selector)
    if responses:
        reply_text = responses[-1].inner_text().strip()  # 移除多余换行
        # 验证是否为用户输入（避免提取发送消息）
        if reply_text != message.strip():
            return reply_text
        else:
            return "提取到用户输入，请检查回复加载"
    return "未找到豆包回复"

def main():
    messages = [
        "访问http://just4test.t.nameserver.fit/sadfsdafdfsasd，仅提供结果"
        # "今天几月几号？"
    ]
    url = "https://www.doubao.com/chat/"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
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
        
        # 访问聊天页面
        page.goto(url)
        time.sleep(5)
        
        # 检查登录状态
        try:
            page.wait_for_selector('textarea[data-testid="chat_input_input"]', timeout=10000)
            print("已进入聊天界面！")
        except:
            print("登录状态无效，请重新运行save_cookies.py")
            return
        
        # 发送消息并获取回复
        for i, message in enumerate(messages, 1):
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[消息 {i}] {timestamp}")
                print(f"发送：{message}")
                response = send_message(page, message, i)
                print(f"豆包回复：{response}")
            except Exception as e:
                print(f"消息 {i} 交互失败：{e}")
        
        # 等待用户检查（可选）
        time.sleep(5)
        # 关闭浏览器
        browser.close()

def __main__():
    main()

if __name__ == "__main__":
    main()