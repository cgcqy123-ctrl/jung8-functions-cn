# -*- coding: utf-8 -*-
"""极简 Markdown 解析器：只支持本项目用到的子集。

支持：# / ## / ### 标题、段落、- 无序列表、1. 有序列表、> 引用、| 管道表格、**加粗**、
空行分块。其余语法原样当普通文字处理。
"""
from __future__ import annotations

import re

TABLE_SEP = re.compile(r"^\|?[\s:\-|]+\|?$")
BULLET = re.compile(r"^[-*]\s+(.*)$")
ORDERED = re.compile(r"^(\d+)[.、]\s*(.*)$")


def _cells(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def parse_md(text: str) -> list[dict]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: list[dict] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        # 分隔线
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", stripped):
            i += 1
            continue
        # 代码块：整块跳过（本项目不用，防意外）
        if stripped.startswith("```"):
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                i += 1
            i += 1
            continue
        # 标题
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            blocks.append({"type": f"h{min(level, 3)}", "text": stripped[level:].strip()})
            i += 1
            continue
        # 表格
        if stripped.startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                if not TABLE_SEP.match(lines[i].strip()):
                    rows.append(_cells(lines[i]))
                i += 1
            if rows:
                blocks.append({"type": "table", "rows": rows})
            continue
        # 引用
        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            blocks.append({"type": "quote", "text": "".join(buf)})
            continue
        # 无序列表
        if BULLET.match(stripped):
            items = []
            while i < n and BULLET.match(lines[i].strip()):
                items.append(BULLET.match(lines[i].strip()).group(1))
                i += 1
            blocks.append({"type": "ul", "items": items})
            continue
        # 有序列表
        if ORDERED.match(stripped):
            items = []
            while i < n and ORDERED.match(lines[i].strip()):
                items.append(ORDERED.match(lines[i].strip()).group(2))
                i += 1
            blocks.append({"type": "ol", "items": items})
            continue
        # 段落：连续非空、且不是其他块的行
        buf = []
        while i < n:
            s = lines[i].strip()
            if (not s or s.startswith(("#", "|", ">", "```"))
                    or BULLET.match(s) or ORDERED.match(s)):
                break
            buf.append(s)
            i += 1
        if buf:
            blocks.append({"type": "p", "text": "".join(buf)})
    return blocks
