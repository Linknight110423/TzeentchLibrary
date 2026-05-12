#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crawl2mm_playwright.py
----------------------
Playwright 动态渲染抓取  ➜  NetworkX 构图  ➜  FreeMind (.mm) 导出
"""

import argparse, asyncio, itertools, json, pathlib, urllib.parse as up, xml.etree.ElementTree as ET
from typing import List, Dict

import networkx as nx, tqdm
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


# ────────────────────── 抓取层 ────────────────────── #
async def crawl_site(start: str, domain: str, depth_limit: int) -> List[Dict]:
    """
    使用 Playwright 递归抓取站内所有 <a href>，返回列表形式的节点字典：
        {url, title, parent}
    """
    visited, stack, items = set(), [(start, 0, None)], []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        while stack:
            url, depth, parent = stack.pop()
            if url in visited or (depth_limit and depth > depth_limit):
                continue
            visited.add(url)

            await page.goto(url, timeout=0)
            soup = BeautifulSoup(await page.content(), "lxml")
            title = (soup.title.string.strip() if soup.title else url)

            items.append({"url": url, "title": title, "parent": parent})

            for a in soup.select("a[href]"):
                child = up.urljoin(url, a["href"].split("#")[0])
                netloc = up.urlparse(child).netloc
                if netloc.endswith(f".{domain}") or netloc == domain:
                    stack.append((child, depth + 1, url))

        await browser.close()
    return items


# ────────────────────── 拓扑层 ────────────────────── #
def build_graph(nodes: List[Dict]) -> nx.DiGraph:
    G = nx.DiGraph()
    for n in tqdm.tqdm(nodes, desc="Build graph"):
        G.add_node(n["url"], title=n["title"])
        if n["parent"]:
            G.add_edge(n["parent"], n["url"])
    return G


def pick_root(G: nx.DiGraph) -> str:
    candidates = [n for n in G.nodes if G.in_degree(n) == 0]
    return min(candidates, key=len) if candidates else next(iter(G.nodes))


# ────────────────────── 导出层 ────────────────────── #
def nx_to_freemind_bytes(G: nx.DiGraph, root: str) -> bytes:
    """NetworkX ➜ FreeMind .mm 字节串"""
    id_iter = (f"ID_{i}" for i in itertools.count(1))

    def build(el_parent: ET.Element, cur: str):
        node_el = ET.SubElement(
            el_parent, "node",
            {"ID": next(id_iter), "TEXT": G.nodes[cur].get("title") or cur}
        )
        for child in G.successors(cur):
            build(node_el, child)

    map_el = ET.Element("map", {"version": "0.9.0"})
    build(map_el, root)
    return ET.tostring(map_el, encoding="utf-8", xml_declaration=True)


# ────────────────────── 主入口 ────────────────────── #
def main():
    parser = argparse.ArgumentParser(
        description="Playwright 抓取 ➜ FreeMind 思维导图 (.mm)")
    parser.add_argument("--start",  default="https://www.cybersac.cn/",
                        help="起始 URL")
    parser.add_argument("--domain", default="cybersac.cn",
                        help="主域名(用于站内判断)")
    parser.add_argument("--depth",  type=int, default=0,
                        help="最大递归深度 (0 表示不限制)")
    parser.add_argument("--output", default="site_map.mm",
                        help="输出 .mm 文件名")
    args = parser.parse_args()

    print(f"🔍  Crawling {args.start} …")
    nodes = asyncio.run(crawl_site(args.start, args.domain, args.depth))

    print("🔄  Building graph …")
    G = build_graph(nodes)
    root = pick_root(G)
    print(f"📌  Root node: {root}")

    print("🧠  Exporting FreeMind …")
    mm_bytes = nx_to_freemind_bytes(G, root)
    pathlib.Path(args.output).write_bytes(mm_bytes)
    print(f"✅  完成！FreeMind 文件已生成：{pathlib.Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
