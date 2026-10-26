# -*- coding: utf-8 -*-
"""校验单个功能的 19 题文件（likert8/items_<fn>.json）。

用法：python likert8/check_items.py likert8/items_Te.json
"""
import json
import os
import sys
import unicodedata
from collections import Counter

FNS = ["Se", "Si", "Ne", "Ni", "Te", "Ti", "Fe", "Fi"]
DOMAINS = {"家庭亲戚": 3, "职场办公": 3, "学习考试": 2, "社交人情": 2, "消费生活": 2,
           "冲突矛盾": 2, "兴趣娱乐": 2, "信息媒体": 1, "亲密关系": 1, "身体健康": 1}
BANNED = ["总是", "从不", "经常", "通常", "一般", "正确", "成熟", "高效", "优秀", "靠谱",
          "幼稚", "情商", "派对", "教会", "公路旅行", "女生", "男生", "文科", "理科",
          "研究表明", "据统计", "名人"]


def nchars(s: str) -> int:
    t = unicodedata.normalize("NFKC", s or "")
    return sum(1 for ch in t if not (ch.isspace() or unicodedata.category(ch)[0] in ("P", "S")))


def main() -> int:
    if len(sys.argv) < 2:
        print("用法：python likert8/check_items.py likert8/items_Te.json")
        return 2
    path = sys.argv[1]
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    fn = d.get("fn")
    items = d.get("items") or []
    errors = []

    if fn not in FNS:
        errors.append(f"fn 非法：{fn}")
    if len(items) != 19:
        errors.append(f"题数 {len(items)}，应为 19")

    dom, rev, seen = Counter(), 0, {}
    for it in items:
        iid = it.get("id", "?")
        if it.get("fn") != fn:
            errors.append(f"{iid}: fn 与文件不一致")
        if it.get("domain") not in DOMAINS:
            errors.append(f"{iid}: domain 非法 {it.get('domain')}")
        else:
            dom[it["domain"]] += 1
        if not isinstance(it.get("reverse"), bool):
            errors.append(f"{iid}: reverse 必须是 true/false")
        elif it["reverse"]:
            rev += 1
        text = it.get("text", "")
        n = nchars(text)
        if not (10 <= n <= 34):
            errors.append(f"{iid}: 文本 {n} 字，超出 10–34")
        if text in seen:
            errors.append(f"{iid}: 与 {seen[text]} 文本重复")
        seen[text] = iid
        for b in BANNED:
            if b in text:
                errors.append(f"{iid}: 含禁用词「{b}」")

    if not (5 <= rev <= 7):
        errors.append(f"反向题 {rev} 道，应为 6 道（允许 5–7）")
    for dname, need in DOMAINS.items():
        got = dom[dname]
        if got != need:
            errors.append(f"域「{dname}」有 {got} 题，应为 {need}")

    print(f"=== {os.path.basename(path)} ===")
    print(f"题数 {len(items)}；反向 {rev} 道")
    print("域分布：" + "  ".join(f"{k}={dom[k]}" for k in DOMAINS if dom[k]))
    if errors:
        print("--- 错误 ---")
        for e in errors:
            print("  x " + e)
        print("结论：FAIL")
        return 1
    print("结论：PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
