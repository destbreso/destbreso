/* ================================================================
   destbreso · signal
   An analyst's view of real commit history. Reads a data snapshot
   committed daily by a GitHub Action (see .github/scripts/generate-data.py)
   from the `output` branch. Falls back to an embedded sample so the page
   always renders, even before the first Action run or offline.
   No live GitHub API calls: nothing here can rate-limit or break.
   ================================================================ */

var DATA_URL =
  "https://raw.githubusercontent.com/destbreso/destbreso/output/data.json";

/* ── Embedded sample (mirrors the shape the generator emits) ───────── */
var SAMPLE = {
  generated_at: null,
  sample: true,
  kpis: [
    { label: "commits · 12mo", val: 1240, delta: 12, spark: [18, 22, 17, 26, 24, 30, 21, 14, 28, 33, 29, 37] },
    { label: "active days", val: 214, delta: 8, spark: [12, 15, 14, 18, 17, 19, 16, 11, 20, 22, 21, 24] },
    { label: "longest streak", val: "28d", delta: 0, spark: [9, 12, 8, 14, 11, 16, 10, 7, 15, 19, 17, 21] },
    { label: "public repos", val: 19, delta: 6, spark: [11, 12, 13, 14, 14, 15, 16, 16, 17, 18, 18, 19] }
  ],
  rhythm: (function () {
    // weekday (rows) x hour (cols): the shape the generator emits from real
    // commit timestamps. A night-owl pattern that spills into the weekend.
    var rows = [];
    for (var d = 0; d < 7; d++) {
      var r = [];
      for (var h = 0; h < 24; h++) {
        var night = Math.exp(-Math.pow(h - 22.5, 2) / 9) + Math.exp(-Math.pow(h + 1.5, 2) / 6);
        var noon = 0.4 * Math.exp(-Math.pow(h - 14, 2) / 10);
        var wk = d >= 5 ? 1.15 : 1;
        var base = (night + noon) * wk;
        r.push(Math.max(0, Math.min(1, base * (0.85 + 0.3 * Math.sin(d + h)))));
      }
      rows.push(r);
    }
    return rows;
  })(),
  blocks: [
    { l: "night 21-06", v: 41, pubv: 12, privv: 29 },
    { l: "evening 17-21", v: 24, pubv: 9, privv: 15 },
    { l: "afternoon 12-17", v: 20, pubv: 11, privv: 9 },
    { l: "morning 06-12", v: 15, pubv: 10, privv: 5 }
  ],
  langs: [
    { n: "TypeScript", p: 46 },
    { n: "Python", p: 22 },
    { n: "JavaScript", p: 12 },
    { n: "Rust", p: 8 },
    { n: "Other", p: 12 }
  ],
  momentum: [74, 88, 79, 102, 96, 118, 84, 52, 96, 124, 116, 141],
  momentumPublic: [28, 30, 26, 34, 31, 40, 30, 20, 33, 42, 39, 46],
  momentumLabels: ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun"],
  momentumAnnot: { index: 7, text: "platform ship + debt paydown" },
  insights: {
    rhythm: "Commits cluster <b>Tuesday to Thursday</b> and taper into the weekend. <b>Decision:</b> I guard midweek for hard problems and keep meetings off it.",
    langs: "<b>TypeScript</b> carries the systems, <b>Python</b> carries the math. <b>Decision:</b> new services default to TS for team velocity; anything analytical starts in Python.",
    momentum: "A deliberate dip while shipping a platform and paying down debt, then a steady climb. <b>Decision:</b> I read cadence over volume, consistency beats heroics.",
    proj: "<b>private work</b> takes the biggest share of commits (43%). <b>Decision:</b> I let the busiest project set the week, and shield the rest from it."
  },
  decisions: [
    { obs: "Most net-new code lands in the <b>first hour</b> of a session.", act: "Protect a cold-start block; batch reviews for later." },
    { obs: "Activity is <b>consistent</b> across months, not spiky.", act: "Trust cadence over crunch; ship small and often." },
    { obs: "The stack splits cleanly: <b>systems in TS, math in Python</b>.", act: "Pick the language by the problem, not by habit." }
  ],
  projects: [
    { n: "private work", c: 420, kind: "private" },
    { n: "cortex", c: 128, kind: "public" },
    { n: "load-testing-lab", c: 96, kind: "public" },
    { n: "abakojs", c: 74, kind: "public" },
    { n: "gaia-pulse", c: 61, kind: "public" },
    { n: "other public", c: 150, kind: "other" }
  ],
  thisWeek: { commits: 34, volDelta: 42, devBlock: "night 21-06", devPts: 12 }
};

var LANG_COLORS = ["#4dd4e0", "#5b8def", "#a78bfa", "#3fb6a8", "#7d8aa0"];
var $ = function (s) { return document.querySelector(s); };

function spark(vals, w, h) {
  var min = Math.min.apply(null, vals), max = Math.max.apply(null, vals), rng = max - min || 1;
  var pts = vals.map(function (v, i) { return [(i / (vals.length - 1)) * w, h - 2 - ((v - min) / rng) * (h - 4)]; });
  var d = pts.map(function (p, i) { return (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1); }).join(" ");
  var last = pts[pts.length - 1];
  return '<svg class="spark" width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + " " + h + '">' +
    '<path d="' + d + '" fill="none" stroke="var(--accent)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity=".85"/>' +
    '<circle cx="' + last[0].toFixed(1) + '" cy="' + last[1].toFixed(1) + '" r="2" fill="var(--accent)"/></svg>';
}

function heatColor(v) {
  if (v < 0.08) return "#131a24";
  return "rgba(77,212,224," + (0.15 + v * 0.75).toFixed(3) + ")";
}

function render(D) {
  D = D || SAMPLE;
  // Null-safety only. We never merge real data with the sample: the sample is
  // shown whole (and labeled) when there is no snapshot, and the real snapshot
  // is shown whole when there is one, so nothing on the page is half-invented.
  D.kpis = D.kpis || []; D.rhythm = D.rhythm || []; D.blocks = D.blocks || [];
  D.langs = D.langs || []; D.momentum = D.momentum || []; D.decisions = D.decisions || [];
  D.insights = D.insights || {}; D.projects = D.projects || [];
  var days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  // status line
  var up = $("#updated");
  if (up) up.textContent = D.sample ? "daily snapshot (sample)" : "updated " + (D.generated_at || "").slice(0, 10);
  var yr = $("#year");
  if (yr && D.generated_at) yr.textContent = D.generated_at.slice(0, 4);

  // KPIs
  $("#kpis").innerHTML = D.kpis.map(function (k) {
    var hasD = k.delta != null;
    var cls = k.delta > 0 ? "up" : k.delta < 0 ? "down" : "flat";
    var sym = k.delta > 0 ? "↗" : k.delta < 0 ? "↘" : "→";
    var deltaHtml = !hasD ? "" : (k.delta === 0 ? "steady" : sym + " " + Math.abs(k.delta) + "% YoY");
    return '<div class="kpi">' + spark(k.spark || [], 58, 26) +
      '<div class="label">' + k.label + "</div>" +
      '<div class="val tabnum">' + (typeof k.val === "number" ? k.val.toLocaleString("en-US") : k.val) + "</div>" +
      (hasD ? '<div class="delta ' + cls + '">' + deltaHtml + "</div>" : "") + "</div>";
  }).join("");

  // rhythm heatmap (weekday rows x week cols; column count is data-driven)
  $("#rhythm").innerHTML = D.rhythm.map(function (row, d) {
    return '<div class="ylab">' + days[d] + '</div>' +
      '<div class="hm" style="grid-template-columns:repeat(' + (row.length || 1) + ',1fr)">' +
      row.map(function (v) { return '<i style="background:' + heatColor(v) + '"></i>'; }).join("") + "</div>";
  }).join("");

  // marginal blocks, stacked public + private
  var maxB = Math.max.apply(null, D.blocks.map(function (b) { return b.v; }).concat([1]));
  $("#marg").innerHTML = D.blocks.map(function (b) {
    var pub = b.pubv != null ? b.pubv : b.v, priv = b.privv || 0;
    return '<div class="barrow"><span class="bl">' + b.l + '</span>' +
      '<span class="track"><i class="seg pub" style="width:' + (pub / maxB * 100) + '%"></i>' +
      '<i class="seg priv" style="width:' + (priv / maxB * 100) + '%"></i></span>' +
      '<span class="bv">' + b.v + "%</span></div>";
  }).join("");

  // language stacked bar + legend
  $("#stack").innerHTML = D.langs.map(function (l, i) {
    return '<span style="width:' + l.p + "%;background:" + (LANG_COLORS[i] || "#7d8aa0") + '"></span>';
  }).join("");
  $("#legend").innerHTML = D.langs.map(function (l, i) {
    return '<div class="li"><span class="sw" style="background:' + (LANG_COLORS[i] || "#7d8aa0") + '"></span><span class="lname">' + l.n + '</span><span class="lpct">' + l.p + "%</span></div>";
  }).join("");

  // projects: where the effort goes (public named, private folded into one bar)
  var pj = $("#proj");
  if (pj) {
    var maxC = Math.max.apply(null, D.projects.map(function (p) { return p.c; }).concat([1]));
    pj.innerHTML = D.projects.map(function (p) {
      var cls = p.kind === "private" ? " priv" : p.kind === "other" ? " other" : "";
      return '<div class="projrow' + cls + '"><div class="projtop"><span class="pn">' + p.n +
        '</span><span class="pc tabnum">' + (p.c || 0).toLocaleString("en-US") + '</span></div>' +
        '<span class="track"><i style="width:' + (p.c / maxC * 100) + '%"></i></span></div>';
    }).join("");
  }

  // this week vs the year baseline
  var tw = $("#thisweek");
  if (tw && D.thisWeek) {
    var t = D.thisWeek;
    var ar = t.volDelta > 0 ? "↗" : t.volDelta < 0 ? "↘" : "→";
    var vol = t.volDelta === 0 ? "right on your weekly average"
      : Math.abs(t.volDelta) + "% " + (t.volDelta > 0 ? "above" : "below") + " your weekly average";
    var dev = t.devBlock ? ", leaning <b>" + t.devBlock + "</b> (" + (t.devPts >= 0 ? "+" : "") + t.devPts + " pts vs usual)" : "";
    tw.innerHTML = '<span class="tw-k">this week</span><span class="tw-v"><b>' + t.commits + "</b> commits, " + ar + " " + vol + dev + "</span>";
  } else if (tw) { tw.style.display = "none"; }

  // decisions + insights
  $("#decisions").innerHTML = D.decisions.map(function (d) {
    return '<div class="dec"><div class="obs">' + d.obs + '</div><div class="act"><span class="a">do &rarr;</span><span>' + d.act + "</span></div></div>";
  }).join("");
  var ins = D.insights || {};
  ["rhythm", "langs", "mom", "proj"].forEach(function (key) {
    var el = $("#insight-" + key);
    var txt = ins[key === "mom" ? "momentum" : key];
    if (el && txt) el.innerHTML = '<span class="arrow">→</span><span>' + txt + "</span>";
  });

  // show the public/private key only when there IS private data to distinguish
  var hasPrivate = (D.projects || []).some(function (p) { return p.kind === "private" && p.c > 0; }) ||
    (D.blocks || []).some(function (b) { return (b.privv || 0) > 0; });
  [].forEach.call(document.querySelectorAll(".pp-key"), function (el) { el.style.display = hasPrivate ? "" : "none"; });

  drawMomentum(D);
}

function drawMomentum(D) {
  var cv = $("#mom");
  if (!cv) return;
  var dpr = Math.min(2, window.devicePixelRatio || 1);
  var total = D.momentum || [];
  var pub = (D.momentumPublic && D.momentumPublic.length === total.length) ? D.momentumPublic : total;
  function draw() {
    var w = cv.clientWidth || 880, h = 200;
    cv.width = w * dpr; cv.height = h * dpr;
    var ctx = cv.getContext("2d"); ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, w, h);
    var n = total.length, pad = 28, gx = w - pad * 1.4, gy = h - 26;
    if (!n) return;
    var max = Math.max.apply(null, total) * 1.12 || 1;
    function X(i) { return pad + (i / (n - 1)) * gx; }
    function Y(v) { return 8 + (1 - v / max) * (gy - 8); }
    ctx.strokeStyle = "#18202c"; ctx.lineWidth = 1;
    for (var g = 0; g <= 3; g++) { var yy = 8 + (g / 3) * (gy - 8); ctx.beginPath(); ctx.moveTo(pad, yy); ctx.lineTo(pad + gx, yy); ctx.stroke(); }
    // filled band between two series (traced forward on top, back on bottom)
    function band(low, high, fill) {
      ctx.beginPath(); ctx.moveTo(X(0), Y(high[0]));
      for (var i = 1; i < n; i++) ctx.lineTo(X(i), Y(high[i]));
      for (var j = n - 1; j >= 0; j--) ctx.lineTo(X(j), Y(low[j]));
      ctx.closePath(); ctx.fillStyle = fill; ctx.fill();
    }
    var zero = []; for (var z = 0; z < n; z++) zero.push(0);
    var anyPriv = false; for (var p = 0; p < n; p++) if (total[p] - pub[p] > 0.0001) anyPriv = true;
    band(zero, pub, "rgba(77,212,224,.30)");                 // public
    if (anyPriv) band(pub, total, "rgba(167,139,250,.34)");  // private, stacked on top
    // total outline
    ctx.beginPath(); ctx.moveTo(X(0), Y(total[0]));
    for (var i2 = 1; i2 < n; i2++) ctx.lineTo(X(i2), Y(total[i2]));
    ctx.strokeStyle = "#4dd4e0"; ctx.lineWidth = 2; ctx.lineJoin = "round"; ctx.stroke();
    if (anyPriv) {  // subtle public boundary line so the split reads
      ctx.beginPath(); ctx.moveTo(X(0), Y(pub[0]));
      for (var i3 = 1; i3 < n; i3++) ctx.lineTo(X(i3), Y(pub[i3]));
      ctx.strokeStyle = "rgba(77,212,224,.5)"; ctx.lineWidth = 1; ctx.stroke();
    }
    // least-squares trend on the total
    var sx = 0, sy = 0, sxy = 0, sxx = 0;
    for (var i4 = 0; i4 < n; i4++) { sx += i4; sy += total[i4]; sxy += i4 * total[i4]; sxx += i4 * i4; }
    var b = (n * sxy - sx * sy) / (n * sxx - sx * sx), a = (sy - b * sx) / n;
    ctx.beginPath(); ctx.moveTo(X(0), Y(a)); ctx.lineTo(X(n - 1), Y(a + b * (n - 1)));
    ctx.strokeStyle = "rgba(147,160,178,.7)"; ctx.lineWidth = 1.4; ctx.setLineDash([5, 4]); ctx.stroke(); ctx.setLineDash([]);
    ctx.beginPath(); ctx.arc(X(n - 1), Y(total[n - 1]), 3.2, 0, 7); ctx.fillStyle = "#4dd4e0"; ctx.fill();
    ctx.fillStyle = "#5c6675"; ctx.font = "10px ui-monospace,monospace"; ctx.textAlign = "center";
    (D.momentumLabels || []).forEach(function (l, i) { if (i % 2 === 0) ctx.fillText(l, X(i), h - 8); });
    var an = $("#momAnnot");
    if (an && D.momentumAnnot) {
      var idx = Math.max(0, Math.min(n - 1, D.momentumAnnot.index));
      an.textContent = D.momentumAnnot.text;
      an.style.left = Math.min(X(idx), w - 190) + "px";
      an.style.top = Y(total[idx]) - 34 + "px";
      an.style.display = "";
    } else if (an) { an.style.display = "none"; }
  }
  draw();
  window.addEventListener("resize", draw);
}

// Fetch the real daily snapshot; on any failure, render the labeled sample.
// The two are never mixed, so the page is either all real or clearly sample.
fetch(DATA_URL, { cache: "no-store" })
  .then(function (r) { if (!r.ok) throw new Error("no snapshot"); return r.json(); })
  .then(function (d) { render(d); })
  .catch(function () { render(SAMPLE); });
