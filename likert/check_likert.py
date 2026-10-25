# -*- coding: utf-8 -*-
"""校验 likert 题库：面向配对、正反各一、文本长度、重复、维度合法。

用法：python likert/check_likert.py
"""
import json
import os
import sys
import unicodedata
from collections import Counter, defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(BASE, "likert", "items.json")

DIMS = {"Mind": ("E", "I"), "Energy": ("N", "S"), "Nature": ("F", "T"),
        "Tactics": ("J", "P"), "Identity": ("A", "T")}
FACETS = {
    "Mind": ["社交启动", "主动表达", "独处恢复", "人群耐受", "陌生场合"],
    "Energy": ["细节留神", "想象投入", "抽象兴趣", "现实焦点", "模式与隐喻"],
    "Nature": ["逻辑优先", "情绪感知", "冲突直面", "取悦倾向", "人情与原则"],
    "Tactics": ["计划性", "收尾习惯", "临场应变", "秩序需求", "开放选项"],
    "Identity": ["自我肯定", "事后反刍", "压力反应", "完美主义", "情绪起伏"],
}


def nchars(s: str) -> int:
    t = unicodedata.normalize("NFKC", s or "")
    return sum(1 for ch in t if not (ch.isspace() or unicodedata.category(ch)[0] in ("P", "S")))


def main() -> int:
    with open(P, encoding="utf-8") as f:
        d = json.load(f)
    items = d["items"]
    errors, warns = [], []
    ids = [it["id"] for it in items]
    if len(set(ids)) != len(ids):
        errors.append("题号重复")
    if len(items) != 50:
        errors.append(f"题数 {len(items)}，应为 50")

    by_facet = defaultdict(list)
    seen = {}
    for it in items:
        if it["dim"] not in DIMS:
            errors.append(f"{it['id']}: 维度非法 {it['dim']}")
            continue
        if it["facet"] not in FACETS[it["dim"]]:
            errors.append(f"{it['id']}: 面向 {it['facet']} 不属于 {it['dim']}")
        if it["key"] not in DIMS[it["dim"]]:
            errors.append(f"{it['id']}: key {it['key']} 不在 {DIMS[it['dim']]}")
        n = nchars(it["text"])
        if not (10 <= n <= 34):
            errors.append(f"{it['id']}: 文本 {n} 字，超出 10–34")
        if it["text"] in seen:
            errors.append(f"{it['id']}: 文本与 {seen[it['text']]} 重复")
        seen[it["text"]] = it["id"]
        by_facet[(it["dim"], it["facet"])].append(it)

    # 每个面向两题，一正一反
    for dim, facets in FACETS.items():
        for fc in facets:
            group = by_facet.get((dim, fc), [])
            if len(group) != 2:
                errors.append(f"{dim}/{fc}: 有 {len(group)} 题，应为 2")
                continue
            revs = sum(1 for x in group if x["reverse"])
            if revs != 1:
                errors.append(f"{dim}/{fc}: 反向题 {revs} 道，应恰好 1 道")
            if group[0]["key"] != group[1]["key"]:
                errors.append(f"{dim}/{fc}: 两题 key 不一致")

    cnt = Counter((it["dim"]) for it in items)
    print(f"题数 {len(items)}；各维题数 " + "  ".join(f"{k}={v}" for k, v in cnt.items()))
    print(f"面向数 {len(by_facet)}（应 25）；每面题数 " +
          ("全部为 2" if all(len(v) == 2 for v in by_facet.values()) else "有不均"))
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
