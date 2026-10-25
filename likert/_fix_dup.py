# -*- coding: utf-8 -*-
"""去掉 template.html 末尾重复的"继续上次"代码块。"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html")
DUP = '''  var saved = null;
  try { saved = JSON.parse(localStorage.getItem(SAVE) || "null"); } catch (e) {}
  if (saved && saved.answers && Object.keys(saved.answers).length && saved.idx < LIKERT.items.length) {
    state = saved;
    $("startBtn").innerHTML = "<b>继续上次</b><span>已答 " + Object.keys(saved.answers).length + " / " + LIKERT.items.length + " 题</span>";
    $("startBtn").addEventListener("click", function () { start(true); });
  }
'''

with io.open(P, encoding="utf-8") as f:
    t = f.read()
n = t.count(DUP)
if n != 1:
    print(f"[WARN] 重复块命中 {n} 次，未改动")
    raise SystemExit(1)
t = t.replace(DUP, "")
with io.open(P, "w", encoding="utf-8", newline="\n") as f:
    f.write(t)
print("[OK] 已删除重复的续答块")
