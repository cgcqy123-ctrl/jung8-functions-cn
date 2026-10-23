# -*- coding: utf-8 -*-
"""成品 docx 的结构性验收：占位符残留、题目数、类型数、Markdown 漏网字符。"""
import os
import sys

from docx import Document

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCX = os.path.join(BASE, "荣格八维人格测验-中国情境版.docx")
CODES = ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
         "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"]
JUNG = ["外倾思维型", "内倾思维型", "外倾情感型", "内倾情感型",
        "外倾感觉型", "内倾感觉型", "外倾直觉型", "内倾直觉型"]


def main() -> int:
    if not os.path.exists(DOCX):
        print("缺少 docx")
        return 1
    doc = Document(DOCX)
    paras = [p.text for p in doc.paragraphs]
    alltext = "\n".join(paras)
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                alltext += "\n" + cell.text
    errors, warns = [], []

    for bad in ("〔缺少", "{{TABLE", "```", "**", "{{"):
        if bad in alltext:
            errors.append(f"残留标记 {bad!r}（{alltext.count(bad)} 处）")
    if "\n---\n" in alltext or any(p.strip() == "---" for p in paras):
        warns.append("仍有分隔线 --- 被当正文渲染")

    n_a = sum(1 for p in paras if p.startswith("A　"))
    n_b = sum(1 for p in paras if p.startswith("B　"))
    print(f"段落 {len(paras)} 段；表格 {len(doc.tables)} 个；正文约 {len(alltext)} 字")
    print(f"选项行：A {n_a} 条 / B {n_b} 条（应为 64 / 64）")
    if n_a != 64 or n_b != 64:
        errors.append(f"题目选项行数不对：A={n_a} B={n_b}（应各 64）")

    missing = [c for c in CODES if f"{c}｜" not in alltext]
    if missing:
        errors.append(f"缺少十六型画像：{missing}")
    miss_j = [j for j in JUNG if f"{j}（" not in alltext]
    if miss_j:
        errors.append(f"缺少荣格类型：{miss_j}")

    for token in ("写在前面", "第一章", "第二章", "第三章", "第四章", "第五章", "第六章",
                  "第七章", "第八章", "附录 A", "附录 B", "附录 C", "目　录"):
        if token not in alltext:
            errors.append(f"缺少章节：{token}")

    # 每章是否有实质内容（用字数粗判）
    print("\n章节篇幅（按一级标题切分）：")
    heads = [(p.style.name == "Heading 1", p.text.strip()) for p in doc.paragraphs]
    body = [p.text for p in doc.paragraphs]
    idx = [(i, t) for i, (is_h1, t) in enumerate(heads) if is_h1]
    for k, (i, name) in enumerate(idx):
        end = idx[k + 1][0] if k + 1 < len(idx) else len(body)
        n = sum(len(body[x]) for x in range(i, end))
        print(f"  {name or '(无标题)'}: {n} 字")
        if n < 500:
            warns.append(f"{name} 篇幅过短（{n} 字）")
    if len(idx) < 12:
        errors.append(f"一级标题只有 {len(idx)} 个，应为 12 个（含目录）")

    if warns:
        print("\n--- 提醒 ---")
        for w in warns:
            print("  ! " + w)
    if errors:
        print("\n--- 错误 ---")
        for e in errors:
            print("  x " + e)
        print("\n结论：FAIL")
        return 1
    print("\n结论：PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
