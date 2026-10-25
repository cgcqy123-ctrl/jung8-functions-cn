# -*- coding: utf-8 -*-
"""生成八维量表版页面：likert8/{items.json,scoring.js,template.html} + data/types_*.json -> index.html

用法：python likert8/build.py
"""
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.join(BASE, "likert8")
OUT = os.path.join(BASE, "index.html")
VERSION = "v3.0"


def load(name):
    with io.open(os.path.join(HERE, name), encoding="utf-8") as f:
        return f.read()


def main() -> int:
    items_doc = json.loads(load("items.json"))
    items = items_doc["items"]
    if len(items) != 152:
        raise SystemExit(f"题数 {len(items)}，应为 152")

    types, jung = {}, {}
    for name in ("types_a.json", "types_b.json"):
        with io.open(os.path.join(BASE, "data", name), encoding="utf-8") as f:
            d = json.load(f)
        for t in d["letter_types"]:
            types[t["code"]] = t
        for j in d["jung_types"]:
            jung[j["code"]] = j
    if len(types) != 16:
        raise SystemExit(f"类型画像 {len(types)}，应为 16")
    if len(jung) != 8:
        raise SystemExit(f"荣格类型 {len(jung)}，应为 8")

    payload = {"items": [{"id": x["id"], "fn": x["fn"], "reverse": x["reverse"], "text": x["text"]}
                         for x in items],
               "types": types, "jung": jung}
    data_js = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    html = load("template.html")
    for token in ("/*__SCORING__*/", "/*__DATA__*/", "/*__VERSION__*/"):
        if token not in html:
            raise SystemExit(f"模板缺少占位符 {token}")
    html = (html.replace("/*__SCORING__*/", load("scoring.js"))
                .replace("/*__DATA__*/", data_js)
                .replace("/*__VERSION__*/", json.dumps(VERSION)))

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print(f"saved: {OUT} ({os.path.getsize(OUT)/1024:.1f} KB, {len(items)} 题, "
          f"{len(types)} 型, {len(jung)} 荣格类型)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
