# -*- coding: utf-8 -*-
"""奇偶/随机作答比对：生成测试用例与 Python 端结果（供 JS 端对齐）。"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score import FUNCS, load_items, score  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(BASE, "tools")


def main() -> int:
    items = load_items([os.path.join(BASE, "data", "items_a.json"),
                        os.path.join(BASE, "data", "items_b.json")])
    if len(items) != 56:
        print("题目不全，跳过")
        return 2
    rnd = random.Random(20261022)
    cases = []
    # 40 组随机作答 + 16 组「按功能栈权重作答」+ 2 组极端作答
    for _ in range(40):
        cases.append({it["id"]: rnd.choice([2, 1, -1, -2]) for it in items})
    from score import STACKS
    for code, st in STACKS.items():
        w = {f: 0.0 for f in FUNCS}
        for wt, f in zip((4.0, 3.0, 2.0, 1.0), st):
            w[f] = wt
        cases.append({it["id"]: (2 if w[it["options"]["A"]["fn"]] > w[it["options"]["B"]["fn"]]
                                 else (-2 if w[it["options"]["A"]["fn"]] < w[it["options"]["B"]["fn"]] else 1))
                      for it in items})
    cases.append({it["id"]: 2 for it in items})
    cases.append({it["id"]: -2 for it in items})

    with open(os.path.join(T, ".parity_in.json"), "w", encoding="utf-8") as f:
        json.dump({"items": [{"id": it["id"],
                              "options": {"A": {"fn": it["options"]["A"]["fn"]},
                                          "B": {"fn": it["options"]["B"]["fn"]}}}
                             for it in items],
                   "cases": cases}, f, ensure_ascii=False)
    py = []
    for ans in cases:
        r = score(ans, items)
        py.append({
            "S": r["S"], "P": r["P"], "dominant": r["dominant"], "auxiliary": r["auxiliary"],
            "tertiary": r["tertiary"], "inferior": r["inferior"], "code": r["code"],
            "jung_code": r["jung_code"], "top3": r["top3"], "gap": r["gap"],
            "consistency": r["consistency"], "confidence": r["confidence"],
        })
    with open(os.path.join(T, ".parity_py.json"), "w", encoding="utf-8") as f:
        json.dump(py, f, ensure_ascii=False)
    print(f"生成 {len(cases)} 组用例，Python 结果已写入 tools/.parity_py.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
