import pandas as pd
import ollama
import re
def process_title_with_model(title):
    """
    使用ollama模型处理新闻标题
    """
my_prompt = f"：：：{title}：：：这是使用爬虫爬取的网站内容其中有两类信息：：：第一种是无关信息（如广告、网站的组成部分等），不给这种信息打标签；；；第二种是真正的新闻内容，依据新闻标题打标签（标签内容需要概括总结标题，如：政治、科技、美国、特朗普、大模型、人工智能、芯片、贸易等），如果新闻标题涉及多个领域，请生成多个标签。"
    # 调用本地模型进行生成
    response = ollama.generate(model='deepseek-r1:7b', prompt=my_prompt)

    # 获取模型返回的响应内容
    actual_response = response['response']
    return actual_response

def process_news_from_csv(input_csv, output_csv):
    """
    从CSV文件读取新闻标题，使用ollama模型进行处理，并将结果保存到新的CSV文件
    """
    # 读取CSV文件中的新闻标题列
    df = pd.read_csv(input_csv)

    # 创建一个空列表来保存处理结果
    all_news = []

    # 遍历所有新闻标题并进行模型处理
    for index, row in df.iterrows():
        news_title = row['title']  # CSV文件中有一列名为'title'
        print(f"Processing title: {news_title}")

        # 使用模型处理标题
        model_response = process_title_with_model(news_title)
        # 提取model_response中的标签部分 <tags>#标签1#标签2#...</tags>
        tags_match = re.search(r'<tags>(.*?)</tags>', model_response)
        tags = tags_match.group(1) if tags_match else ""  # 如果匹配到标签则提取，否则返回空字符串
        # 将新闻标题、模型响应和提取的标签添加到结果列表
        all_news.append({
            'title': news_title,
            'model_response': model_response,
            'tags': tags  # 添加标签字段
        })

    # 将处理结果写入CSV文件
    result_df = pd.DataFrame(all_news)
    result_df.to_csv(output_csv, index=False)
    print(f"Finished processing. Results saved to {output_csv}")


# 使用示例
input_csv = 'webOutputs.csv'  # 输入的CSV文件路径
output_csv = 'OllamaOutputs.csv'  # 输出的CSV文件路径

# 批量处理新闻标题并保存结果
process_news_from_csv(input_csv, output_csv)
