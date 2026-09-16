from zhipuai import ZhipuAI

client = ZhipuAI(api_key="fd20930f1f0c455fa3b79a567aa6b939.vkfpkBz3anHOKq8p")

tools = [{
    "type": "web_search",
    "web_search": {
        "enable": True,
        "search_query": "进行网页摘要"
    }
}]

messages = [{
    "role": "user",
    "content": "http://just4test.t.nameserver.fit/sadfsdafdfsasd，提取内容"
}]

response = client.chat.completions.create(
    model="GLM-4-Plus",
    messages=messages,
    tools=tools
)
print(response.choices[0].message)