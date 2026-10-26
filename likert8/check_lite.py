# -*- coding: utf-8 -*-
"""校验精简版题库：80 题、每功能 10 题、十域各 1、3 题反向、无重复、长度合规。

用法：python likert8/check_lite.py [likert8/items_lite.json]
"""
import io
import json
import os
import sys
import unicodedata
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUNCS = ["Se", "Si", "Ne", "Ni", "Te", "Ti", "Fe", "Fi"]
DOMAINS = {"家庭亲戚", "职场办公", "学习考试", "社交人情", "消费生活",
           "冲突矛盾", "兴趣娱乐", "信息媒体", "亲密关系", "身体健康"}


def nchars(s: str) -> int:
    t = unicodedata.normalize("NFKC", s or "")
    return sum(1 for ch in t if not (ch.isspace() or unicodedata.category(ch)[0] in ("P", "S")))


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "likert8", "items_lite.json")
    with io.open(path, encoding="utf-8") as f:
        items = json.load(f)["items"]
    errors = []

    if len(items) != 80:
        errors.append(f"总题数 {len(items)}，应为 80")

    per = Counter(x["fn"] for x in items)
    for fn in FUNCS:
        g = [x for x in items if x["fn"] == fn]
        if len(g) != 10:
            errors.append(f"{fn} 有 {len(g)} 题，应为 10")
        rev = sum(1 for x in g if x["reverse"])
        if rev != 3:
            errors.append(f"{fn} 反向 {rev} 道，应为 3")
        doms = Counter(x["domain"] for x in g)
        if len(doms) != 10:
            errors.append(f"{fn} 覆盖 {len(doms)} 个生活域，应为 10")
        for d, c in doms.items():
            if c != 1:
                errors.append(f"{fn}/{d} 有 {c} 题，应为 1")

    seen = {}
    for x in items:
        if x["domain"] not in DOMAINS:
            errors.append(f"{x['id']} 域非法：{x['domain']}")
        t = x["text"]
        if t in seen:
            errors.append(f"文本重复：{x['id']} 与 {seen[t]}")
        seen[t] = x["id"]
        n = nchars(t)
        if not (10 <= n <= 34):
            errors.append(f"{x['id']} 长度 {n}（10–34）")

    if len({x["id"] for x in items}) != len(items):
        errors.append("题号重复")

    print(f"题数 {len(items)}；反向 {sum(1 for x in items if x['reverse'])}")
    print("各功能：" + "  ".join(f"{fn}={per[fn]}" for fn in FUNCS))
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
