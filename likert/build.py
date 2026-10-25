# -*- coding: utf-8 -*-
"""把 likert/items.json 注入模板，生成仓库根目录的 index.html（7 点量表版）。

用法：python likert/build.py
"""
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.join(BASE, "likert")
OUT = os.path.join(BASE, "index.html")
VERSION = "v0.2"


def main() -> int:
    with io.open(os.path.join(HERE, "items.json"), encoding="utf-8") as f:
        data = json.load(f)
    items = data["items"]
    if len(items) != 50:
        raise SystemExit(f"题数 {len(items)}，应为 50")

    payload = json.loads(json.dumps(data))  # 只带需要的字段
    slim = {"meta": data.get("meta", {}), "items": [
        {k: it[k] for k in ("id", "dim", "facet", "key", "reverse", "text")} for it in items
    ]}
    body = json.dumps(slim, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    with io.open(os.path.join(HERE, "template.html"), encoding="utf-8") as f:
        tpl = f.read()
    if "/*__DATA__*/" not in tpl or "/*__VERSION__*/" not in tpl:
        raise SystemExit("模板缺少占位符")
    html = tpl.replace("/*__DATA__*/", body).replace("/*__VERSION__*/", json.dumps(VERSION))
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print(f"saved: {OUT} ({os.path.getsize(OUT)/1024:.1f} KB, {len(items)} 题)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
