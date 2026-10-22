// 读取 .parity_in.json，用 scoring.js 计算，写 .parity_js.json
const fs = require("fs");
const path = require("path");
const J8 = require("./scoring.js");

const T = __dirname;
const input = JSON.parse(fs.readFileSync(path.join(T, ".parity_in.json"), "utf8"));
const out = [];
for (const ans of input.cases) {
  const r = J8.computeResult(ans, input.items);
  out.push({
    S: r.S, P: r.P, dominant: r.dominant, auxiliary: r.auxiliary,
    tertiary: r.tertiary, inferior: r.inferior, code: r.code,
    jung_code: r.jung_code, top3: r.top3, gap: r.gap,
    consistency: r.consistency, confidence: r.confidence
  });
}
fs.writeFileSync(path.join(T, ".parity_js.json"), JSON.stringify(out));
console.log(`JS 计算 ${out.length} 组，写入 tools/.parity_js.json`);
