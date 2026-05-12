#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
article_structure_parser.py  (v2 – grid‑CSV edition)
---------------------------------------------------
将采用传统中文政策文档层次（“一、… / （一）… / 一是…”）的文章解析为
两种结构化结果：

1. **layer.json** – 扁平层级表（code + text），与上一版保持兼容。
2. **grid.csv**  – 适配您截图中的拆解模板：
       A 列   → 标题（第 1 行）
       第 2 行 → 摘要句子，自 B 列起横向展开
       第 3 行起 → 正文层次（C = 一级标题，D = 二级标题，E = “一是…”，
                              F/G/H… = 句子）

用法
----
    # 只打印 JSON
    python article_structure_parser.py input.txt

    # 生成 grid.csv（输出文件名自由指定）
    python article_structure_parser.py input.txt --grid grid.csv

    # 同时生成三种格式
    python article_structure_parser.py input.txt -j layer.json -e layer.xlsx -g grid.csv

依赖：Python ≥3.8；若需导出 Excel，需额外安装 pandas & openpyxl。
"""

import re
import sys
import json
import csv
import argparse
from collections import OrderedDict
from typing import List, Dict, Tuple

try:
    import pandas as pd  # 可选：写 Excel
except ImportError:
    pd = None

# -------------------------- 基本工具 --------------------------- #
CN_NUMS = "一二三四五六七八九十"
CN_MAP = {c: i + 1 for i, c in enumerate(CN_NUMS)}

LEVEL1_RE = re.compile(r"^([%s]+)、\s*(.+)$" % CN_NUMS)
LEVEL2_RE = re.compile(r"^（([%s]+)）\s*(.+)$" % CN_NUMS)
LEVEL3_RE = re.compile(r"^([%s]+)是\s*(.+)$" % CN_NUMS)
SENT_SPLIT_RE = re.compile(r"(?<=[。．.!！?？])")


def split_sentences(text: str) -> List[str]:
    """按句号等终结符切分，并剔除空串。"""
    return [s.strip() for s in SENT_SPLIT_RE.split(text) if s.strip()]

# ------------------------ 解析核心 ----------------------------- #

def segment_article(lines: List[str]) -> Tuple[str, List[str], List[str]]:
    """粗分段：标题 / 摘要 / 正文 (返回正文起始索引)。"""
    title = ""
    abstract_lines, body_lines = [], []
    stage = "title"
    for line in lines:
        l = line.strip()
        if not l:
            continue
        if stage == "title":
            title = l
            stage = "abstract"
            continue
        # 遇到一级标题才算进入正文
        if LEVEL1_RE.match(l):
            stage = "body"
        if stage == "abstract":
            abstract_lines.append(l)
        else:
            body_lines.append(l)
    return title, abstract_lines, body_lines


def parse_body(lines: List[str]) -> OrderedDict:
    """把正文行解析成 {1: {title, subs:{1.1:{title, points:{1.1.1:{content,sentences}}}}}}"""
    doc: OrderedDict[str, Dict] = OrderedDict()
    l1 = l2 = l3 = None
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        m1 = LEVEL1_RE.match(line)
        if m1:
            idx = CN_MAP.get(m1.group(1))
            l1 = f"{idx}"
            doc[l1] = {"title": m1.group(2), "subs": OrderedDict()}
            l2 = l3 = None
            continue
        m2 = LEVEL2_RE.match(line)
        if m2 and l1:
            idx = CN_MAP.get(m2.group(1))
            l2 = f"{l1}.{idx}"
            doc[l1]["subs"][l2] = {"title": m2.group(2), "points": OrderedDict()}
            l3 = None
            continue
        m3 = LEVEL3_RE.match(line)
        if m3 and l2:
            idx = CN_MAP.get(m3.group(1))
            l3 = f"{l2}.{idx}"
            doc[l1]["subs"][l2]["points"][l3] = {"content": m3.group(2), "sentences": []}
            continue
        # 补充行→拼接到当前 l3
        if l3:
            p = doc[l1]["subs"][l2]["points"][l3]
            p["content"] += " " + line

    # 拆句
    for l1v in doc.values():
        for l2v in l1v["subs"].values():
            for p in l2v["points"].values():
                p["sentences"] = split_sentences(p["content"])
    return doc

# ----------------------- 扁平 & 网格导出 ----------------------- #

def flatten_layers(doc: OrderedDict) -> List[Dict[str, str]]:
    rows = []
    for l1k, l1v in doc.items():
        rows.append({"code": l1k, "text": l1v["title"]})
        for l2k, l2v in l1v["subs"].items():
            rows.append({"code": l2k, "text": l2v["title"]})
            for l3k, l3v in l2v["points"].values():
                rows.append({"code": l3k, "text": l3v["content"]})
                for i, s in enumerate(l3v["sentences"], 1):
                    rows.append({"code": f"{l3k}.{i}", "text": s})
    return rows


def build_grid(title: str, abstract_lines: List[str], body_tree: OrderedDict) -> List[List[str]]:
    grid: List[List[str]] = []

    # 计算最大列数动态扩展
    def ensure_cols(r: List[str], n: int):
        if len(r) < n:
            r.extend([""] * (n - len(r)))

    # Row 1 – Title in A (index 0)
    r_title = [title]
    grid.append(r_title)

    # Row 2 – Abstract sentences across from B (index 1)
    r_abs = [""]  # A 列留空
    abstract_txt = " ".join(abstract_lines)
    abs_sents = split_sentences(abstract_txt)
    r_abs.extend(abs_sents)
    grid.append(r_abs)

    # Body
    for l1v in body_tree.values():
        # 准备 row for 一级标题 & 首个二级标题（若有）
        base_row: List[str] = [""] * 3  # 至少到 C
        ensure_cols(base_row, 3)
        base_row[2] = l1v["title"]  # C 列 (idx2)

        l2s = list(l1v["subs"].values())
        if l2s:
            base_row.append(l2s[0]["title"])  # D (idx3)
            grid.append(base_row)
            # 处理二级标题的内容（首个）
            process_l2(l2s[0], grid)
            # 其余二级标题另外起行
            for l2v in l2s[1:]:
                row_l2 = [""] * 4  # 至少到 D
                ensure_cols(row_l2, 4)
                row_l2[3] = l2v["title"]
                grid.append(row_l2)
                process_l2(l2v, grid)
        else:
            grid.append(base_row)

    return grid


def process_l2(l2v: Dict, grid: List[List[str]]):
    """写入三级要点及句子。"""
    for p in l2v["points"].values():
        row = [""] * 5  # 至少到 E
        ensure_cols(row, 5)
        row[4] = p["content"]  # E 列 (idx4)
        # 句子从 F (idx5) 开始
        for j, sent in enumerate(p["sentences"], 5):
            ensure_cols(row, j + 1)
            row[j] = sent
        grid.append(row)

# ----------------------- 主函数 / CLI -------------------------- #

def main():
    parser = argparse.ArgumentParser(description="Parse Chinese policy‑style article into JSON/XLSX/CSV grid")
    parser.add_argument("input", help="plain‑text article file (UTF‑8)")
    parser.add_argument("--json", "-j", help="output JSON file (flattened layers)")
    parser.add_argument("--excel", "-e", help="output Excel file (flattened layers, two columns)")
    parser.add_argument("--grid", "-g", help="output CSV file (spreadsheet grid)")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        lines = f.readlines()

    title, abs_lines, body_lines = segment_article(lines)
    body_tree = parse_body(body_lines)

    # 输出 JSON
    flat_rows = flatten_layers(body_tree)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as jf:
            json.dump(flat_rows, jf, ensure_ascii=False, indent=2)
    else:
        print(json.dumps(flat_rows, ensure_ascii=False, indent=2))

    # Excel
    if args.excel:
        if pd is None:
            sys.exit("pandas/openpyxl 未安装，无法写 Excel。pip install pandas openpyxl")
        pd.DataFrame(flat_rows).to_excel(args.excel, index=False)

    # Grid CSV
    if args.grid:
        grid = build_grid(title, abs_lines, body_tree)
        # 用逗号分隔，Excel/Sheets 可直接打开
        with open(args.grid, "w", encoding="utf-8", newline="") as cf:
            writer = csv.writer(cf)
            for row in grid:
                writer.writerow(row)
        print(f"CSV grid written to {args.grid}")

if __name__ == "__main__":
    main()
