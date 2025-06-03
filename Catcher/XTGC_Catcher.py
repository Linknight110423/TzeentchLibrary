import requests
from bs4 import BeautifulSoup
import csv
def parse_news(url):
    # 1. 请求页面
    response = requests.get(url)
    # 避免出现中文乱码
    response.encoding = response.apparent_encoding

    # 2. 判断是否请求成功
    if response.status_code != 200:
        print("Failed to retrieve the webpage:", url)
        return []

    # 3. 用BeautifulSoup解析
    soup = BeautifulSoup(response.text, 'html.parser')

    # 4. 找到包含资讯的div容器（style属性包含 'border-bottom:1px dashed #eee'）
    items_divs = soup.find_all(
        "div",
        style=lambda x: x and "border-bottom:1px dashed #eee" in x
    )

    news_list = []
    for div in items_divs:
        # ---- A. 标题 ----
        h4_tag = div.find("h4")
        if not h4_tag:
            # 没有标题就跳过
            continue
        title = h4_tag.get_text(strip=True)

        # ---- B. 正文内容 ----
        #   网页结构：正文在 <p style="text-align:justify"> 中
        #   找第一个满足条件的 p 即可
        content_p = div.find("p", attrs={"style":"text-align:justify"})
        if not content_p:
            # 没有正文也跳过
            continue
        content = content_p.get_text(strip=True)

        # ---- C. 来源信息 ----
        #   <p class="fr">来源：<a href="xxx">xxx</a></p>
        source_p = div.find("p", class_="fr")
        if source_p:
            # 提取 a 标签
            source_a = source_p.find("a")
            if source_a:
                source_title = source_a.get_text(strip=True)
                source_link = source_a.get("href", "")
            else:
                source_title = ""
                source_link = ""
        else:
            source_title = ""
            source_link = ""

        # 收集该条记录
        news_list.append({
            "title": title,
            "content": content,
            "source_title": source_title,
            "source_link": source_link
        })

    return news_list



if __name__ == "__main__":
    # 使用示例
    url = "http://k.caict.ac.cn/ekp/caict/km/zhaozixun/mzkjgc/qsnew2/202502/t20250214_654039.html"  # 请替换为你真正的目标URL
    csv_filename = "output.csv"
    #csv_filename = input("请输入CSV文件名(如 output.csv): ").strip()
    #url = input("请输入要抓取的网页URL: "). strip()
    all_news = parse_news(url)


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


    # 将结果保存CSV