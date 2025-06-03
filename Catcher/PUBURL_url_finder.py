import re

html_text = "http://k.caict.ac.cn"  # 请替换为你的实际网页内容

# 正则匹配所有URL
pattern = r'/ekp/caict/km/pub/wcmpage\.jsp\?URL=(https?://[^\s"\']+)'
matches = re.findall(pattern, html_text)

# 生成完整URL
base_url = "http://k.caict.ac.cn/ekp/caict/km/pub/wcmpage.jsp?URL="
full_urls = [base_url + match for match in matches]

# 打印所有网址
for url in full_urls:
    print(url)
