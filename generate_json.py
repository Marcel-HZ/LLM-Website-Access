from flask import Flask, jsonify, request
import logging

app = Flask(__name__)

# 创建一个自定义的日志处理器，用于将含有访问URL的数据保存到文件
class URLAccessFileHandler(logging.FileHandler):
    def emit(self, record):
        if 'URL:' in record.getMessage():
            super().emit(record)

# 设置日志记录
log_filename = 'access.log'

# 配置文件日志处理器
file_handler = URLAccessFileHandler(log_filename)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s %(message)s')
file_handler.setFormatter(file_formatter)

# 配置控制台日志处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s %(message)s')
console_handler.setFormatter(console_formatter)

# 获取根日志记录器并添加处理器
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

@app.route('/<path:path>')
def catch_all(path):
    client_ip = request.remote_addr
    url_accessed = request.url
    log_message = f'IP: {client_ip} URL: {url_accessed}'
    logging.info(log_message)  # 记录IP地址和访问的URL
    results = {
        "results": path
    }
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)