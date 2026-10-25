// 7 点量表版的冒烟测试（无浏览器，用最小 DOM 桩）
const fs = require("fs");
const vm = require("vm");
const path = require("path");

const file = path.join(path.dirname(path.dirname(__filename)), "index.html");
const html = fs.readFileSync(file, "utf8");
const scripts = [...html.matchAll(/<script>\n([\s\S]*?)\n<\/script>/g)].map((m) => m[1]);
if (scripts.length !== 2) throw new Error("script 块数量异常：" + scripts.length);

let fails = 0;
const ok = (c, m) => { console.log((c ? "  PASS " : "  FAIL ") + m); if (!c) fails++; };

function makeEl(id, attrs) {
  const el = {
    id, attrs: attrs || {}, style: {}, children: [], handlers: {}, _text: "", _html: "",
    disabled: false, className: "",
    classList: { _s: new Set(), add(c) { this._s.add(c); }, remove(c) { this._s.delete(c); },
      contains(c) { return this._s.has(c); },
      toggle(c, f) { if (f === undefined) { this._s.has(c) ? this._s.delete(c) : this._s.add(c); } else if (f) this._s.add(c); else this._s.delete(c); } },
    addEventListener(e, f) { (this.handlers[e] = this.handlers[e] || []).push(f); },
    getAttribute(k) { return this.attrs[k] === undefined ? null : this.attrs[k]; },
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
const ctx = {
  document, window: { scrollTo() {}, print() {} },
  localStorage: { getItem: () => null, setItem() {}, removeItem() {} },
  navigator: { clipboard: null }, setTimeout: (fn) => fn(), console
};
ctx.globalThis = ctx;
vm.createContext(ctx);
scripts.forEach((s) => vm.runInContext(s, ctx, { timeout: 15000 }));

const D = ctx.window.__LIKERT_DEBUG;
ok(!!D, "暴露了测试钩子");
ok((get("scale")._html.match(/<button/g) || []).length === 7, "量表渲染出 7 个选项：" + (get("scale")._html.match(/<button/g) || []).length);
ok(typeof get("startBtn").handlers.click[0] === "function", "开始按钮已绑定");

D.start();
ok(get("test").classList.contains("hidden") === false, "进入答题页");
ok(get("statement").textContent.length > 5, "题干非空：" + get("statement").textContent.slice(0, 14) + "…");

for (let i = 0; i < 50; i++) D.choose(i % 7);   // 走一遍全 50 题
ok(get("result").classList.contains("hidden") === false, "答完显示结果页");
const res = get("result")._html;
ok(res.length > 2000, "结果 HTML 长度 " + res.length);
ok(res.indexOf("五个维度") > 0, "含五维区块");
ok(res.indexOf("25 个面向") > 0, "含面向区块");
ok(/class="code">[EI?][NS?][TF?][JP?]-[AT?]</.test(res), "含四字母+身份码");
ok(res.indexOf("undefined") < 0 && res.indexOf("NaN") < 0, "结果里没有 undefined / NaN");
ok(typeof get("againBtn").onclick === "function", "重新开始已绑定");
ok((get("aiPrompt").value || "").length > 800, "AI 提示词长度 " + (get("aiPrompt").value || "").length);

const r = D.compute();
ok(Object.keys(r.dims).length === 5, "五维都有分：" + Object.keys(r.dims).join(","));
ok(r.letters.length === 5, "字母串长度 5：" + r.letters);
ok(Object.keys(r.facets).length === 25, "面向数 25：" + Object.keys(r.facets).length);

console.log(fails === 0 ? "\n结论：PASS（7 点量表版冒烟测试通过）" : `\n结论：FAIL（${fails} 项）`);
process.exit(fails === 0 ? 0 : 1);
