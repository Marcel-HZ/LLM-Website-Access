import json
from datetime import datetime

def analyze_results(sent_file="sent_messages.json", received_file="received_messages.json"):
    try:
        with open(sent_file, "r", encoding="utf-8") as f:
            sent_messages = json.load(f)
        with open(received_file, "r", encoding="utf-8") as f:
            received_messages = json.load(f)
    except FileNotFoundError as e:
        print(f"错误：未找到消息文件 {e}")
        return
    except json.JSONDecodeError as e:
        print(f"错误：JSON解析失败 {e}")
        return

    if not sent_messages or len(received_messages) <= 1:
        print("错误：消息文件为空或有效接收消息不足")
        return

    # 计算比特数（跳过第一条开启对话的消息）
    bits_per_char = 8
    total_sent_bits = sum(len(msg["message"]) * bits_per_char for msg in sent_messages)
    total_received_bits = sum(len(msg["message"]) * bits_per_char for msg in received_messages[1:])

    # 计算发送和接收速率（基于每个消息的时间戳）
    def calculate_rate(messages, total_bits):
        if not messages:
            return 0
        # 假设每个消息的timestamp是发送/接收的时刻
        timestamps = [datetime.strptime(msg["timestamp"], "%Y-%m-%d %H:%M:%S") for msg in messages]
        if len(timestamps) < 2:
            return 0
        # 计算每个消息的处理时间
        intervals = [(t2 - t1).total_seconds() for t1, t2 in zip(timestamps[:-1], timestamps[1:])]
        # 避免除以零，过滤掉无效间隔
        valid_intervals = [t for t in intervals if t > 0]
        if not valid_intervals:
            return 0
        avg_interval = sum(valid_intervals) / len(valid_intervals)
        # 速率 = 总比特数 / (消息数 * 平均间隔)
        return total_bits / (len(messages) * avg_interval) if avg_interval > 0 else 0

    upload_rate = calculate_rate(sent_messages, total_sent_bits)
    download_rate = calculate_rate(received_messages[1:], total_received_bits)

    # 计算正确率
    sent_list = [msg["message"] for msg in sent_messages]
    received_list = [msg["message"] for msg in received_messages[1:]]  # 跳过第一条
    correct_count = sum(1 for s, r in zip(sent_list, received_list) if s == r)
    total_messages = len(sent_messages)
    accuracy = (correct_count / total_messages) * 100 if total_messages > 0 else 0

    # 计算平均消息长度
    avg_message_length = sum(len(msg["message"]) for msg in received_messages[1:]) / total_messages if total_messages > 0 else 0

    # 输出分析结果
    print("\n=== 异步消息传输分析 ===")
    print(f"总消息数：{total_messages}")
    print(f"平均消息长度：{avg_message_length:.2f} 字符")
    print(f"发送端总比特数：{total_sent_bits} 比特")
    print(f"接收端总比特数：{total_received_bits} 比特")
    print(f"发送端上传速率：{upload_rate:.2f} 比特/秒")
    print(f"接收端下载速率：{download_rate:.2f} 比特/秒")
    print(f"正确消息数：{correct_count}")
    print(f"正确率：{accuracy:.2f}%")

if __name__ == "__main__":
    analyze_results()