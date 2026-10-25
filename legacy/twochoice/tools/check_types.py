# -*- coding: utf-8 -*-
"""校验类型画像 JSON（字数、字段、功能栈、中文名）。"""
import json
import os
import sys
import unicodedata

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
from score import ATT, CN_NAME, FUNCS, JUNG_OF, OPP, STACKS  # noqa: E402

TYPE_RANGES = {  # 字段: (最小, 最大)
    "oneliner": (8, 40), "core": (180, 300), "work": (100, 190), "family": (100, 190),
    "love": (80, 160), "stress": (80, 150), "growth": (80, 150), "mistype": (60, 130),
}
JUNG_RANGES = {
    "essence": (100, 200), "aux_a": (60, 110), "aux_b": (60, 110),
    "everyday": (100, 180), "blind": (60, 130), "mistype": (50, 100),
}


def nchars(s: str) -> int:
    t = unicodedata.normalize("NFKC", s or "")
    return sum(1 for ch in t
               if not (ch.isspace() or unicodedata.category(ch)[0] in ("P", "S")))


def aux_cands(dom):
    other = [f for f in FUNCS if (f in ("Se", "Si", "Ne", "Ni")) != (dom in ("Se", "Si", "Ne", "Ni"))]
    return [f for f in other if ATT[f] != ATT[dom]]


def main() -> int:
    errors, warns = [], []
    letters, jung = {}, {}
    for name in ("types_a.json", "types_b.json"):
        path = os.path.join(BASE, "data", name)
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        for t in d.get("letter_types", []):
            if t["code"] in letters:
                errors.append(f"{name}: 重复类型 {t['code']}")
            letters[t["code"]] = t
        for j in d.get("jung_types", []):
            if j["code"] in jung:
                errors.append(f"{name}: 重复荣格类型 {j['code']}")
            jung[j["code"]] = j

    print(f"letter_types {len(letters)} 个，jung_types {len(jung)} 个")
    if set(letters) != set(STACKS):
        errors.append(f"letter_types 应恰为 16 型，缺 {set(STACKS)-set(letters)}，多 {set(letters)-set(STACKS)}")
    if set(jung) != {"ET", "IT", "EF", "IF", "ES", "IS", "EN", "IN"}:
        errors.append("jung_types 应恰为 ET/IT/EF/IF/ES/IS/EN/IN")

    print("\n--- 十六型 ---")
    for code in STACKS:
        t = letters.get(code)
        if not t:
            continue
        if t["stack"] != STACKS[code]:
            errors.append(f"{code}: 功能栈 {t['stack']} ≠ 基准 {STACKS[code]}")
        if CN_NAME.get(code) and t.get("cn_name") != CN_NAME[code]:
            errors.append(f"{code}: cn_name '{t.get('cn_name')}' ≠ '{CN_NAME[code]}'")
        if t.get("jung_type") != JUNG_OF[STACKS[code][0]][1]:
            errors.append(f"{code}: jung_type '{t.get('jung_type')}' ≠ '{JUNG_OF[STACKS[code][0]][1]}'")
        cells = []
        for field, (lo, hi) in TYPE_RANGES.items():
            n = nchars(t.get(field, ""))
            ok = lo <= n <= hi
            cells.append(f"{field}{n}{'' if ok else '!'}")
            if not ok:
                warns.append(f"{code}.{field} = {n} 字，期望 {lo}–{hi}")
        for field in ("strength", "blindspot"):
            v = t.get(field) or []
            if len(v) != 3:
                warns.append(f"{code}.{field} 有 {len(v)} 条，期望 3")
            for s in v:
                if nchars(s) > 22:
                    warns.append(f"{code}.{field} 单条过长：{s[:12]}…")
        print(f"  {code} " + " ".join(cells))

    print("\n--- 荣格八型 ---")
    for code in ("ET", "IT", "EF", "IF", "ES", "IS", "EN", "IN"):
        j = jung.get(code)
        if not j:
            continue
        dom = j.get("fn")
        if dom not in FUNCS:
            errors.append(f"{code}: fn 非法 {dom}")
            continue
        if JUNG_OF[dom][0] != code:
            errors.append(f"{code}: fn {dom} 与 code 不符")
        cells = []
        for field, (lo, hi) in JUNG_RANGES.items():
            n = nchars(j.get(field, ""))
            ok = lo <= n <= hi
            cells.append(f"{field}{n}{'' if ok else '!'}")
            if not ok:
                warns.append(f"{code}.{field} = {n} 字，期望 {lo}–{hi}")
        print(f"  {code}({dom}) " + " ".join(cells))

    if warns:
        print(f"\n--- 提醒 {len(warns)} 条 ---")
        for w in warns:
            print("  ! " + w)
    if errors:
        print(f"\n--- 错误 {len(errors)} 条 ---")
        for e in errors:
            print("  x " + e)
        print("\n结论：FAIL")
        return 1
    print("\n结论：PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
