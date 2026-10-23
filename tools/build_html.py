# -*- coding: utf-8 -*-
"""把题目与类型数据注入模板，生成单文件、可离线使用的 HTML 自测页。

用法：python tools/build_html.py
"""
from __future__ import annotations

import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "index.html")

TYPE_FIELDS = ["cn_name", "jung_type", "oneliner", "core", "work", "family", "love",
               "strength", "blindspot", "stress", "growth", "mistype"]
JUNG_FIELDS = ["name", "fn", "essence", "aux_a", "aux_b", "everyday", "blind", "mistype"]


def load_json(name):
    path = os.path.join(BASE, "data", name)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_data():
    items = (load_json("items_a.json")["items"] + load_json("items_b.json")["items"]
             + load_json("items_c.json")["items"])
    items.sort(key=lambda it: it["id"])
    ids = [it["id"] for it in items]
    expect = [f"Q{n:02d}{s}" for n in range(1, 33) for s in ("a", "b")]
    missing = [i for i in expect if i not in ids]
    if missing or len(items) != len(expect):
        raise SystemExit(f"题目不完整：{len(items)} 题，缺 {missing[:5]}")

    slim_items = []
    for it in items:
        slim_items.append({
            "id": it["id"],
            "scenario": it["scenario"],
            "options": {
                "A": {"fn": it["options"]["A"]["fn"], "text": it["options"]["A"]["text"]},
                "B": {"fn": it["options"]["B"]["fn"], "text": it["options"]["B"]["text"]},
            },
        })

    types, jung = {}, {}
    for name in ("types_a.json", "types_b.json"):
        d = load_json(name)
        for t in d.get("letter_types", []):
            rec = {"stack": t["stack"]}
            for f in TYPE_FIELDS:
                rec[f] = t.get(f, "")
            types[t["code"]] = rec
        for j in d.get("jung_types", []):
            rec = {}
            for f in JUNG_FIELDS:
                rec[f] = j.get(f, "")
            jung[j["code"]] = rec
    if len(types) != 16 or len(jung) != 8:
        raise SystemExit(f"类型数据不完整：letter={len(types)} jung={len(jung)}")
    return {"items": slim_items, "types": types, "jung": jung}


def main() -> int:
    data = build_data()
    with open(os.path.join(BASE, "tools", "template.html"), encoding="utf-8") as f:
        tpl = f.read()
    with open(os.path.join(BASE, "tools", "scoring.js"), encoding="utf-8") as f:
        scoring = f.read()

    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("</", "<\\/")
    if "/*__SCORING__*/" not in tpl or "/*__DATA__*/" not in tpl:
        raise SystemExit("模板缺少占位符")
    html = tpl.replace("/*__SCORING__*/", scoring).replace("/*__DATA__*/", payload)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    size = os.path.getsize(OUT)
    print(f"saved: {OUT} ({size/1024:.1f} KB, {len(data['items'])} 题, "
          f"{len(data['types'])} 型)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
