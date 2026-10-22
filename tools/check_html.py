# -*- coding: utf-8 -*-
"""HTML 成品静态检查：数据完整性、占位符残留、脚本可解析性、关键字段。

用法：python tools/check_html.py
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(BASE, "index.html")
TMP = os.path.join(BASE, "tools", ".tmp_app.js")


def main() -> int:
    if not os.path.exists(HTML):
        print("缺少 HTML 成品")
        return 1
    with open(HTML, encoding="utf-8") as f:
        html = f.read()
    errors, warns = [], []

    print(f"文件大小：{len(html)/1024:.1f} KB")
    if "__DATA__" in html or "__SCORING__" in html:
        errors.append("模板占位符未替换")
    if html.count("</script>") != 2:
        warns.append(f"</script> 出现 {html.count('</script>')} 次（应为 2）")

    m = re.search(r'var DATA = (\{.*?\});\n', html, re.S)
    if not m:
        errors.append("找不到 DATA 常量")
        data = None
    else:
        try:
            data = json.loads(m.group(1).replace("<\\/", "</"))
        except json.JSONDecodeError as e:
            errors.append(f"DATA 不是合法 JSON：{e}")
            data = None

    if data:
        items, types, jung = data.get("items", []), data.get("types", {}), data.get("jung", {})
        print(f"题目 {len(items)} 题，类型 {len(types)} 个，荣格类型 {len(jung)} 个")
        if len(items) != 56:
            errors.append(f"题目数应为 56，实际 {len(items)}")
        ids = [it["id"] for it in items]
        expect = [f"Q{n:02d}{s}" for n in range(1, 29) for s in ("a", "b")]
        if sorted(ids) != sorted(expect):
            errors.append("题号集合不完整")
        for it in items:
            for side in ("A", "B"):
                if not it["options"][side].get("text"):
                    errors.append(f"{it['id']} 选项 {side} 无文本")
                if it["options"][side].get("fn") not in (
                        "Se", "Si", "Ne", "Ni", "Te", "Ti", "Fe", "Fi"):
                    errors.append(f"{it['id']} 选项 {side} 功能非法")
        if set(types) != {"INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
                          "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"}:
            errors.append("十六型集合不完整")
        if set(jung) != {"ET", "IT", "EF", "IF", "ES", "IS", "EN", "IN"}:
            errors.append("荣格八型代码集合不对")
        if len(jung) != 8:
            errors.append("荣格八型不完整")
        for code, t in types.items():
            for f in ("cn_name", "core", "work", "family", "love", "stress", "growth"):
                if not t.get(f):
                    errors.append(f"{code} 缺字段 {f}")
            if len(t.get("stack") or []) != 4:
                errors.append(f"{code} 功能栈不是 4 位")
        for code, j in jung.items():
            for f in ("name", "essence", "everyday", "blind"):
                if not j.get(f):
                    errors.append(f"{code} 缺字段 {f}")
        # 三个速答路径的可达性（静态检查）
        for token in ('id="scale"', 'id="result"', 'id="intro"', 'choose(', 'computeResult'):
            if token not in html:
                errors.append(f"缺少关键片段：{token}")

    # 抽出应用脚本供 node --check
    blocks = re.findall(r"<script>\n(.*?)\n</script>", html, re.S)
    if len(blocks) >= 2:
        with open(TMP, "w", encoding="utf-8") as f:
            f.write(blocks[-1])
        print(f"应用脚本已导出：{TMP}（{len(blocks[-1])/1024:.1f} KB）")
    else:
        warns.append(f"脚本块数量异常：{len(blocks)}")

    if warns:
        print("\n--- 提醒 ---")
        for w in warns:
            print("  ! " + w)
    if errors:
        print("\n--- 错误 ---")
        for e in errors:
            print("  x " + e)
        print("\n结论：FAIL")
        return 1
    print("\n结论：PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
