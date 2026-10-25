// 成品回归测试：直接跑 index.html 里内嵌的计分脚本，验证「推导出的类型与功能栈」是否与标准一致。
// 之所以测成品而不是源码：v1.2 修的那个 bug 正是"源码对了、成品还是旧逻辑"。
const fs = require("fs");
const vm = require("vm");
const path = require("path");

const BASE = path.dirname(path.dirname(__filename));
const html = fs.readFileSync(path.join(BASE, "index.html"), "utf8");
const blocks = [...html.matchAll(/<script>\n([\s\S]*?)\n<\/script>/g)].map((m) => m[1]);
if (blocks.length < 1) throw new Error("成品里没有脚本块");

const ctx = { console };
vm.createContext(ctx);
vm.runInContext(blocks[0], ctx);
const J8 = ctx.J8;
if (!J8 || !J8.STACKS) throw new Error("成品里取不到计分内核");

const dataMatch = html.match(/var DATA = (\{[\s\S]*?\});\n/);
const DATA = JSON.parse(dataMatch[1].replace(/<\\\//g, "</"));

let fail = 0;
const types = Object.keys(J8.STACKS);
for (const code of types) {
  const stack = J8.STACKS[code];
  const weights = { Se: 0, Si: 0, Ne: 0, Ni: 0, Te: 0, Ti: 0, Fe: 0, Fi: 0 };
  stack.forEach((f, i) => { weights[f] = [4, 3, 2, 1][i]; });
  const answers = {};
  DATA.items.forEach((it) => {
    const d = weights[it.options.A.fn] - weights[it.options.B.fn];
    answers[it.id] = d > 0 ? 2 : d < 0 ? -2 : 1;
  });
  const r = J8.computeResult(answers, DATA.items);
  const got = r.stack.join("-");
  const want = stack.join("-");
  const ok = r.code === code && got === want;
  if (!ok) fail++;
  console.log(`  ${ok ? "PASS" : "FAIL"}  ${code}: 期望 ${want}，得到 ${r.code} ${got}`);
}
console.log(fail === 0 ? "\n结论：PASS（成品推导的 16 型功能栈全部正确）" : `\n结论：FAIL（${fail} 型不符）`);
process.exit(fail === 0 ? 0 : 1);
