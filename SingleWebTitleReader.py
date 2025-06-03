import requests
from bs4 import BeautifulSoup

def get_news_titles_and_links(url):
    # 发送GET请求获取网页内容
    response = requests.get(url)

    # 检查请求是否成功
    if response.status_code != 200:
        print("Failed to retrieve the webpage.")
        return []

    # 使用BeautifulSoup解析HTML内容
    soup = BeautifulSoup(response.text, 'html.parser')

    # 找到所有新闻标题和链接
    news_items = []
    for article in soup.find_all('a', href=True):  # 找到所有<a>标签并且它们有href属性
        title = article.get_text(strip=True)
        link = article['href']

        # 过滤掉没有标题或者链接的条目
        if title and link:
            news_items.append({'title': title, 'link': link})

    return news_items

# 使用示例
url = 'http://k.caict.ac.cn/ekp/caict/km/zhaozixun/mzkyck_2212/202502/t20250228_655953.html'  # 替换成你需要抓取的新闻网站
news = get_news_titles_and_links(url)

# 输出抓取的标题和链接
for item in news:
    print(f"Title: {item['title']}")
    print(f"Link: {item['link']}")
    print('-' * 50)
