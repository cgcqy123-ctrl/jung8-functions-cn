// 冒烟测试：完整版 152 题与精简版 80 题都跑一遍（无浏览器，最小 DOM 桩）
const fs = require("fs");
const vm = require("vm");
const path = require("path");

const ROOT = path.dirname(path.dirname(__filename));
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
    setAttribute(k, v) { this.attrs[k] = v; },
    querySelectorAll() { return []; }, appendChild(c) { this.children.push(c); },
    removeChild(c) { this.children = this.children.filter((x) => x !== c); }, select() {}
  };
  Object.defineProperty(el, "textContent", { get() { return this._text; }, set(v) { this._text = String(v); } });
  Object.defineProperty(el, "innerHTML", { get() { return this._html; }, set(v) { this._html = String(v); } });
  return el;
}

function runPage(file, expectN, expectMode) {
  const html = fs.readFileSync(path.join(ROOT, file), "utf8");
  const scripts = [...html.matchAll(/<script>\n([\s\S]*?)\n<\/script>/g)].map((m) => m[1]);
  console.log(`\n=== ${file}（应为 ${expectN} 题 / ${expectMode}） ===`);
  ok(scripts.length === 2, `script 块 ${scripts.length} 个（应 2）`);

  const els = {};
  const get = (id) => (els[id] = els[id] || makeEl(id));
  const document = {
    getElementById: get, querySelectorAll: () => [], addEventListener() {},
    createElement: (t) => makeEl(t), body: makeEl("body"), execCommand() {}, title: ""
  };
  const store = { _d: {}, getItem(k) { return this._d[k] === undefined ? null : this._d[k]; },
    setItem(k, v) { this._d[k] = String(v); }, removeItem(k) { delete this._d[k]; } };
  const ctx = { document, window: { scrollTo() {}, print() {} },
    localStorage: store,
    navigator: { clipboard: null }, setTimeout: (fn) => fn(), console };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  scripts.forEach((s) => vm.runInContext(s, ctx, { timeout: 30000 }));

  const J = ctx.J8L, D = ctx.window.__J8L_DEBUG, DATA = ctx.DATA;
  ok(!!J && !!D, "计分内核与测试钩子就绪");
  ok(DATA.items.length === expectN, `题库 ${expectN} 题：${DATA.items.length}`);
  ok(DATA.meta && DATA.meta.mode === expectMode, `模式标记：${DATA.meta && DATA.meta.mode}`);
  ok(Object.keys(DATA.types).length === 16, "16 型画像");
  ok(Object.keys(DATA.jung).length === 8, "8 个荣格类型");
  ok((get("scale")._html.match(/<button/g) || []).length === 7, "7 档按钮");
  ok(String(D.saveKey).indexOf(expectMode) > 0, `存档 key 按版本隔离：${D.saveKey}`);

  // 随机顺序：是排列、相邻不同功能（跑 20 次）
  let permBad = 0, adjBad = 0;
  const want = DATA.items.map((x) => x.id).sort().join(",");
  for (let t = 0; t < 20; t++) {
    const seq = J.interleave(DATA.items);
    if (seq.map((x) => x.id).sort().join(",") !== want) permBad++;
    for (let i = 1; i < seq.length; i++) if (seq[i].fn === seq[i - 1].fn) { adjBad++; break; }
  }
  ok(permBad === 0, `20 次洗牌都是完整排列（异常 ${permBad}）`);
  ok(adjBad === 0, `20 次洗牌都无相邻同功能（异常 ${adjBad}）`);

  // 定向断言：只在 Se 正向题上给「强烈同意」
  const only = {};
  DATA.items.forEach((it) => { only[it.id] = 0; });
  DATA.items.filter((it) => it.fn === "Se" && !it.reverse).forEach((it) => { only[it.id] = 6; });
  DATA.items.filter((it) => it.fn === "Se" && it.reverse).forEach((it) => { only[it.id] = 0; });
  const r1 = J.computeResult(only, DATA.items);
  ok(r1.dominant === "Se", "偏 Se 作答 → 主导 Se：" + r1.dominant);
  ok(r1.stack.join("-") === "Se-Ti-Fe-Ni", "功能栈 Se-Ti-Fe-Ni：" + r1.stack.join("-"));
  ok(r1.code === "ESTP", "四字母 ESTP：" + r1.code);

  // 反向题方向：只对 Se 的反向题给「强烈同意」（＝否认 Se），Se 应被压到八维最低
  const reverseSe = {};
  DATA.items.forEach((it) => { reverseSe[it.id] = 3; });                       // 全部中立
  DATA.items.filter((it) => it.fn === "Se" && it.reverse).forEach((it) => { reverseSe[it.id] = 6; });
  const r2 = J.computeResult(reverseSe, DATA.items);
  ok(r2.scores.Se < 50, "同意 Se 反向题会压低 Se 分：" + r2.scores.Se);
  ok(r2.order[r2.order.length - 1] === "Se", "Se 落到八维末位：" + r2.order.join("-"));

  // 存档校验：题序不属于本版本题库的存档必须拒绝续答（两版曾共用 key 导致串档）
  const badOrder = { values: { [DATA.items[0].id]: 3 }, order: [DATA.items[0].id], idx: 0 };
  ok(D.resume(badOrder) === null, "题序不完整的存档被拒绝");
  const badIds = { values: { "XX-01": 3 }, order: DATA.items.map((x) => x.id), idx: 1 };
  badIds.order[0] = "XX-01";
  ok(D.resume(badIds) === null, "含未知题号的存档被拒绝");
  const goodSave = { values: { [DATA.items[0].id]: 3 }, order: DATA.items.map((x) => x.id), idx: 1 };
  ok(!!D.resume(goodSave), "本版本题序的存档可以续答");

  // 全中立
  const mid = {};
  DATA.items.forEach((it) => { mid[it.id] = 3; });
  const r3 = J.computeResult(mid, DATA.items);
  ok(Object.keys(r3.scores).every((f) => Math.abs(r3.scores[f] - 50) < 0.01), "全中立 → 八维均 50");
  ok(r3.confidence === "低", "全中立 → 置信度低");

  // 走一遍 UI
  D.start();
  ok(!get("test").classList.contains("hidden"), "进入答题页");
  ok(D.order().length === expectN && new Set(D.order()).size === expectN, `作答顺序覆盖 ${expectN} 题且不重复`);
  for (let i = 0; i < expectN; i++) D.choose(i % 7);
  ok(!get("result").classList.contains("hidden"), "答完显示结果页");
  const res = get("result")._html;
  ok(/class="code">[EI][NS][TF][JP]</.test(res), "结果含四字母码");
  ok(res.indexOf("功能栈") > 0 && res.indexOf("八维强度") > 0 && res.indexOf("候选类型") > 0, "核心区块齐全");
  ok(res.indexOf("undefined") < 0 && res.indexOf("NaN") < 0, "结果无 undefined / NaN");
  ok((get("aiPrompt").value || "").length > 700, "AI 提示词已生成");
  ok(String((get("manualBtn").attrs || {}).href || "").indexOf(".docx") > 0, "手册下载按钮已绑定");
  ok(String((get("altLink").attrs || {}).href || "").indexOf(".html") > 0, "另一版本互链已绑定：" + (get("altLink").attrs || {}).href);
}

runPage("index.html", 152, "full");
runPage("lite.html", 80, "lite");

console.log(fails === 0 ? "\n结论：PASS（完整版 + 精简版冒烟测试通过）" : `\n结论：FAIL（${fails} 项）`);
process.exit(fails === 0 ? 0 : 1);
