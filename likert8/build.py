# -*- coding: utf-8 -*-
"""生成两个版本：index.html（完整 152 题）与 lite.html（精简 80 题）。

文案在构建期就写进静态 HTML（占位符替换），不依赖 JS；DATA.meta 只作兜底。
用法：python likert8/build.py
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from version import VERSION  # noqa: E402  唯一的版本号来源

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.join(BASE, "likert8")

PAGES = [
    {
        "file": "index.html",
        "items": "items.json",
        "expect": 152,
        "meta": {
            "mode": "full",
            "title": "荣格八维人格测验（完整版 · 152 题）",
            "eyebrow": "荣格八维 · 7 点同意度 · 152 句中国日常",
            "lede": "152 句话 · 每句选一个同意程度 · 约 25 分钟",
            "batches": "152 题，可以分三次做完，进度自动存在这台设备上。",
            "start": "152 题 · 约 25 分钟",
            "note": "八个维度每题数相同（各 19 题、其中 6 题反向），所以分数之间可以直接比。"
                    "这是自我认识工具，不是诊断。",
            "minutes": 25,
            "altNote": "时间紧？",
            "altLabel": "做精简版 80 题",
            "altUrl": "./lite.html",
            "altTime": "（约 13 分钟，精度略低）",
        },
    },
    {
        "file": "lite.html",
        "items": "items_lite.json",
        "expect": 80,
        "meta": {
            "mode": "lite",
            "title": "荣格八维人格测验（精简版 · 80 题）",
            "eyebrow": "荣格八维 · 7 点同意度 · 80 句中国日常",
            "lede": "80 句话 · 每句选一个同意程度 · 约 13 分钟",
            "batches": "80 题，一次做完即可；进度自动存在这台设备上。",
            "start": "80 题 · 约 13 分钟",
            "note": "精简版每个功能 10 题（十个生活域各 1 题、3 题反向），八个维度题数仍然相同，所以分数之间可以直接比。"
                    "题量只有完整版的一半，判定的稳定性会低一些——结果页的置信度会如实反映这一点。",
            "minutes": 13,
            "altNote": "想要更稳的结果？",
            "altLabel": "做完整版 152 题",
            "altUrl": "./index.html",
            "altTime": "（约 25 分钟）",
        },
    },
]

TOKENS = ["__TITLE__", "__EYEBROW__", "__LEDE__", "__BATCHES__", "__START__",
          "__ALT_URL__", "__ALT_LABEL__", "__ALT_NOTE__", "__ALT_TIME__", "__NOTE__"]


def load(name):
    with io.open(os.path.join(HERE, name), encoding="utf-8") as f:
        return f.read()


def load_types():
    types, jung = {}, {}
    for name in ("types_a.json", "types_b.json"):
        with io.open(os.path.join(BASE, "data", name), encoding="utf-8") as f:
            d = json.load(f)
        for t in d["letter_types"]:
            types[t["code"]] = t
        for j in d["jung_types"]:
            jung[j["code"]] = j
    if len(types) != 16 or len(jung) != 8:
        raise SystemExit(f"类型数据不完整：{len(types)} 型 / {len(jung)} 荣格类型")
    return types, jung


def main() -> int:
    types, jung = load_types()
    tpl = load("template.html")
    for token in ("/*__SCORING__*/", "/*__DATA__*/", "/*__VERSION__*/"):
        if token not in tpl:
            raise SystemExit(f"模板缺少占位符 {token}")
    missing = [t for t in TOKENS if t not in tpl]
    if missing:
        raise SystemExit(f"模板缺少文案占位符：{missing}")

    manual_name = "荣格八维测验-152题手册.docx"
    has_manual = os.path.exists(os.path.join(BASE, manual_name))

    for page in PAGES:
        m = page["meta"]
        doc = json.loads(load(page["items"]))
        items = doc["items"]
        if len(items) != page["expect"]:
            raise SystemExit(f"{page['file']}：题数 {len(items)}，应为 {page['expect']}")

        payload = {
            "meta": m,
            "items": [{"id": x["id"], "fn": x["fn"], "reverse": x["reverse"], "text": x["text"]}
                      for x in items],
            "types": types,
            "jung": jung,
        }
        if has_manual:
            payload["manual"] = {"name": manual_name}
        data_js = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

        html = (tpl.replace("/*__SCORING__*/", load("scoring.js"))
                   .replace("/*__DATA__*/", data_js)
                   .replace("/*__VERSION__*/", json.dumps(VERSION)))
        for tok, val in (("__TITLE__", m["title"]), ("__EYEBROW__", m["eyebrow"]), ("__LEDE__", m["lede"]),
                         ("__BATCHES__", m["batches"]), ("__START__", m["start"]),
                         ("__ALT_URL__", m["altUrl"]), ("__ALT_LABEL__", m["altLabel"]),
                         ("__ALT_NOTE__", m["altNote"]), ("__ALT_TIME__", m["altTime"]),
                         ("__NOTE__", m["note"])):
            html = html.replace(tok, val)

        left = [t for t in TOKENS if t in html]
        if left:
            raise SystemExit(f"{page['file']} 仍残留占位符：{left}")

        out = os.path.join(BASE, page["file"])
        with io.open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
        print(f"saved: {out} ({os.path.getsize(out)/1024:.1f} KB, {len(items)} 题, 模式 {m['mode']})")
    if not has_manual:
        print(f"[提醒] 未找到 {manual_name}，页面不会出现手册下载按钮")
    return 0


if __name__ == "__main__":
    sys.exit(main())
