# -*- coding: utf-8 -*-
"""把 8 个功能的题目文件合并成 likert8/items.json（152 题）。

用法：python likert8/merge.py
缺文件会直接报错并列出缺哪个。
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from version import VERSION  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.join(BASE, "likert8")
ORDER = ["Se", "Si", "Ne", "Ni", "Te", "Ti", "Fe", "Fi"]


def main() -> int:
    items, missing = [], []
    for fn in ORDER:
        p = os.path.join(HERE, f"items_{fn}.json")
        if not os.path.exists(p):
            missing.append(f"items_{fn}.json")
            continue
        with io.open(p, encoding="utf-8") as f:
            d = json.load(f)
        for it in d["items"]:
            items.append({"id": it["id"], "fn": it["fn"], "reverse": bool(it["reverse"]),
                          "domain": it["domain"], "text": it["text"]})
    if missing:
        print("[缺文件] " + "、".join(missing))
        return 2

    if len(items) != 152:
        print(f"[题数异常] {len(items)}，应为 152")
        return 1

    out = {"meta": {"version": VERSION, "scale": 7, "items": len(items),
                    "plan": "8 个功能 × 19 题；每题 7 点同意度；每功能 6 题反向"},
           "items": items}
    with io.open(os.path.join(HERE, "items.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"合并完成：{len(items)} 题 -> likert8/items.json")
    for fn in ORDER:
        n = sum(1 for x in items if x["fn"] == fn)
        r = sum(1 for x in items if x["fn"] == fn and x["reverse"])
        print(f"  {fn}: {n} 题（反向 {r}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
