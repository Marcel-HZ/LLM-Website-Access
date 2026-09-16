from typing import *
import json
from openai import OpenAI, RateLimitError
from openai.types.chat.chat_completion import Choice
import time
import httpx  # 需要安装 httpx 库：pip install httpx

# 初始化 OpenAI 客户端
client = OpenAI(
    base_url="https://api.moonshot.cn/v1",
    api_key="sk-EEs7GJMUDR3yjFcmjguCKxNkvLyMHhsk8HtDoZqEN0sTuOyF",  # 你的 API Key
)

def search_impl(arguments: Dict[str, Any]) -> Any:
    return arguments

def crawl_impl(url: str) -> str:
    try:
        r = httpx.get(url, timeout=10.0)
        r.raise_for_status()
        return r.text
    except httpx.HTTPError as e:
        return f"抓取网页失败: {str(e)}"

def crawl(arguments: dict) -> str:
    url = arguments.get("url", "")
    content = crawl_impl(url)
    return {"content": content}

def chat(messages) -> Choice:
    completion = client.chat.completions.create(
        model="moonshot-v1-128k",
        messages=messages,
        temperature=0.3,
        tools=[
            {
                "type": "builtin_function",
                "function": {
                    "name": "$web_search",
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "crawl_url",
                    "description": "根据 URL 抓取网页内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "要抓取的网页 URL"}
                        },
                        "required": ["url"]
                    }
                }
            }
        ]
    )
    usage = completion.usage
    choice = completion.choices[0]

    if choice.finish_reason == "stop":
        print(f"chat_prompt_tokens:          {usage.prompt_tokens}")
        print(f"chat_completion_tokens:      {usage.completion_tokens}")
        print(f"chat_total_tokens:           {usage.total_tokens}")

    return choice

def main():
    messages = [
        {"role": "system", "content": "你是一个智能助手，可以使用 $web_search 工具进行联网搜索，或使用 crawl_url 工具抓取指定网页内容。"}
    ]

    while True:
        user_input = input("你: ")
        if user_input.lower() in ["exit", "quit"]:
            print("对话结束。")
            break

        messages.append({"role": "user", "content": user_input})

        finish_reason = None
        while finish_reason is None or finish_reason == "tool_calls":
            choice = chat(messages)
            finish_reason = choice.finish_reason

            if finish_reason == "tool_calls":
                messages.append(choice.message)
                for tool_call in choice.message.tool_calls:
                    tool_call_name = tool_call.function.name
                    tool_call_arguments = json.loads(tool_call.function.arguments)

                    if tool_call_name == "$web_search":
                        print(f"调用 $web_search，查询: {tool_call_arguments.get('query')}")
                        tool_result = search_impl(tool_call_arguments)
                    elif tool_call_name == "crawl_url":
                        print(f"调用 crawl_url，URL: {tool_call_arguments.get('url')}")
                        tool_result = crawl(tool_call_arguments)
                    else:
                        tool_result = {"error": f"未知工具: {tool_call_name}"}

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call_name,
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })
            elif finish_reason == "stop":
                print(f"Kimi: {choice.message.content}")

        time.sleep(20)

if __name__ == '__main__':
    main()