# -*- coding: utf-8 -*-
"""校验题目 JSON 是否符合 SPEC（配对/方向/字数/重复/配平）。

用法：
    python tools/check_items.py data/items_a.json
    python tools/check_items.py data/items_a.json data/items_b.json --merged
"""
import json
import re
import sys
import unicodedata
from collections import Counter

PAIRS = {
    "P01": ("Se", "Si"), "P02": ("Se", "Ne"), "P03": ("Se", "Ni"),
    "P04": ("Si", "Ne"), "P05": ("Si", "Ni"), "P06": ("Ne", "Ni"),
    "P07": ("Te", "Ti"), "P08": ("Te", "Fe"), "P09": ("Te", "Fi"),
    "P10": ("Ti", "Fe"), "P11": ("Ti", "Fi"), "P12": ("Fe", "Fi"),
    "P13": ("Se", "Te"), "P14": ("Se", "Ti"), "P15": ("Se", "Fe"),
    "P16": ("Se", "Fi"), "P17": ("Si", "Te"), "P18": ("Si", "Ti"),
    "P19": ("Si", "Fe"), "P20": ("Si", "Fi"), "P21": ("Ne", "Te"),
    "P22": ("Ne", "Ti"), "P23": ("Ne", "Fe"), "P24": ("Ne", "Fi"),
    "P25": ("Ni", "Te"), "P26": ("Ni", "Ti"), "P27": ("Ni", "Fe"),
    "P28": ("Ni", "Fi"),
    # v1.4 扩展组：八个功能各多出现一次，配平不受影响
    "P29": ("Fe", "Ti"), "P30": ("Fi", "Te"),
    "P31": ("Ni", "Se"), "P32": ("Ne", "Si"),
}
FUNCS = ["Se", "Si", "Ne", "Ni", "Te", "Ti", "Fe", "Fi"]
DOMAINS = ["家庭亲戚", "职场办公", "学习考试", "社交人情", "消费生活", "冲突矛盾", "兴趣娱乐", "信息媒体"]


def expected_counts(pair_ids) -> dict:
    """每个功能应有的出现次数 = 2 × 含该功能的配对数（a/b 双向各一次）。"""
    exp = {f: 0 for f in FUNCS}
    for pid in pair_ids:
        for f in PAIRS[pid]:
            exp[f] += 2
    return exp


def nchars(s: str) -> int:
    """统计有效字数（不计标点、符号与空白）。"""
    t = unicodedata.normalize("NFKC", s)
    return sum(1 for ch in t
               if not (ch.isspace() or unicodedata.category(ch)[0] in ("P", "S")))


def check_file(path: str, errors: list, warns: list) -> list:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    items = raw.get("items")
    if not isinstance(items, list):
        errors.append(f"{path}: 缺少 items 列表")
        return []
    seen_ids, seen_scen = set(), {}
    fcount = Counter()
    apos = Counter()
    domains = Counter()
    ids_expected = []
    for item in items:
        iid = item.get("id", "?")
        pid = item.get("pair_id", "?")
        if pid not in PAIRS:
            errors.append(f"{iid}: pair_id 非法 {pid}")
            continue
        first, second = PAIRS[pid]
        if tuple(item.get("pair", [])) != (first, second):
            errors.append(f"{iid}: pair 应为 {first}-{second}，实际 {item.get('pair')}")
        # 方向规则
        suffix = str(iid)[-1]
        want_A = first if suffix == "a" else second
        want_B = second if suffix == "a" else first
        if str(iid)[:3] != "Q" + pid[1:]:
            errors.append(f"{iid}: 题号与 pair_id {pid} 不匹配")
        opts = item.get("options", {})
        A, B = opts.get("A", {}), opts.get("B", {})
        if A.get("fn") != want_A:
            errors.append(f"{iid}: A 应为 {want_A}，实际 {A.get('fn')}")
        if B.get("fn") != want_B:
            errors.append(f"{iid}: B 应为 {want_B}，实际 {B.get('fn')}")
        for k, side in (("A", A), ("B", B)):
            if side.get("fn") not in FUNCS:
                errors.append(f"{iid}: {k} 功能非法 {side.get('fn')}")
                continue
            fcount[side["fn"]] += 1
            if k == "A":
                apos[side["fn"]] += 1
        if not item.get("scenario"):
            errors.append(f"{iid}: 缺 scenario")
            continue
        sl = nchars(item["scenario"])
        if sl > 70:
            errors.append(f"{iid}: 场景 {sl} 字 > 70")
        elif sl < 12:
            warns.append(f"{iid}: 场景只有 {sl} 字，信息量可能不够")
        if item.get("domain") not in DOMAINS:
            errors.append(f"{iid}: domain 非法 {item.get('domain')}")
        else:
            domains[item["domain"]] += 1
        la, lb = nchars(A.get("text", "")), nchars(B.get("text", ""))
        for k, ln in (("A", la), ("B", lb)):
            if ln > 34:
                errors.append(f"{iid}: 选项 {k} {ln} 字 > 34")
            elif ln < 8:
                warns.append(f"{iid}: 选项 {k} 只有 {ln} 字，太单薄")
        if abs(la - lb) > 4:
            errors.append(f"{iid}: 两选项字数差 {abs(la-lb)} > 4（A {la} / B {lb}）")
        rat = item.get("rationale", {})
        for k in ("A", "B"):
            if not rat.get(k):
                errors.append(f"{iid}: 缺 rationale.{k}")
            elif nchars(rat[k]) > 30:
                errors.append(f"{iid}: rationale.{k} 超 30 字")
        if iid in seen_ids:
            errors.append(f"{iid}: 题号重复")
        seen_ids.add(iid)
        if item["scenario"] in seen_scen:
            errors.append(f"{iid}: 场景与 {seen_scen[item['scenario']]} 重复")
        seen_scen[item["scenario"]] = iid
        ids_expected.append(iid)
    # 允许清单：是否为连续的一段
    if ids_expected:
        nums = sorted({int(i[1:3]) for i in ids_expected})
        if nums != list(range(nums[0], nums[-1] + 1)):
            errors.append(f"{path}: 题号不连续 {nums}")
        if len(ids_expected) != 2 * len(nums):
            errors.append(f"{path}: 每个 pair 应有 a/b 两题，实际 {len(ids_expected)} 题 / {len(nums)} 对")
    # 配平
    pids = sorted({it["pair_id"] for it in items if it.get("pair_id") in PAIRS})
    exp = expected_counts(pids)
    for fn in FUNCS:
        if fcount[fn] != exp[fn]:
            errors.append(f"配平错误：{fn} 出现 {fcount[fn]} 次，应为 {exp[fn]}")
        if apos[fn] * 2 not in (fcount[fn], fcount[fn] + 1):
            warns.append(f"位置偏差：{fn} 作 A 位 {apos[fn]} 次 / 共 {fcount[fn]} 次")
    print(f"\n=== {path} ===")
    print(f"题数: {len(ids_expected)}（{len(nums) if ids_expected else 0} 对）")
    print("功能出现次数: " + "  ".join(f"{f}={fcount[f]}" for f in FUNCS))
    print("领域分布: " + "  ".join(f"{d}={domains[d]}" for d in DOMAINS if domains[d]))
    empty = [d for d in DOMAINS if not domains[d]]
    if empty:
        warns.append("领域未覆盖: " + "、".join(empty))
    return items


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    merged = "--merged" in sys.argv
    errors, warns = [], []
    allitems = []
    for path in args:
        allitems += check_file(path, errors, warns)
    if merged:
        fcount = Counter()
        for it in allitems:
            fcount[it["options"]["A"]["fn"]] += 1
            fcount[it["options"]["B"]["fn"]] += 1
        print("\n=== 合并校验 ===")
        print(f"总题数: {len(allitems)}")
        print("功能出现次数: " + "  ".join(f"{f}={fcount[f]}" for f in FUNCS))
        for fn in FUNCS:
            need = expected_counts(list(PAIRS))[fn]
            if fcount[fn] != need:
                errors.append(f"合并配平错误：{fn} 出现 {fcount[fn]} 次，应为 {need}")
        ids = {it["id"] for it in allitems}
        if len(ids) != len(allitems):
            errors.append("合并后题号有重复")
        for pid in PAIRS:
            for suf in ("a", "b"):
                if f"Q{pid[1:]}{suf}" not in ids:
                    errors.append(f"缺题：Q{pid[1:]}{suf}")
    if warns:
        print("\n--- 提醒（不阻断）---")
        for w in warns:
            print("  ! " + w)
    if errors:
        print("\n--- 错误（必须修）---")
        for e in errors:
            print("  x " + e)
        print(f"\n结论：FAIL（{len(errors)} 个错误）")
        return 1
    print("\n结论：PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
