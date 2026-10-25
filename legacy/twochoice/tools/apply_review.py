# -*- coding: utf-8 -*-
"""按 research/03_item_review.md 的结论修订题目文案（必须改 6 题 + 建议改 7 题）。

只改文案/场景，不增删题目、不改配对与方向。改完必须重跑 check_items。
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")

PATCH = {
    # ---- 必须改 ----
    "Q02b": {
        "options": {"A": {"text": "你先往下想：这钱出去会牵出哪些事——他生意、你年底买房。"},
                    "B": {"text": "你先问清具体：哪天要、分几次还、转账还是现金，问完再说。"}},
        "rationale": {"A": "由一个点发散出多条后果链", "B": "先接住眼前的具体条件"},
    },
    "Q03a": {
        "options": {"A": {"text": "你一坐下就上手，谁杯子空了就满上，跟着桌上的节奏来。"},
                    "B": {"text": "你坐下时忽然想到：这一桌人往后怕是难再凑这么齐。"}},
        "rationale": {"A": "对眼前场面即时上手张罗", "B": "从一场席里抽出往后的走向"},
    },
    "Q11a": {
        "options": {"A": {"text": "你先想清楚这顿图什么：省时间就点，省钱就煮，定了再动。"},
                    "B": {"text": "你不管哪个更划算，就想吃口自己做的，洗手就开火。"}},
        "rationale": {"A": "先定判断标准再落到动作", "B": "按内在想要直接动手"},
    },
    "Q16b": {
        "options": {"A": {"text": "你照自己平时爱吃的点，不为显得好相处改口味。"},
                    "B": {"text": "你翻菜单先看今天有什么新鲜的，抬头问服务员哪样卖得好。"}},
        "rationale": {"A": "按自己真实的口味和界限来选", "B": "抓当下的具体信息再定"},
    },
    "Q17a": {
        "scenario": "几个朋友聚会，饭吃完，账单放在桌子中间，大家还在聊天。",
        "domain": "社交人情",
        "options": {"A": {"text": "你想起上回是老张结的，这回该你了，伸手把单拿过来。"},
                    "B": {"text": "你拿过账单按人一除，说清每人多少，现场收齐。"}},
        "rationale": {"A": "调用旧惯例定这次怎么办", "B": "定规则、当场把流程推完"},
    },
    "Q20b": {
        "options": {"A": {"text": "你挑那个你打心里认同的角色，别的先不管。"},
                    "B": {"text": "你先问老板，上回玩得最尽兴的那本是什么路数。"}},
        "rationale": {"A": "按内在认同来选角色", "B": "拿过去愉快的具体经验作参照"},
    },
    # ---- 建议改 ----
    "Q01b": {
        "options": {"B": {"text": "你看文里写的一天三顿、顿顿那几样，说这么吃你撑不过三天。"}},
        "rationale": {"B": "抓住文里的具体细节直接回应"},
    },
    "Q04a": {
        "options": {"A": {"text": "你照上周的格式，把在办的事一项项列清楚，进度写到哪一步。"},
                    "B": {"text": "你盯着那几件零碎，忽然发现能拼成一条线，顺手多想了两步。"}},
        "rationale": {"A": "沿用旧格式逐项列清", "B": "把零碎连成新的组合"},
    },
    "Q12b": {
        "options": {"A": {"text": "你认准了要去看的那一场，就只刷那一场，别的不点。"}},
        "rationale": {"A": "只锁定自己认定的那场"},
    },
    "Q19a": {
        "options": {"B": {"text": "你先替那位老人觉得难受，在评论区说上两句，别的先不管。"}},
        "rationale": {"B": "先照顾受委屈一方的感受"},
    },
    "Q21b": {
        "options": {"B": {"text": "你把能想到的乐器列出来，挨个看上手难不难。"}},
        "rationale": {"B": "把选项铺开逐个看"},
    },
    "Q22a": {
        "options": {"A": {"text": "你把能想到的走法都列出来，说每条各通向哪、大概多久。"},
                    "B": {"text": "你拿太阳方位和山势比，先定哪边是北，再倒推公路在哪。"}},
        "rationale": {"A": "先铺开多种可能再挑", "B": "由前提一步步推结论"},
    },
    "Q25a": {
        "options": {"A": {"text": "你心里先落下一个判断：这项目的问题不在数据，在分工。"}},
        "rationale": {"A": "直接收束到问题的真正所在"},
    },
}


def apply(path: str) -> int:
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    hits = 0
    for it in d["items"]:
        p = PATCH.get(it["id"])
        if not p:
            continue
        hits += 1
        if "scenario" in p:
            it["scenario"] = p["scenario"]
        if "domain" in p:
            it["domain"] = p["domain"]
        for side, patch in p.get("options", {}).items():
            for k in ("fn", "text"):
                if k in patch:
                    it["options"][side][k] = patch[k]
        for side, patch in p.get("rationale", {}).items():
            it["rationale"][side] = patch
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return hits


def main() -> int:
    total = 0
    for name in ("items_a.json", "items_b.json"):
        n = apply(os.path.join(DATA, name))
        total += n
        print(f"{name}: 修订 {n} 题")
    print(f"合计修订 {total} 题（预期 13）")
    return 0 if total == 13 else 1


if __name__ == "__main__":
    sys.exit(main())
