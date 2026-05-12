#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crawl_caict_pdfs.py   –   批量下载 online_bqbh.jsp 列出的所有 PDF
用法：
    python crawl_caict_pdfs.py "http://k.caict.ac.cn/ekp/caict/km/bqbh/online_bqbh.jsp?..." \
                               "JSESSIONID=20D79383FFD47A42BAD21CDC365274B9"
"""
"""
REM ① 把 filePath= 后面那一长串 Base64 放进变量
set "B64=V0NNL1AwMjAyNTA0L1AwMjAyNTA0MDMvUDAyMDI1MDQwMzUxODYyODU3MTgyMi5wZGY="

REM ② 浏览器 DevTools 复制整串 Cookie
set "CK=JSESSIONID=20D79383FFD47A42BAD21CDC365274B9; EKPSSID=6B1E4C..."

REM ③ 当前毫秒
for /f %%a in ('powershell -NoProfile -Command "(Get-Date).ToUniversalTime().ToString('yyyyMMddHHmmssfff')"') do set TS=%%a

REM ④ 真正下载
curl -L -C - -e "http://k.caict.ac.cn/" ^
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) ..." ^
  -H "Cookie: %CK%" ^
  -o "2024-T-011.pdf" ^
  "http://k.caict.ac.cn/root/getFile.do?filePath=%TS%%B64%"


"""
import sys
import re
import time
import base64
import pathlib
import urllib.parse as up
import requests
from bs4 import BeautifulSoup
from unittest.mock import patch

def test_script():
    """测试脚本功能"""
    with patch('sys.argv', ['script.py', 'http://k.caict.ac.cn/ekp/caict/km/zhaochengguo/kjcg/202407/t20240717_487532.html', 'JSESSIONID=20D79383FFD47A42BAD21CDC365274B9']):
        try:
            main()
            print("测试运行成功")
        except SystemExit as e:
            print(f"测试退出: {e}")
        except Exception as e:
            print(f"测试失败: {e}")

def main():
    # 检查命令行参数
    if len(sys.argv) < 3:
        sys.exit("用法: python crawl_caict_pdfs.py <母页面 URL> <Cookie(JSESSIONID=...)>")

    # 解析参数
    MOTHER_URL = sys.argv[1]
    COOKIE = {"JSESSIONID": sys.argv[2].split("=", 1)[-1]}

    # 创建会话并设置请求头
    with requests.Session() as sess:
        sess.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": MOTHER_URL,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })
        sess.cookies.update(COOKIE)

        print("→ 抓取母页面 …")
        try:
            response = sess.get(MOTHER_URL, timeout=15)
            response.raise_for_status()
            html = response.text
        except requests.RequestException as e:
            sys.exit(f"❌ 无法访问母页面: {e}")

        soup = BeautifulSoup(html, "lxml")

        # 提取所有online_bqbh.jsp链接
        base_url = up.urljoin(MOTHER_URL, '/')  # 获取基URL
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "online_bqbh.jsp" in href:
                # 转换为绝对URL
                absolute_url = up.urljoin(base_url, href)
                links.append(absolute_url)

        if not links:
            sys.exit("❌ 母页面里没找到任何 online_bqbh.jsp 链接；检查是否登陆成功？")

        print(f"找到 {len(links)} 个链接，开始下载 …")

        # 创建保存目录
        output_dir = pathlib.Path("downloaded_pdfs")
        output_dir.mkdir(exist_ok=True)

        for idx, href in enumerate(links, 1):
            try:
                # 解析URL参数
                qs = up.parse_qs(up.urlparse(href).query)
                b64 = qs.get("filePath", [""])[0]
                if not b64:
                    print(f"[{idx}] 跳过（无 filePath）")
                    continue

                # 尝试使用原始域名而非内网IP
                ts = str(int(time.time() * 1000))
                parsed_mother = up.urlparse(MOTHER_URL)
                base_domain = f"{parsed_mother.scheme}://{parsed_mother.netloc}"
                getf = f"{base_domain}/root/getFile.do?filePath={ts}{b64}"

                # 还原文件名
                try:
                    raw_path = base64.b64decode(b64).decode("utf-8")
                    fname = pathlib.Path(raw_path).name
                    # 过滤文件名中的非法字符
                    valid_fname = re.sub(r'[\\/:*?"<>|]', '_', fname)
                except Exception:
                    valid_fname = f"file_{idx}.pdf"

                file_path = output_dir / valid_fname

                print(f"[{idx:02d}] {valid_fname}  ←  正在下载 …", end="", flush=True)

                # 下载文件
                r = sess.get(getf, stream=True, timeout=30)
                r.raise_for_status()

                # 检查内容类型
                content_type = r.headers.get("Content-Type", "")
                if "pdf" not in content_type.lower():
                    raise RuntimeError(f"返回类型不匹配: {content_type}")

                # 保存文件
                with open(file_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                print(" ✅")

                # 控制下载速度，避免被封
                time.sleep(0.5)

            except Exception as e:
                print(f" ⚠ 失败：{e}")

    print("全部完成。")

if __name__ == '__main__':
    #main()

    test_script()