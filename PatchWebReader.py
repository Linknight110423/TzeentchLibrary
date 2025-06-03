import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import datetime

def get_news_titles_and_links(url):
    """
    爬取指定网页的新闻标题和链接
    """
    try:
        # 发送GET请求获取网页内容
        response = requests.get(url)

        # 检查请求是否成功
        if response.status_code != 200:
            print(f"Failed to retrieve the webpage: {url}")
            return []

        # 使用BeautifulSoup解析HTML内容
        soup = BeautifulSoup(response.text, 'html.parser')

        # 存储新闻标题和链接
        news_items = []

        # 假设新闻标题和链接在<a>标签内，并且有href属性
        for article in soup.find_all('a', href=True):
            title = article.get_text(strip=True)
            link = article['href']

            # 过滤掉没有标题或者链接的条目，标题小于三个单词的也过滤掉
            if title and link:
                words_in_title = len(title.split())  # 分割标题并计算单词数
                if words_in_title >= 7:  # 如果标题有 xx或更多单词
                    news_items.append({'title': title, 'link': link})

        return news_items
    except Exception as e:
        print(f"Error while processing {url}: {e}")
        return []

def batch_scrape_from_csv(input_csv, output_csv):
    """
    从CSV文件读取URL，批量爬取新闻标题和链接，保存到新的CSV文件
    """
    # 读取CSV文件中的URL列
    df = pd.read_csv(input_csv)

    # 创建一个空列表来保存所有爬取的结果
    all_news = []

    # 遍历所有URL并爬取新闻
    for index, row in df.iterrows():
        url = row['url']  # 网址的tiltie
        print(f"Scraping {url}...")
        news = get_news_titles_and_links(url)

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 将结果添加到all_news列表
        # 将每个新闻项加入结果列表，同时附上当前日期时间
        for item in news:
            all_news.append({
                'source_url': url,
                'title': item['title'],
                'link': item['link'],
                'scraped_at': current_time  # 当前的日期时间
            })

        # 延时2秒，避免过于频繁请求
        time.sleep(2)

    print(all_news)
    result_df = pd.DataFrame(all_news)
    result_df.to_csv(output_csv, index=False)
    print(f"Finished scraping. Results saved to {output_csv}")


# 使用示例
input_csv = 'webInputs.csv'  # 输入CSV文件路径
output_csv = 'webOutputs.csv'  # 输出的CSV文件路径

# 批量爬取并保存结果
batch_scrape_from_csv(input_csv, output_csv)
