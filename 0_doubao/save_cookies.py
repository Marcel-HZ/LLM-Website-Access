from playwright.sync_api import sync_playwright
import json

def save_cookies():
    with sync_playwright() as p:
        # 启动浏览器（显示窗口）
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # 访问登录页面
        page.goto("https://www.doubao.com/chat")
        
        # 等待用户手动登录
        print("请在浏览器中完成手机号登录（包括验证码），登录成功后按Enter...")
        input()
        
        # 保存Cookies
        cookies = context.cookies()
        with open("cookies.json", "w") as f:
            json.dump(cookies, f)
        print("Cookies已保存到cookies.json")
        
        # 关闭浏览器
        browser.close()

if __name__ == "__main__":
    save_cookies()