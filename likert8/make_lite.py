# -*- coding: utf-8 -*-
"""从 152 题里抽出精简版 80 题：每个功能 10 题，十域各 1 题，3 题反向。

用法：python likert8/make_lite.py  ->  生成 likert8/items_lite.json
规则是确定性的（同样输入永远得到同样输出），方便核对与回溯。
"""
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.join(BASE, "likert8")
FUNCS = ["Se", "Si", "Ne", "Ni", "Te", "Ti", "Fe", "Fi"]
DOMAINS = ["家庭亲戚", "职场办公", "学习考试", "社交人情", "消费生活",
           "冲突矛盾", "兴趣娱乐", "信息媒体", "亲密关系", "身体健康"]
REV_TARGET = 3          # 每功能保留 3 题反向（10 题里 30%）
REV_ORDER = ["冲突矛盾", "兴趣娱乐", "信息媒体", "身体健康", "亲密关系", 
             "消费生活", "社交人情", "学习考试", "职场办公", "家庭亲戚"]
PREFER = "first"        # 同域多题时先取 id 靠前的，再按反向配额微调


def pick_for_function(items, fn):
    by_dom = {d: sorted([x for x in items if x["fn"] == fn and x["domain"] == d], key=lambda x: x["id"])
              for d in DOMAINS}
    missing = [d for d in DOMAINS if not by_dom[d]]
    if missing:
        raise SystemExit(f"{fn} 缺少生活域：{missing}")

    # 初始：每个域优先选正向题（读起来更自然），没有正向才退回第一题
    sel = {}
    for d in DOMAINS:
        pos = [x for x in by_dom[d] if not x["reverse"]]
        sel[d] = pos[0] if pos else by_dom[d][0]
    rev = sum(1 for x in sel.values() if x["reverse"])

    # 反向题太多：把某些域换成该域里的正向题
    if rev > REV_TARGET:
        for d in DOMAINS:
            if rev == REV_TARGET:
                break
            if sel[d]["reverse"]:
                alts = [x for x in by_dom[d] if not x["reverse"]]
                if alts:
                    sel[d] = alts[0]
                    rev -= 1
    # 反向题太少：把某些域换成该域里的反向题
    elif rev < REV_TARGET:
        for d in REV_ORDER:
            if rev == REV_TARGET:
                break
            if not sel[d]["reverse"]:
                alts = [x for x in by_dom[d] if x["reverse"]]
                if alts:
                    sel[d] = alts[0]
                    rev += 1

    if rev != REV_TARGET:
        raise SystemExit(f"{fn} 反向题调不到 {REV_TARGET} 题（现有 {rev}），需要人工挑")
    return [sel[d] for d in DOMAINS]


def main() -> int:
    with io.open(os.path.join(HERE, "items.json"), encoding="utf-8") as f:
        full = json.load(f)["items"]
    if len(full) != 152:
        raise SystemExit(f"完整版题数 {len(full)}，应为 152")

    lite = []
    for fn in FUNCS:
        lite.extend(pick_for_function(full, fn))
    if len(lite) != 80:
        raise SystemExit(f"精简版题数 {len(lite)}，应为 80")

    out = {"meta": {"version": "v3.3-lite", "scale": 7, "items": len(lite),
                    "source": "由 items.json 抽取：每功能 10 题、十域各 1 题、3 题反向",
                    "plan": "8 个功能 × 10 题（full 版的一半）"},
           "items": [{"id": x["id"], "fn": x["fn"], "reverse": x["reverse"],
                      "domain": x["domain"], "text": x["text"]} for x in lite]}
    with io.open(os.path.join(HERE, "items_lite.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"精简版 {len(lite)} 题 -> items_lite.json")
    for fn in FUNCS:
        g = [x for x in lite if x["fn"] == fn]
        print(f"  {fn}: {len(g)} 题（反向 {sum(1 for x in g if x['reverse'])}，域 {len(set(x['domain'] for x in g))} 个）")
    print("  题号：" + "、".join(x["id"] for x in lite))
    return 0


if __name__ == "__main__":
    sys.exit(main())
