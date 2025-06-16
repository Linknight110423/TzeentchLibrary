# -*- coding: utf-8 -*-
import pandas as pd
import ollama
import re
import time
import os
from ollama import Client, ResponseError

def process_title_with_model(title):
    """使用ollama模型处理新闻标题"""
    my_prompt = f":::{title}:::这是使用爬虫爬取的网站内容其中有两类信息:::第一种是无关信息（如广告、网站的组成部分等），不给这种信息打标签；；；第二种是真正的新闻内容，依据新闻标题打标签（标签内容需要概括总结标题，如：政治、科技、美国、特朗普、大模型、人工智能、芯片、贸易等，至少包括三个维度：国家、领域（如科技、贸易、政治）、相关实体（如人物、机构等），每个维度里至少有一个标签），如果新闻标题涉及多个领域，请生成多个标签。标签请用<tags>#标签1#标签2#标签3</tags>这样的形式来呈现"

    client = Client("http://localhost:11434")
    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = client.generate(model='deepseek-r1:14b', prompt=my_prompt)
            return response.response
        except ResponseError as e:
            print(f"API 请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if e.status_code == 502 and attempt < max_retries - 1:
                print("等待5秒后重试...")
                time.sleep(5)
            else:
                raise
        except Exception as e:
            print(f"发生未知错误: {e}")
            raise

def process_news_from_csv(input_csv, output_csv):
    """逐条处理CSV文件中的新闻标题并立即写入结果"""
    df = pd.read_csv(input_csv)

    # 检查输出文件是否已存在，如果存在则删除
    if os.path.exists(output_csv):
        os.remove(output_csv)

    total = len(df)
    success_count = 0
    error_count = 0

    for index, row in df.iterrows():
        news_title = row['title']
        print(f"处理标题 ({index + 1}/{total}): {news_title}")

        try:
            model_response = process_title_with_model(news_title)
            tags_match = re.search(r'<tags>(.*?)</tags>', model_response)
            tags = tags_match.group(1) if tags_match else ""

            result = {
                'title': news_title,
                'model_response': model_response,
                'tags': tags,
                'success': True,
                'error': None
            }
            success_count += 1

        except Exception as e:
            print(f"处理标题时出错: {e}")
            result = {
                'title': news_title,
                'model_response': None,
                'tags': "",
                'success': False,
                'error': str(e)
            }
            error_count += 1

        # 将单条结果追加到CSV文件
        result_df = pd.DataFrame([result])

        # 如果文件不存在，写入表头；否则追加数据
        if not os.path.exists(output_csv):
            result_df.to_csv(output_csv, index=False)
        else:
            result_df.to_csv(output_csv, index=False, mode='a', header=False)

        print(f"已处理: {index + 1}/{total}, 成功: {success_count}, 失败: {error_count}")
        time.sleep(0.1)  # 防止过快请求

    print(f"处理完成。结果已保存到 {output_csv}")
    print(f"成功处理: {success_count}/{total}")
    print(f"失败处理: {error_count}/{total}")

# 使用示例
input_csv = 'webOutputs.csv'
output_csv = 'OllamaOutputs.csv'

process_news_from_csv(input_csv, output_csv)