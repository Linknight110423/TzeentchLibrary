import requests
from bs4 import BeautifulSoup
import csv
def get_news_titles_and_links(url):
    # 发送GET请求获取网页内容
    response = requests.get(url)
    # 如果不设定编码，可能会出现中文乱码
    response.encoding = response.apparent_encoding

    # 检查请求是否成功
    if response.status_code != 200:
        print("Failed to retrieve the webpage.")
        return []

    # 使用BeautifulSoup解析HTML内容
    soup = BeautifulSoup(response.text, 'html.parser')

    # 查找所有符合特征的 div 块：style 包含 'border-bottom:1px dashed #eee'
    news_divs = soup.find_all("div", style=lambda v: v and "border-bottom:1px dashed #eee" in v)

    rows = []
    for div in news_divs:
        # 找标题
        title_tag = div.find("h4")
        # 找正文：注意这次是在 div 里 class="articleP"
        content_div = div.find("div", class_="articleP")

        if not title_tag or not content_div:
            continue

        # 提取文本
        title = title_tag.get_text(strip=True)
        content = content_div.get_text(strip=True)

        # 这个网页里没看到明确的“来源标题”和“来源链接”，先留空
        source_title, source_link = "", ""

        # 存为字典，后续访问更直观
        rows.append({
            "title": title,
            "content": content,
            "source_title": source_title,
            "source_link": source_link
        })

    return rows




if __name__ == "__main__":
    # 使用示例
    url = 'http://k.caict.ac.cn/ekp/caict/km/zhaozixun/mzkyck_2212/202502/t20250228_655953.html' # 请替换为你真正的目标URL
    #csv_filename = "output.csv"
    csv_filename = input("请输入CSV文件名(如 output.csv,如果没有检测到则会直接创建一个): ").strip()
    #url = input("请输入要抓取的网页URL: "). strip()
    all_news = get_news_titles_and_links(url)


    # 这里打印示例
    for i, item in enumerate(all_news, 1):
        print(f"--- 第{i}条 ---")
        print(f"title: {item['title']}")
        print(f"content: {item['content']}")
        print(f"source_title: {item['source_title']}")
        print(f"source_link: {item['source_link']}")
        print()

    # **打开文件一次，写入所有数据**
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # **写表头**
        writer.writerow(["Index", "Title", "Content", "Source Title", "Source Link"])

        # **写数据**
        for i, item in enumerate(all_news, 1):
            writer.writerow([i, item['title'], item['content'], item['source_title'], item['source_link']])

    print(f"数据已写入 {csv_filename}")

