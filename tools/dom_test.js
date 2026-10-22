// 无浏览器环境下的 HTML 交互冒烟测试：用极简 DOM 桩把整份网页跑一遍。
// 覆盖：初始渲染 → 点完 56 题 → 出结果 → 快速版 28 题 → 复制摘要。
const fs = require("fs");
const vm = require("vm");
const path = require("path");

const BASE = path.resolve(__dirname, "..");
const file = path.join(BASE, "荣格八维人格测验·中国情境版.html");
const html = fs.readFileSync(file, "utf8");
const scripts = [...html.matchAll(/<script>\n([\s\S]*?)\n<\/script>/g)].map((m) => m[1]);
if (scripts.length !== 2) throw new Error("script 块数量异常：" + scripts.length);

let fails = 0;
const ok = (cond, msg) => { console.log((cond ? "  PASS " : "  FAIL ") + msg); if (!cond) fails++; };

function makeEl(id, attrs) {
  const el = {
    id, attrs: attrs || {}, style: {}, children: [], handlers: {},
    _text: "", _html: "", disabled: false, className: "",
    classList: {
      _s: new Set(),
      add(c) { this._s.add(c); }, remove(c) { this._s.delete(c); },
      contains(c) { return this._s.has(c); },
      toggle(c, force) { if (force === undefined) { this._s.has(c) ? this._s.delete(c) : this._s.add(c); } else if (force) this._s.add(c); else this._s.delete(c); }
    },
    addEventListener(ev, fn) { (this.handlers[ev] = this.handlers[ev] || []).push(fn); },
    getAttribute(k) { return this.attrs[k] === undefined ? null : this.attrs[k]; },
    querySelectorAll() { return []; },
    appendChild(c) { this.children.push(c); },
    removeChild(c) { this.children = this.children.filter((x) => x !== c); },
    select() {}, focus() {}
  };
  Object.defineProperty(el, "textContent", { get() { return this._text; }, set(v) { this._text = String(v); } });
  Object.defineProperty(el, "innerHTML", { get() { return this._html; }, set(v) { this._html = String(v); } });
  return el;
}

function run(mode) {
  const els = {};
  const get = (id) => (els[id] = els[id] || makeEl(id));
  // 量表 4 个按钮
  const scale = get("scale");
  scale.querySelectorAll = (sel) => (sel === "button"
    ? [2, 1, -1, -2].map((v, i) => (scale["b" + i] = scale["b" + i] || makeEl("b" + i, { "data-v": String(v) })))
    : []);
  // 两个模式按钮
  const modes = [makeEl("m0", { "data-mode": "full" }), makeEl("m1", { "data-mode": "quick" })];

  const document = {
    getElementById: get,
    querySelectorAll: (sel) => (sel === ".mode" ? modes : []),
    addEventListener() {},
    createElement: (t) => makeEl(t),
    body: makeEl("body"),
    execCommand() {}
  };
  const store = {};
  const ctx = {
    document,
    window: { scrollTo() {}, print() {} },
    localStorage: {
      getItem: (k) => (k in store ? store[k] : null),
      setItem: (k, v) => { store[k] = String(v); },
      removeItem: (k) => { delete store[k]; }
    },
    navigator: { clipboard: null },
    setTimeout: (fn) => fn(),
    console
  };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  scripts.forEach((s) => vm.runInContext(s, ctx, { timeout: 15000 }));

  ok(get("intro").classList.contains("hidden") === false, `${mode}：初始显示介绍页`);
  // 点模式按钮开始
  const startHandler = modes[mode === "full" ? 0 : 1].handlers.click[0];
  startHandler.call(modes[mode === "full" ? 0 : 1]);
  ok(get("test").classList.contains("hidden") === false, `${mode}：进入答题页`);
  const n = mode === "full" ? 56 : 28;
  ok(get("qno").textContent.indexOf("/ " + n) > 0, `${mode}：题量 ${n}（${get("qno").textContent}）`);
  ok(get("scenario").textContent.length > 8, `${mode}：题干非空`);
  ok(get("textA").textContent.length > 5 && get("textB").textContent.length > 5, `${mode}：两个选项非空`);

  // 逐题作答：按 A 的强度交替，制造一个有倾向的作答
  const order = ["b0", "b1"]; // data-v 2 / 1 → 偏 A
  for (let i = 0; i < n; i++) {
    const btn = scale[order[i % 2]];
    const h = btn.handlers.click[0];
    h.call(btn);
  }
  ok(get("result").classList.contains("hidden") === false, `${mode}：答完后显示结果页`);
  const res = get("result")._html;
  ok(res.length > 2000, `${mode}：结果 HTML 长度 ${res.length}`);
  ok(/class="code">[EI][SN][TF][JP]</.test(res), `${mode}：结果含四字母类型码`);
  ok(res.indexOf("功能栈") > 0 && res.indexOf("八维相对强度") > 0, `${mode}：含功能栈与八维条`);
  ok(res.indexOf("置信度") > 0, `${mode}：含置信度`);
  ok(res.indexOf("荣格归属") > 0, `${mode}：含荣格归属`);
  ok(res.indexOf("压力下的样子") > 0, `${mode}：含压力段落`);
  ok(res.indexOf("undefined") < 0 && res.indexOf("NaN") < 0, `${mode}：结果里没有 undefined / NaN`);
  // 重新开始按钮可用
  ok(typeof get("againBtn").onclick === "function", `${mode}：重新开始按钮已绑定`);
  get("againBtn").onclick();
  ok(get("test").classList.contains("hidden") === false, `${mode}：重新开始回到答题页`);
  return res;
}

console.log("== 完整版 ==");
const full = run("full");
console.log("== 快速版 ==");
run("quick");

// 结果摘要复制文本
const m = full.match(/class="code">([EI][SN][TF][JP])</);
ok(!!m, "能从结果页取出类型码：" + (m ? m[1] : "无"));
console.log(fails === 0 ? "\n结论：PASS（DOM 桩冒烟测试通过）" : `\n结论：FAIL（${fails} 项）`);
process.exit(fails === 0 ? 0 : 1);
