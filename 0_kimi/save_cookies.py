from playwright.sync_api import sync_playwright
import json
import time

def find_selectors(page):
    """调试：打印可能的输入框和其他关键元素"""
    print("调试：当前页面URL:", page.url)
    print("调试：页面标题:", page.title())
    print("调试：寻找输入框...")
    possible_inputs = page.query_selector_all('input, textarea, [contenteditable]')
    for i, elem in enumerate(possible_inputs):
        outer_html = elem.evaluate('el => el.outerHTML')
        print(f"输入框 {i}: {outer_html[:100]}...")

    print("\n调试：寻找按钮（登录、发送等）...")
    possible_buttons = page.query_selector_all('button, [role="button"], [type="submit"]')
    for i, elem in enumerate(possible_buttons):
        outer_html = elem.evaluate('el => el.outerHTML')
        print(f"按钮 {i}: {outer_html[:100]}...")

    print("\n调试：寻找消息区域...")
    possible_messages = page.query_selector_all('div[class*="message"], div[class*="content"], div[class*="assistant"]')
    for i, elem in enumerate(possible_messages):
        outer_html = elem.evaluate('el => el.outerHTML')
        print(f"消息 {i}: {outer_html[:200]}...")

def save_kimi_cookies():
    url = "https://kimi.moonshot.cn/chat"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()
        
        # 访问Kimi登录页面
        page.goto(url)
        time.sleep(5)  # 等待页面初始加载
        print("请在浏览器中完成登录（输入手机号、验证码等），登录成功后按Enter...")
        print("注意：如果看到Cloudflare验证页面，请手动完成验证。")
        
        # 等待用户手动登录
        input()
        
        # 检查是否被Cloudflare拦截
        if "Just a moment" in page.title() or "cf-" in page.content():
            print("检测到Cloudflare验证，请手动完成验证后再按Enter...")
            input()
        
        # 延长等待，检查聊天界面
        print("检查登录状态...")
        try:
            # 更宽泛的选择器，包含可能的输入框类型
            page.wait_for_selector('input, textarea, [contenteditable], [role="textbox"]', timeout=30000)
            print("检测到聊天界面，登录成功！")
        except:
            print("未找到聊天输入框，可能的原因：")
            print("1. 输入框选择器不正确")
            print("2. 页面未完全加载")
            print("3. 反爬机制（如Cloudflare）")
            print("4. 未跳转到聊天界面")
            find_selectors(page)
            browser.close()
            return
        
        # 保存Cookies
        cookies = context.cookies()
        if not cookies:
            print("未获取到Cookies，可能未成功登录")
            browser.close()
            return
        
        with open("cookies.json", "w") as f:
            json.dump(cookies, f, indent=2)
        print("Cookies已保存到cookies.json")
        
        # 打印Cookies以供检查
        print("保存的Cookies：")
        for cookie in cookies:
            print(f"Name: {cookie['name']}, Value: {cookie['value'][:50]}...")
        
        browser.close()

if __name__ == "__main__":
    save_kimi_cookies()