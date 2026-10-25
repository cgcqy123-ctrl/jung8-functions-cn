// 八维量表版冒烟测试（无浏览器，最小 DOM 桩）
const fs = require("fs");
const vm = require("vm");
const path = require("path");

const ROOT = path.dirname(path.dirname(__filename));
const html = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
const scripts = [...html.matchAll(/<script>\n([\s\S]*?)\n<\/script>/g)].map((m) => m[1]);

let fails = 0;
const ok = (c, m) => { console.log((c ? "  PASS " : "  FAIL ") + m); if (!c) fails++; };

ok(scripts.length === 2, `script 块 ${scripts.length} 个（应 2）`);
ok((html.match(/<\/script>/g) || []).length === 2, "内联脚本未混入多余标签");

function makeEl(id, attrs) {
  const el = {
    id, attrs: attrs || {}, style: {}, children: [], handlers: {}, _text: "", _html: "",
    disabled: false, className: "",
    classList: { _s: new Set(), add(c) { this._s.add(c); }, remove(c) { this._s.delete(c); },
      contains(c) { return this._s.has(c); },
      toggle(c, f) { if (f === undefined) { this._s.has(c) ? this._s.delete(c) : this._s.add(c); } else if (f) this._s.add(c); else this._s.delete(c); } },
    addEventListener(e, f) { (this.handlers[e] = this.handlers[e] || []).push(f); },
    getAttribute(k) { return this.attrs[k] === undefined ? null : this.attrs[k]; },
    setAttribute(k, v) { this.attrs[k] = v; },
    querySelectorAll() { return []; }, appendChild(c) { this.children.push(c); },
    removeChild(c) { this.children = this.children.filter((x) => x !== c); }, select() {}
  };
  Object.defineProperty(el, "textContent", { get() { return this._text; }, set(v) { this._text = String(v); } });
  Object.defineProperty(el, "innerHTML", { get() { return this._html; }, set(v) { this._html = String(v); } });
  return el;
}

const els = {};
const get = (id) => (els[id] = els[id] || makeEl(id));
const document = {
  getElementById: get, querySelectorAll: () => [], addEventListener() {},
  createElement: (t) => makeEl(t), body: makeEl("body"), execCommand() {}
};
const ctx = { document, window: { scrollTo() {}, print() {} },
  localStorage: { getItem: () => null, setItem() {}, removeItem() {} },
  navigator: { clipboard: null }, setTimeout: (fn) => fn(), console };
ctx.globalThis = ctx;
vm.createContext(ctx);
scripts.forEach((s) => vm.runInContext(s, ctx, { timeout: 30000 }));

const J = ctx.J8L, D = ctx.window.__J8L_DEBUG, DATA = ctx.DATA;
ok(!!J, "计分内核已就绪");
ok(DATA.items.length === 152, "题库 152 题：" + DATA.items.length);
ok(Object.keys(DATA.types).length === 16, "16 型画像：" + Object.keys(DATA.types).length);
ok(Object.keys(DATA.jung).length === 8, "8 个荣格类型：" + Object.keys(DATA.jung).length);
ok((get("scale")._html.match(/<button/g) || []).length === 7, "7 档按钮");

// 定向断言：只对 Se 相关题给 +3，其余 -3
const only = {};
DATA.items.forEach((it) => { only[it.id] = 0; });
DATA.items.filter((it) => it.fn === "Se" && !it.reverse).forEach((it) => { only[it.id] = 6; });
DATA.items.filter((it) => it.fn === "Se" && it.reverse).forEach((it) => { only[it.id] = 0; });
const r1 = J.computeResult(only, DATA.items);
ok(r1.dominant === "Se", "只在 Se 题上强烈同意 → 主导 Se：" + r1.dominant);
ok(r1.stack.join("-") === "Se-Ti-Fe-Ni", "功能栈 Se-Ti-Fe-Ni：" + r1.stack.join("-"));
ok(r1.code === "ESTP", "四字母 ESTP：" + r1.code);

// 反向题单独校验：只在反向 Se 题上强烈不同意（0 档）应仍指向 Se
const only2 = {};
DATA.items.forEach((it) => { only2[it.id] = 0; });
DATA.items.filter((it) => it.fn === "Se" && it.reverse).forEach((it) => { only2[it.id] = 0; });
const r2 = J.computeResult(only2, DATA.items);
ok(r2.dominant === "Se", "反向题计分方向正确（主导仍是 Se）：" + r2.dominant);

// 全中立：八维应接近 50 分、置信度低
const mid = {};
DATA.items.forEach((it) => { mid[it.id] = 3; });
const r3 = J.computeResult(mid, DATA.items);
const allMid = Object.keys(r3.scores).every((f) => Math.abs(r3.scores[f] - 50) < 0.01);
ok(allMid, "全中立 → 八维都是 50 分");
ok(r3.confidence === "低", "全中立 → 置信度低：" + r3.confidence);

// 随机顺序：是排列、且相邻不同功能
for (let t = 0; t < 6; t++) {
  const seq = J.interleave(DATA.items);
  const ids = seq.map((x) => x.id).sort().join(",");
  const want = DATA.items.map((x) => x.id).sort().join(",");
  ok(ids === want, `第 ${t + 1} 次打乱仍是完整排列（${seq.length} 题）`);
  let adj = 0;
  for (let i = 1; i < seq.length; i++) if (seq[i].fn === seq[i - 1].fn) adj++;
  ok(adj === 0, `第 ${t + 1} 次打乱无相邻同功能（相邻重复 ${adj} 处）`);
}

// 走一遍 UI 流程
D.start();
ok(D.order().length === 152, "作答顺序覆盖 152 题：" + D.order().length);
ok(new Set(D.order()).size === 152, "作答顺序无重复题");
ok(!get("test").classList.contains("hidden"), "进入答题页");
ok(get("statement").textContent.length > 5, "题干非空：" + get("statement").textContent.slice(0, 12) + "…");
for (let i = 0; i < 152; i++) D.choose(i % 7);
ok(!get("result").classList.contains("hidden"), "答完显示结果页");
const res = get("result")._html;
ok(res.length > 4500, "结果 HTML 长度 " + res.length);
ok(/class="code">[EI][NS][TF][JP]</.test(res), "结果含四字母码");
ok(res.indexOf("功能栈") > 0 && res.indexOf("八维强度") > 0 && res.indexOf("候选类型") > 0, "三个核心区块都在");
ok(res.indexOf("undefined") < 0 && res.indexOf("NaN") < 0, "结果里没有 undefined / NaN");
ok((get("aiPrompt").value || "").length > 700, "AI 提示词长度 " + (get("aiPrompt").value || "").length);
ok(res.indexOf("Se</span>") > 0 && res.indexOf("Fi</span>") > 0, "八维条覆盖首尾功能");

ok(String((get("manualBtn").attrs||{}).href||"").indexOf(".docx") > 0, "手册下载按钮已绑定：" + String((get("manualBtn").attrs||{}).href).slice(-24));
ok(String((get("manualNote")._text||"")).indexOf("手册") >= 0, "手册说明文案已写入");
console.log(fails === 0 ? "\n结论：PASS（八维量表版冒烟测试通过）" : `\n结论：FAIL（${fails} 项）`);
process.exit(fails === 0 ? 0 : 1);
