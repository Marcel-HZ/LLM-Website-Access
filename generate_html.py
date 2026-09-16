from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    table_data = [
        ["邮箱：", "abc@foxmail.com"],  # 第一行：邮箱标签和邮箱地址
        ["备用邮箱：", "def@gmail.com"]  # 第二行：另一个邮箱标签和邮箱地址（示例）
    ]

    # 生成表格的HTML代码
    table_html = ''.join([
        '<tr>' + ''.join([f'<td>{row[j]}</td>' for j in range(len(row))]) + '</tr>' for row in table_data
    ])

    html = f'''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>TEST</title>
    <style>
      body, html {{
        height: 100%;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        background-color: #e6e6fa; /* 淡紫色背景 */
      }}
      .container {{
        width: 100%;  /* 确保容器宽度为100% */
        max-width: 100%; /* 防止在宽屏设备上溢出 */
      }}
      h1 {{
        width: 100%;
        text-align: center;
        font-size: 3em;
        margin: 20px 0;
        color: #4b0082; /* 深紫色标题 */
      }}
      table {{
        width: 90vw; /* 使用 vw 单位确保表格宽度是视口宽度的90% */
        border-collapse: collapse;
        margin: 0 auto; /* 居中表格 */
        background-color: #f5f5f5; /* 浅灰色表格背景 */
      }}
      td {{
        border: 1px solid #800080; /* 紫色边框 */
        height: 80px; /* 维持单元格高度 */
        width: 10%;  /* 每个单元格宽度为表格宽度的10% */
        background-color: white;
        text-align: center;
      }}
    </style>
  </head>
  <body>
    <div class="container">
      <h1>TEST</h1>
      <table>{table_html}</table>
    </div>
  </body>
</html>
    '''
    return render_template_string(html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)