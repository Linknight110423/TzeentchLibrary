import requests, time, random, csv
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://www.foxnews.com/"          # 目标站点
SEED =  "/latest"                          # 起始列表页

HEADERS = {
    "User-Agent": "MyNewsCrawler/1.0 (+https://github.com/you)"
}
DELAY   = (1, 3)                           # 抓取间隔范围

def fetch(url):
    """下载页面并返回 Soup 对象"""
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")

def parse_list(url):
    soup = fetch(url)
    # 根据实际 HTML 结构修改选择器
    for a in soup.select("h2>a.article-link"):
        yield urljoin(BASE, a["href"])
    next_page = soup.select_one("a.next")   # 翻页
    if next_page:
        time.sleep(random.uniform(*DELAY))
        yield from parse_list(urljoin(BASE, next_page["href"]))

def parse_article(url):
    soup = fetch(url)
    return {
        "url"   : url,
        "title" : soup.select_one("h1.headline").text.strip(),
        "date"  : soup.select_one("time")["datetime"],
        "body"  : "\n".join(p.text.strip() for p in soup.select("div.article-body p"))
    }

def crawl(seed):
    with open("news.csv", "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "title", "date", "body"])
        writer.writeheader()
        for article_url in parse_list(seed):
            data = parse_article(article_url)
            writer.writerow(data)
            print("Saved:", data["title"])
            time.sleep(random.uniform(*DELAY))

if __name__ == "__main__":
    crawl(urljoin(BASE, SEED))
