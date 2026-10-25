/* 荣格八维计分内核（JS 版，与 tools/score.py 逐值同构） */
var J8 = (function () {
  var FUNCS = ["Se", "Si", "Ne", "Ni", "Te", "Ti", "Fe", "Fi"];
  var ATT = { Se: "E", Si: "I", Ne: "E", Ni: "I", Te: "E", Ti: "I", Fe: "E", Fi: "I" };
  var OPP = { Se: "Si", Si: "Se", Ne: "Ni", Ni: "Ne", Te: "Ti", Ti: "Te", Fe: "Fi", Fi: "Fe" };
  // 第三/劣势：同类（判断↔判断、知觉↔知觉）、功能对立（思维↔情感、感觉↔直觉）、态度相反
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
  var JUDG = { Te: 1, Ti: 1, Fe: 1, Fi: 1 };
  var PERC = { Se: 1, Si: 1, Ne: 1, Ni: 1 };

  function mean(a) { var s = 0; a.forEach(function (x) { s += x; }); return s / a.length; }
  function std(a) {
    var m = mean(a), s = 0;
    a.forEach(function (x) { s += (x - m) * (x - m); });
    return Math.sqrt(s / a.length);
  }
  function rank(xs) {
    var idx = xs.map(function (v, i) { return i; });
    idx.sort(function (a, b) { return xs[a] - xs[b]; });
    var r = new Array(xs.length);
    var i = 0;
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

  function sumS(answers, items) {
    var S = {}; FUNCS.forEach(function (f) { S[f] = 0; });
    items.forEach(function (it) {
      var r = answers[it.id];
      if (r === undefined || r === null) return;
      S[it.options.A.fn] += r;
      S[it.options.B.fn] -= r;
    });
    return S;
  }

  function zOf(S) {
    var vals = FUNCS.map(function (f) { return S[f]; });
    var m = mean(vals), sd = std(vals) || 1, Z = {};
    FUNCS.forEach(function (f) { Z[f] = (S[f] - m) / sd; });
    return Z;
  }

  function computeResult(answers, items) {
    var cnt = {}; FUNCS.forEach(function (f) { cnt[f] = 0; });
    items.forEach(function (it) { cnt[it.options.A.fn]++; cnt[it.options.B.fn]++; });
    var M = 0; FUNCS.forEach(function (f) { if (cnt[f] > M) M = cnt[f]; });
    if (!M) M = 14;

    var S = sumS(answers, items);
    var P = {}, Z = zOf(S);
    FUNCS.forEach(function (f) { P[f] = 50 + 25 * S[f] / M; });

    var order = FUNCS.slice().sort(function (a, b) {
      return (S[b] - S[a]) || (FUNCS.indexOf(a) - FUNCS.indexOf(b));
    });
    var dom = order[0];
    var otherIsPerc = !PERC[dom];
    var cand = FUNCS.filter(function (f) {
      var isPerc = !!PERC[f];
      return (otherIsPerc ? isPerc : !isPerc) && ATT[f] !== ATT[dom];
    }).sort(function (a, b) { return (S[b] - S[a]) || (FUNCS.indexOf(a) - FUNCS.indexOf(b)); });
    var aux = cand[0];
    var tert = MAP[aux], inf = MAP[dom];

    var ei = ATT[dom], sn, tf;
    if (PERC[dom]) {
      sn = (dom === "Ne" || dom === "Ni") ? "N" : "S";
      tf = (aux === "Te" || aux === "Ti") ? "T" : "F";
    } else {
      tf = (dom === "Te" || dom === "Ti") ? "T" : "F";
      sn = (aux === "Ne" || aux === "Ni") ? "N" : "S";
    }
    var extFn = ATT[dom] === "E" ? dom : aux;
    var jp = JUDG[extFn] ? "J" : "P";
    var code = ei + sn + tf + jp;

    var fits = {}, ranked = [];
    Object.keys(STACKS).forEach(function (t) {
      var st = STACKS[t], v = 0;
      for (var i = 0; i < 4; i++) v += W[i] * Z[st[i]];
      fits[t] = Math.round(v * 1000) / 1000;
      ranked.push([t, fits[t]]);
    });
    ranked.sort(function (a, b) { return b[1] - a[1]; });

    var odd = {}, even = {}, n = 0;
    items.forEach(function (it, i) {
      if (answers[it.id] === undefined) return;
      if (i % 2 === 0) odd[it.id] = answers[it.id]; else even[it.id] = answers[it.id];
      n++;
    });
    var Zo = zOf(sumS(odd, items)), Ze = zOf(sumS(even, items));
    var rHalf = Math.round(spearman(FUNCS.map(function (f) { return Zo[f]; }),
                                    FUNCS.map(function (f) { return Ze[f]; })) * 1000) / 1000;
    var gap = Math.round((ranked[0][1] - ranked[1][1]) * 1000) / 1000;
    var conf = (gap >= 0.6 && rHalf >= 0.5) ? "高" : ((gap >= 0.3 && rHalf >= 0.25) ? "中" : "低");

    var outs = {};
    FUNCS.forEach(function (f) { outs[f] = Math.round(P[f] * 10) / 10; });
    var sortedP = FUNCS.slice().sort(function (a, b) { return outs[b] - outs[a]; });

    return {
      answered: n, total: items.length, complete: n === items.length,
      S: S, P: outs, P_order: sortedP, Z: Z,
      dominant: dom, dominant_cn: FN_CN[dom],
      auxiliary: aux, auxiliary_cn: FN_CN[aux],
      tertiary: tert, inferior: inf,
      jung_code: JUNG_OF[dom][0], jung_name: JUNG_OF[dom][1],
      code: code, cn_name: CN_NAME[code], stack: [dom, aux, tert, inf],
      top3: ranked.slice(0, 3), gap: gap, consistency: rHalf,
      confidence: conf, mismatch: ranked[0][0] !== code
    };
  }

  return {
    FUNCS: FUNCS, FN_CN: FN_CN, STACKS: STACKS, CN_NAME: CN_NAME, OPP: OPP,
    computeResult: computeResult, spearman: spearman
  };
})();

if (typeof module !== "undefined" && module.exports) module.exports = J8;
