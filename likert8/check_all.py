# -*- coding: utf-8 -*-
"""全量校验合并后的题库：题数、等权、反向、域配额、全局去重、正文长度。

用法：python likert8/check_all.py
"""
import io
import json
import os
import sys
import unicodedata
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(BASE, "likert8", "items.json")
ORDER = ["Se", "Si", "Ne", "Ni", "Te", "Ti", "Fe", "Fi"]
DOMAINS = {"家庭亲戚": 24, "职场办公": 24, "学习考试": 16, "社交人情": 16, "消费生活": 16,
           "冲突矛盾": 16, "兴趣娱乐": 16, "信息媒体": 8, "亲密关系": 8, "身体健康": 8}


def nchars(s: str) -> int:
    t = unicodedata.normalize("NFKC", s or "")
    return sum(1 for ch in t if not (ch.isspace() or unicodedata.category(ch)[0] in ("P", "S")))


def main() -> int:
    if not os.path.exists(P):
        print("缺 likert8/items.json，先跑 merge.py")
        return 2
    with io.open(P, encoding="utf-8") as f:
        d = json.load(f)
    items = d["items"]
    errors = []

    if len(items) != 152:
        errors.append(f"总题数 {len(items)}，应为 152")

    per_fn = Counter(x["fn"] for x in items)
    for fn in ORDER:
        if per_fn[fn] != 19:
            errors.append(f"{fn} 有 {per_fn[fn]} 题，应为 19")
        rev = sum(1 for x in items if x["fn"] == fn and x["reverse"])
        if rev != 6:
            errors.append(f"{fn} 反向 {rev} 道，应为 6")

    dom = Counter(x["domain"] for x in items)
    for k, need in DOMAINS.items():
        if dom[k] != need:
            errors.append(f"域「{k}」共 {dom[k]} 题，应为 {need}")

    seen = {}
    for x in items:
        t = x["text"]
        if t in seen:
            errors.append(f"文本重复：{x['id']} 与 {seen[t]}")
        seen[t] = x["id"]
        n = nchars(t)
        if not (10 <= n <= 34):
            errors.append(f"{x['id']} 长度 {n}（10–34）")

    ids = [x["id"] for x in items]
    if len(set(ids)) != len(ids):
        errors.append("题号重复")

    print(f"总题数 {len(items)}；反向 {sum(1 for x in items if x['reverse'])}")
    print("各功能：" + "  ".join(f"{fn}={per_fn[fn]}" for fn in ORDER))
    print("各域：" + "  ".join(f"{k}={dom[k]}" for k in DOMAINS))
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
