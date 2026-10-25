# -*- coding: utf-8 -*-
"""单点修订：把 Q16b 的 Se 选项压到与 Fi 选项等长（审校后字数配平）。"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(BASE, "data", "items_b.json")
d = json.load(open(p, encoding="utf-8"))
n = 0
for it in d["items"]:
    if it["id"] == "Q16b":
        it["options"]["B"]["text"] = "你先看今天有什么新鲜的，问服务员哪样卖得好。"
        n += 1
with open(p, "w", encoding="utf-8", newline="\n") as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
    f.write("\n")
print(f"patched {n} item")
