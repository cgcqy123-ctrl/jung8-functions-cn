/* 八维量表计分内核（7 点同意度 → 八功能强度 → 荣格类型） */
var J8L = (function () {
  var FUNCS = ["Se", "Si", "Ne", "Ni", "Te", "Ti", "Fe", "Fi"];
  var PERC = { Se: 1, Si: 1, Ne: 1, Ni: 1 };
  var JUDG = { Te: 1, Ti: 1, Fe: 1, Fi: 1 };
  var ATT = { Se: "E", Si: "I", Ne: "E", Ni: "I", Te: "E", Ti: "I", Fe: "E", Fi: "I" };
  // 第三/劣势：同类、功能对立、态度相反
  var MAP = { Te: "Fi", Ti: "Fe", Fe: "Ti", Fi: "Te", Se: "Ni", Si: "Ne", Ne: "Si", Ni: "Se" };
  var FN_CN = { Se: "外倾感觉", Si: "内倾感觉", Ne: "外倾直觉", Ni: "内倾直觉",
                Te: "外倾思维", Ti: "内倾思维", Fe: "外倾情感", Fi: "内倾情感" };
  var JUNG_OF = { Te: ["ET", "外倾思维型"], Ti: ["IT", "内倾思维型"],
                  Fe: ["EF", "外倾情感型"], Fi: ["IF", "内倾情感型"],
                  Se: ["ES", "外倾感觉型"], Si: ["IS", "内倾感觉型"],
                  Ne: ["EN", "外倾直觉型"], Ni: ["IN", "内倾直觉型"] };
  var STACKS = {
    INTJ: ["Ni", "Te", "Fi", "Se"], INTP: ["Ti", "Ne", "Si", "Fe"],
    ENTJ: ["Te", "Ni", "Se", "Fi"], ENTP: ["Ne", "Ti", "Fe", "Si"],
    INFJ: ["Ni", "Fe", "Ti", "Se"], INFP: ["Fi", "Ne", "Si", "Te"],
    ENFJ: ["Fe", "Ni", "Se", "Ti"], ENFP: ["Ne", "Fi", "Te", "Si"],
    ISTJ: ["Si", "Te", "Fi", "Ne"], ISFJ: ["Si", "Fe", "Ti", "Ne"],
    ESTJ: ["Te", "Si", "Ne", "Fi"], ESFJ: ["Fe", "Si", "Ne", "Ti"],
    ISTP: ["Ti", "Se", "Ni", "Fe"], ISFP: ["Fi", "Se", "Ni", "Te"],
    ESTP: ["Se", "Ti", "Fe", "Ni"], ESFP: ["Se", "Fi", "Te", "Ni"]
  };
  var CN_NAME = {
    INTJ: "远景架构者", INTP: "原理拆解者", ENTJ: "目标统帅者", ENTP: "可能性发动机",
    INFJ: "深察引路者", INFP: "价值守火者", ENFJ: "人心凝聚者", ENFP: "火花点燃者",
    ISTJ: "秩序守护者", ISFJ: "细致托底者", ESTJ: "事务操盘者", ESFJ: "场面照拂者",
    ISTP: "现场解题者", ISFP: "感受力行家", ESTP: "临场破局者", ESFP: "即兴享乐者"
  };
  var W = [1.0, 0.6, 0.3, 0.1];

  function mean(a) { var s = 0; a.forEach(function (x) { s += x; }); return s / a.length; }
  function rank(xs) {
    var idx = xs.map(function (v, i) { return i; }).sort(function (a, b) { return xs[a] - xs[b]; });
    var r = new Array(xs.length), i = 0;
    while (i < idx.length) {
      var j = i;
      while (j + 1 < idx.length && xs[idx[j + 1]] === xs[idx[i]]) j++;
      var avg = (i + j) / 2 + 1;
      for (var k = i; k <= j; k++) r[idx[k]] = avg;
      i = j + 1;
    }
    return r;
  }
  function pearson(a, b) {
    var ma = mean(a), mb = mean(b), cov = 0, va = 0, vb = 0;
    for (var i = 0; i < a.length; i++) {
      cov += (a[i] - ma) * (b[i] - mb);
      va += (a[i] - ma) * (a[i] - ma);
      vb += (b[i] - mb) * (b[i] - mb);
    }
    if (va === 0 || vb === 0) return 0;
    return cov / Math.sqrt(va * vb);
  }
  function spearman(a, b) { return pearson(rank(a), rank(b)); }

  function profile(values, items, filter) {
    var acc = {}, n = {};
    FUNCS.forEach(function (f) { acc[f] = 0; n[f] = 0; });
    items.forEach(function (it, i) {
      var raw = values[it.id];
      if (raw === undefined) return;
      if (filter && !filter(i)) return;
      var v = raw - 3;                       // 0..6 → -3..3
      if (it.reverse) v = -v;                // 反向题翻转
      acc[it.fn] += v; n[it.fn] += 1;
    });
    var out = {};
    FUNCS.forEach(function (f) { out[f] = n[f] ? acc[f] / n[f] : 0; });
    return out;
  }

  function computeResult(values, items) {
    var m = profile(values, items);
    var scores = {}, avg = 0;
    FUNCS.forEach(function (f) { scores[f] = Math.round((m[f] + 3) / 6 * 1000) / 10; avg += scores[f]; });
    avg = avg / 8;
    var c = {};
    FUNCS.forEach(function (f) { c[f] = Math.round((scores[f] - avg) * 10) / 10; });

    var order = FUNCS.slice().sort(function (a, b) {
      return (c[b] - c[a]) || (FUNCS.indexOf(a) - FUNCS.indexOf(b));
    });
    var dom = order[0];
    var otherIsPerc = !PERC[dom];
    var cand = FUNCS.filter(function (f) {
      var isPerc = !!PERC[f];
      return (otherIsPerc ? isPerc : !isPerc) && ATT[f] !== ATT[dom];
    }).sort(function (a, b) { return (c[b] - c[a]) || (FUNCS.indexOf(a) - FUNCS.indexOf(b)); });
    var aux = cand[0], tert = MAP[aux], inf = MAP[dom];

    var ei = ATT[dom], sn, tf;
    if (PERC[dom]) { sn = (dom === "Ne" || dom === "Ni") ? "N" : "S"; tf = (aux === "Te" || aux === "Ti") ? "T" : "F"; }
    else { tf = (dom === "Te" || dom === "Ti") ? "T" : "F"; sn = (aux === "Ne" || aux === "Ni") ? "N" : "S"; }
    var extFn = ATT[dom] === "E" ? dom : aux;
    var jp = JUDG[extFn] ? "J" : "P";
    var code = ei + sn + tf + jp;

    var fits = [], ranked = [];
    Object.keys(STACKS).forEach(function (t) {
      var st = STACKS[t], v = 0;
      for (var i = 0; i < 4; i++) v += W[i] * c[st[i]];
      fits.push([t, Math.round(v * 100) / 100]);
    });
    ranked = fits.slice().sort(function (a, b) { return b[1] - a[1]; });

    var half = [true, false].map(function (odd) {
      return profile(values, items, function (i) { return (i % 2 === 0) === odd; });
    });
    var hs = half.map(function (p) {
      var s = {};
      FUNCS.forEach(function (f) { s[f] = (p[f] + 3) / 6 * 100; });
      return s;
    });
    var r = Math.round(spearman(FUNCS.map(function (f) { return hs[0][f]; }),
                                FUNCS.map(function (f) { return hs[1][f]; })) * 100) / 100;
    var gap = Math.round((c[order[0]] - c[order[1]]) * 10) / 10;
    var conf = (gap >= 6 && r >= 0.5) ? "高" : ((gap >= 3 && r >= 0.25) ? "中" : "低");

    return {
      scores: scores, centered: c, order: order,
      dominant: dom, auxiliary: aux, tertiary: tert, inferior: inf,
      code: code, jung_code: JUNG_OF[dom][0], jung_name: JUNG_OF[dom][1],
      cn_name: CN_NAME[code], stack: [dom, aux, tert, inf],
      top3: ranked.slice(0, 3), gap: gap, consistency: r, confidence: conf,
      mismatch: ranked[0][0] !== code,
      answered: Object.keys(values).length, total: items.length
    };
  }

  /* ---------- 出题顺序：随机 + 同功能不相邻 ---------- */
  function shuffled(a, rand) {
    var out = a.slice();
    for (var i = out.length - 1; i > 0; i--) {
      var j = Math.floor(rand() * (i + 1));
      var t = out[i]; out[i] = out[j]; out[j] = t;
    }
    return out;
  }
  function interleave(items, rand) {
    rand = rand || Math.random;
    var groups = {}, keys = [];
    items.forEach(function (it) {
      if (!groups[it.fn]) { groups[it.fn] = []; keys.push(it.fn); }
      groups[it.fn].push(it);
    });
    keys.forEach(function (k) { groups[k] = shuffled(groups[k], rand); });

    var out = [], last = null, lastDom = null;
    while (out.length < items.length) {
      var cands = keys.filter(function (k) { return groups[k].length && k !== last; });
      if (!cands.length) cands = keys.filter(function (k) { return groups[k].length; });
      var best = cands[0], bestScore = -1;
      cands.forEach(function (k) {
        var score = groups[k].length * 10 + (groups[k][0].domain !== lastDom ? 3 : 0) + rand();
        if (score > bestScore) { bestScore = score; best = k; }
      });
      var it = groups[best].shift();
      out.push(it);
      last = best;
      lastDom = it.domain;
    }
    return out;
  }

  return { FUNCS: FUNCS, FN_CN: FN_CN, STACKS: STACKS, CN_NAME: CN_NAME,
           computeResult: computeResult, interleave: interleave, shuffled: shuffled };
})();
if (typeof module !== "undefined" && module.exports) module.exports = J8L;
