# -*- coding: utf-8 -*-
"""《荣格八维人格测验·中国情境版》计分引擎（唯一权威实现）。

用法：
    python tools/score.py --selftest                 # 16 型往返自测 + 恒等式检查
    python tools/score.py answers.json               # 给一份作答打分
    python tools/score.py answers.json --json        # 机器可读输出
answers.json 形如 {"Q01a": 2, "Q01b": -1, ...}，取值 +2/+1/-1/-2（+ 偏 A，- 偏 B）。
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter

FUNCS = ["Se", "Si", "Ne", "Ni", "Te", "Ti", "Fe", "Fi"]
PERCEIVING = {"Se", "Si", "Ne", "Ni"}
JUDGING = {"Te", "Ti", "Fe", "Fi"}
ATT = {"Se": "E", "Si": "I", "Ne": "E", "Ni": "I",
       "Te": "E", "Ti": "I", "Fe": "E", "Fi": "I"}
OPP = {"Se": "Si", "Si": "Se", "Ne": "Ni", "Ni": "Ne",
       "Te": "Ti", "Ti": "Te", "Fe": "Fi", "Fi": "Fe"}
FN_CN = {"Se": "外倾感觉", "Si": "内倾感觉", "Ne": "外倾直觉", "Ni": "内倾直觉",
         "Te": "外倾思维", "Ti": "内倾思维", "Fe": "外倾情感", "Fi": "内倾情感"}
JUNG_OF = {"Te": ("ET", "外倾思维型"), "Ti": ("IT", "内倾思维型"),
           "Fe": ("EF", "外倾情感型"), "Fi": ("IF", "内倾情感型"),
           "Se": ("ES", "外倾感觉型"), "Si": ("IS", "内倾感觉型"),
           "Ne": ("EN", "外倾直觉型"), "Ni": ("IN", "内倾直觉型")}
# 第三/劣势功能：与给定功能**同类**（判断对判断、知觉对知觉）、**功能对立**
# （思维↔情感、感觉↔直觉）、**态度相反**的那一个。注意这不是"同功能换态度"。
MAP = {"Te": "Fi", "Ti": "Fe", "Fe": "Ti", "Fi": "Te",
       "Se": "Ni", "Si": "Ne", "Ne": "Si", "Ni": "Se"}

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
}

STACKS = {
    "INTJ": ["Ni", "Te", "Fi", "Se"], "INTP": ["Ti", "Ne", "Si", "Fe"],
    "ENTJ": ["Te", "Ni", "Se", "Fi"], "ENTP": ["Ne", "Ti", "Fe", "Si"],
    "INFJ": ["Ni", "Fe", "Ti", "Se"], "INFP": ["Fi", "Ne", "Si", "Te"],
    "ENFJ": ["Fe", "Ni", "Se", "Ti"], "ENFP": ["Ne", "Fi", "Te", "Si"],
    "ISTJ": ["Si", "Te", "Fi", "Ne"], "ISFJ": ["Si", "Fe", "Ti", "Ne"],
    "ESTJ": ["Te", "Si", "Ne", "Fi"], "ESFJ": ["Fe", "Si", "Ne", "Ti"],
    "ISTP": ["Ti", "Se", "Ni", "Fe"], "ISFP": ["Fi", "Se", "Ni", "Te"],
    "ESTP": ["Se", "Ti", "Fe", "Ni"], "ESFP": ["Se", "Fi", "Te", "Ni"],
}
CN_NAME = {
    "INTJ": "远景架构者", "INTP": "原理拆解者", "ENTJ": "目标统帅者", "ENTP": "可能性发动机",
    "INFJ": "深察引路者", "INFP": "价值守火者", "ENFJ": "人心凝聚者", "ENFP": "火花点燃者",
    "ISTJ": "秩序守护者", "ISFJ": "细致托底者", "ESTJ": "事务操盘者", "ESFJ": "场面照拂者",
    "ISTP": "现场解题者", "ISFP": "感受力行家", "ESTP": "临场破局者", "ESFP": "即兴享乐者",
}
W = (1.0, 0.6, 0.3, 0.1)  # 主导/辅助/第三/劣势 的匹配权重


# ---------------------------------------------------------------- 基础设施
def synthetic_items() -> list[dict]:
    """不依赖题目的合成题集：28 对 × 2 方向，用于算法自测。"""
    items = []
    for pid, (f1, f2) in PAIRS.items():
        n = pid[1:]
        for suf, a, b in (("a", f1, f2), ("b", f2, f1)):
            items.append({"id": f"Q{n}{suf}", "pair_id": pid, "pair": [f1, f2],
                          "options": {"A": {"fn": a}, "B": {"fn": b}}})
    return items


def load_items(paths: list[str]) -> list[dict]:
    items: list[dict] = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            items += json.load(f)["items"]
    items.sort(key=lambda it: it["id"])
    return items


def appearances(items: list[dict]) -> Counter:
    c: Counter = Counter()
    for it in items:
        c[it["options"]["A"]["fn"]] += 1
        c[it["options"]["B"]["fn"]] += 1
    return c


def _z(s: dict[str, float]) -> dict[str, float]:
    m = sum(s.values()) / len(s)
    var = sum((v - m) ** 2 for v in s.values()) / len(s)
    sd = var ** 0.5 or 1.0
    return {k: (v - m) / sd for k, v in s.items()}


def _rank(xs: list[float]) -> list[float]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(a: list[float], b: list[float]) -> float:
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    va = sum((x - ma) ** 2 for x in a) ** 0.5
    vb = sum((y - mb) ** 2 for y in b) ** 0.5
    if va == 0 or vb == 0:
        return 0.0
    return cov / (va * vb)


def spearman(a: list[float], b: list[float]) -> float:
    return _pearson(_rank(a), _rank(b))


# ---------------------------------------------------------------- 核心计分
def _sums(answers: dict, items: list[dict]) -> dict[str, float]:
    s = {f: 0.0 for f in FUNCS}
    for it in items:
        r = answers.get(it["id"])
        if r is None:
            continue
        fa = it["options"]["A"]["fn"]
        fb = it["options"]["B"]["fn"]
        s[fa] += float(r)
        s[fb] -= float(r)
    return s


def score(answers: dict, items: list[dict]) -> dict:
    cnt = appearances(items)
    M = max(cnt.values()) if cnt else 14
    answered = [it for it in items if it["id"] in answers]
    S = _sums(answers, items)
    P = {f: 50 + 25 * S[f] / M for f in FUNCS}  # |S| <= 2M，故 25*S/M 落在 ±50
    Z = _z(S)

    dom = sorted(FUNCS, key=lambda f: (-S[f], FUNCS.index(f)))[0]
    other_cat = list(JUDGING) if dom in PERCEIVING else list(PERCEIVING)
    cand = [f for f in other_cat if ATT[f] != ATT[dom]]
    aux = sorted(cand, key=lambda f: (-S[f], FUNCS.index(f)))[0]
    tert = MAP[aux]
    inf = MAP[dom]

    ei = ATT[dom]
    if dom in PERCEIVING:
        sn = "N" if dom in ("Ne", "Ni") else "S"
        tf = "T" if aux in ("Te", "Ti") else "F"
    else:
        tf = "T" if dom in ("Te", "Ti") else "F"
        sn = "N" if aux in ("Ne", "Ni") else "S"
    ext_fn = dom if ATT[dom] == "E" else aux
    jp = "J" if ext_fn in JUDGING else "P"
    code = f"{ei}{sn}{tf}{jp}"

    fits = {}
    for t, st in STACKS.items():
        fits[t] = round(sum(w * Z[f] for w, f in zip(W, st)), 3)
    ranked = sorted(fits.items(), key=lambda kv: -kv[1])

    # 奇偶分半一致性（按题面固定顺序的 seq 奇偶，与作答顺序无关）
    odd = {it["id"]: answers[it["id"]] for i, it in enumerate(items)
           if i % 2 == 0 and it["id"] in answers}
    even = {it["id"]: answers[it["id"]] for i, it in enumerate(items)
            if i % 2 == 1 and it["id"] in answers}
    Zo = _z(_sums(odd, items))
    Ze = _z(_sums(even, items))
    r_half = round(spearman([Zo[f] for f in FUNCS], [Ze[f] for f in FUNCS]), 3)

    gap = round(ranked[0][1] - ranked[1][1], 3)
    if gap >= 0.6 and r_half >= 0.5:
        conf = "高"
    elif gap >= 0.3 and r_half >= 0.25:
        conf = "中"
    else:
        conf = "低"

    jcode, jname = JUNG_OF[dom]
    return {
        "n_answered": len(answered), "n_items": len(items), "complete": len(answered) == len(items),
        "S": {f: round(S[f], 2) for f in FUNCS},
        "P": {f: math.floor(P[f] * 10 + 0.5) / 10 for f in FUNCS},
        "Z": {f: round(Z[f], 3) for f in FUNCS},
        "dominant": dom, "dominant_cn": FN_CN[dom],
        "auxiliary": aux, "auxiliary_cn": FN_CN[aux],
        "tertiary": tert, "inferior": inf,
        "jung_code": jcode, "jung_name": jname,
        "code": code, "cn_name": CN_NAME[code], "stack": [dom, aux, tert, inf],
        "fits": fits, "top3": ranked[:3], "gap": gap,
        "consistency": r_half, "confidence": conf,
        "mismatch": ranked[0][0] != code,
        "sum_check": round(sum(S.values()), 6),
    }


def report(res: dict) -> str:
    L = []
    L.append(f"作答 {res['n_answered']}/{res['n_items']} 题")
    L.append("八维相对强度（0–100，相对排名，非能力分）：")
    for f in sorted(FUNCS, key=lambda x: -res["P"][x]):
        bar = "█" * int(round(res["P"][f] / 5))
        L.append(f"  {f} {FN_CN[f]:<5} {res['P'][f]:5.1f} {bar}")
    L.append(f"主导：{res['dominant']}（{res['dominant_cn']}）")
    L.append(f"辅助：{res['auxiliary']}（{res['auxiliary_cn']}）  第三：{res['tertiary']}  劣势：{res['inferior']}")
    L.append(f"荣格类型：{res['jung_name']}（{res['jung_code']}）")
    L.append(f"四字母：{res['code']}｜{res['cn_name']}｜功能栈 {'-'.join(res['stack'])}")
    L.append("吻合度前三：" + "，".join(f"{t} {v:+.2f}" for t, v in res["top3"]))
    L.append(f"置信度：{res['confidence']}（gap={res['gap']}，奇偶一致性 r={res['consistency']}）")
    if res["mismatch"]:
        L.append("⚠ 主判与吻合度排序不一致：答案内部存在张力，建议复测或做快速版对照。")
    return "\n".join(L)


# ---------------------------------------------------------------- 自测
def selftest() -> int:
    items = synthetic_items()
    fail = 0
    print(f"合成题集：{len(items)} 题；每功能出现 {dict(appearances(items))}")
    print(f"\n{'目标型':<6}{'推导型':<8}{'主导':<4}{'辅助':<4}{'sum(S)':<8}{'结果'}")
    for target, st in STACKS.items():
        weights = {f: 0.0 for f in FUNCS}
        for w, f in zip((4.0, 3.0, 2.0, 1.0), st):
            weights[f] = w
        answers = {}
        for it in items:
            a, b = it["options"]["A"]["fn"], it["options"]["B"]["fn"]
            d = weights[a] - weights[b]
            answers[it["id"]] = 2 if d > 0 else (-2 if d < 0 else 1)
        r = score(answers, items)
        ok = (r["code"] == target and r["jung_code"] == JUNG_OF[st[0]][0]
              and r["stack"] == st  # 第三/劣势必须与标准功能栈一致
              and abs(r["sum_check"]) < 1e-9)
        fail += 0 if ok else 1
        print(f"{target:<6}{r['code']:<8}{r['dominant']:<4}{r['auxiliary']:<4}"
              f"{r['sum_check']:<8}{'PASS' if ok else 'FAIL'}")
    print("\n恒等式：随机作答 sum(S)==0 与 P 范围检查")
    import random
    random.seed(7)
    bad = 0
    for _ in range(300):
        answers = {it["id"]: random.choice([2, 1, -1, -2]) for it in items}
        r = score(answers, items)
        if abs(r["sum_check"]) > 1e-9 or not all(0 <= v <= 100 for v in r["P"].values()):
            bad += 1
    print(f"  300 组随机作答：异常 {bad} 组")
    fail += 1 if bad else 0
    print("\n自测结论：" + ("全部通过" if fail == 0 else f"有 {fail} 项未通过"))
    return 0 if fail == 0 else 1


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--selftest" in sys.argv or not args:
        return selftest()
    with open(args[0], encoding="utf-8") as f:
        answers = json.load(f)
    items_paths = ["data/items_a.json", "data/items_b.json", "data/items_c.json"]
    if "--quick" in sys.argv:
        items_paths = ["data/items_a.json", "data/items_b.json", "data/items_c.json"]
    try:
        items = load_items(items_paths)
    except FileNotFoundError:
        print("未找到题目文件，先做 selftest：--selftest")
        return 2
    if "--quick" in sys.argv:
        items = [it for it in items if it["id"].endswith("a")]
    res = score(answers, items)
    if "--json" in sys.argv:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(report(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
