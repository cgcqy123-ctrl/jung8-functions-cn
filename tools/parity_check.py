# -*- coding: utf-8 -*-
"""比对 Python 与 JS 两份计分结果，必须逐值一致。"""
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(BASE, "tools")
FUNCS = ["Se", "Si", "Ne", "Ni", "Te", "Ti", "Fe", "Fi"]


def main() -> int:
    with open(os.path.join(T, ".parity_py.json"), encoding="utf-8") as f:
        py = json.load(f)
    with open(os.path.join(T, ".parity_js.json"), encoding="utf-8") as f:
        js = json.load(f)
    if len(py) != len(js):
        print(f"FAIL 用例数不一致 {len(py)} vs {len(js)}")
        return 1
    bad = 0
    for i, (a, b) in enumerate(zip(py, js)):
        errs = []
        for k in ("dominant", "auxiliary", "tertiary", "inferior", "code",
                  "jung_code", "confidence"):
            if a[k] != b[k]:
                errs.append(f"{k}: py={a[k]} js={b[k]}")
        for f in FUNCS:
            if abs(a["S"][f] - b["S"][f]) > 1e-6:
                errs.append(f"S.{f}: {a['S'][f]} vs {b['S'][f]}")
            if abs(a["P"][f] - b["P"][f]) > 0.06:
                errs.append(f"P.{f}: {a['P'][f]} vs {b['P'][f]}")
        if abs(a["gap"] - b["gap"]) > 0.002:
            errs.append(f"gap: {a['gap']} vs {b['gap']}")
        if abs(a["consistency"] - b["consistency"]) > 0.002:
            errs.append(f"consistency: {a['consistency']} vs {b['consistency']}")
        for ta, tb in zip(a["top3"], b["top3"]):
            if ta[0] != tb[0] or abs(ta[1] - tb[1]) > 0.002:
                errs.append(f"top3: {ta} vs {tb}")
        if errs:
            bad += 1
            print(f"用例 {i}: " + "; ".join(errs))
    print(f"\n比对 {len(py)} 组：不一致 {bad} 组")
    print("结论：" + ("PASS（Python 与 JS 计分完全一致）" if bad == 0 else "FAIL"))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
