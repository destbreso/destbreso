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
    { l: "night 21-02", v: 41 },
    { l: "evening 17-21", v: 24 },
    { l: "afternoon 12-17", v: 20 },
    { l: "morning 06-12", v: 15 }
  ],
  langs: [
    { n: "TypeScript", p: 46 },
    { n: "Python", p: 22 },
    { n: "JavaScript", p: 12 },
    { n: "Rust", p: 8 },
    { n: "Other", p: 12 }
  ],
  momentum: [74, 88, 79, 102, 96, 118, 84, 52, 96, 124, 116, 141],
  momentumLabels: ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun"],
  momentumAnnot: { index: 7, text: "platform ship + debt paydown" },
  insights: {
    rhythm: "Deep work clusters <b>21:00 to 01:00</b> and spills into weekends. <b>Decision:</b> I guard the late block for hard problems and keep meetings out of it.",
    langs: "<b>TypeScript</b> carries the systems, <b>Python</b> carries the math. <b>Decision:</b> new services default to TS for team velocity; anything analytical starts in Python.",
    momentum: "A deliberate dip while shipping a platform and paying down debt, then a steady climb. <b>Decision:</b> I read cadence over volume, consistency beats heroics."
  },
  decisions: [
    { obs: "Most net-new code lands in the <b>first hour</b> of a session.", act: "Protect a cold-start block; batch reviews for later." },
    { obs: "Activity is <b>consistent</b> across months, not spiky.", act: "Trust cadence over crunch; ship small and often." },
    { obs: "The stack splits cleanly: <b>systems in TS, math in Python</b>.", act: "Pick the language by the problem, not by habit." }
  ]
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
  D.insights = D.insights || {};
  var days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  // status line
  var up = $("#updated");
  if (up) up.textContent = D.sample ? "daily snapshot (sample)" : "updated " + (D.generated_at || "").slice(0, 10);
  var yr = $("#year");
  if (yr && D.generated_at) yr.textContent = D.generated_at.slice(0, 4);

  // KPIs
  $("#kpis").innerHTML = D.kpis.map(function (k) {
    var cls = k.delta > 0 ? "up" : k.delta < 0 ? "down" : "flat";
    var sym = k.delta > 0 ? "↗" : k.delta < 0 ? "↘" : "→";
    var deltaHtml = k.delta === 0 ? "steady" : sym + " " + Math.abs(k.delta) + "% YoY";
    return '<div class="kpi">' + spark(k.spark || [], 58, 26) +
      '<div class="label">' + k.label + "</div>" +
      '<div class="val tabnum">' + (typeof k.val === "number" ? k.val.toLocaleString("en-US") : k.val) + "</div>" +
      '<div class="delta ' + cls + '">' + deltaHtml + "</div></div>";
  }).join("");

  // rhythm heatmap
  $("#rhythm").innerHTML = D.rhythm.map(function (row, d) {
    return '<div class="ylab">' + days[d] + '</div><div class="hm">' +
      row.map(function (v) { return '<i style="background:' + heatColor(v) + '"></i>'; }).join("") + "</div>";
  }).join("");

  // marginal blocks
  var maxB = Math.max.apply(null, D.blocks.map(function (b) { return b.v; }));
  $("#marg").innerHTML = D.blocks.map(function (b) {
    return '<div class="barrow"><span class="bl">' + b.l + '</span><span class="track"><i style="width:' + (b.v / maxB * 100) + '%"></i></span><span class="bv">' + b.v + "%</span></div>";
  }).join("");

  // language stacked bar + legend
  $("#stack").innerHTML = D.langs.map(function (l, i) {
    return '<span style="width:' + l.p + "%;background:" + (LANG_COLORS[i] || "#7d8aa0") + '"></span>';
  }).join("");
  $("#legend").innerHTML = D.langs.map(function (l, i) {
    return '<div class="li"><span class="sw" style="background:' + (LANG_COLORS[i] || "#7d8aa0") + '"></span><span class="lname">' + l.n + '</span><span class="lpct">' + l.p + "%</span></div>";
  }).join("");

  // decisions + insights
  $("#decisions").innerHTML = D.decisions.map(function (d) {
    return '<div class="dec"><div class="obs">' + d.obs + '</div><div class="act"><span class="a">do &rarr;</span><span>' + d.act + "</span></div></div>";
  }).join("");
  var ins = D.insights || {};
  ["rhythm", "langs", "mom"].forEach(function (key) {
    var el = $("#insight-" + key);
    var txt = ins[key === "mom" ? "momentum" : key];
    if (el && txt) el.innerHTML = '<span class="arrow">→</span><span>' + txt + "</span>";
  });

  drawMomentum(D);
}

function drawMomentum(D) {
  var cv = $("#mom");
  if (!cv) return;
  var dpr = Math.min(2, window.devicePixelRatio || 1);
  function draw() {
    var w = cv.clientWidth || 880, h = 200;
    cv.width = w * dpr; cv.height = h * dpr;
    var ctx = cv.getContext("2d"); ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, w, h);
    var vals = D.momentum, n = vals.length, pad = 28, gx = w - pad * 1.4, gy = h - 26;
    var max = Math.max.apply(null, vals) * 1.12 || 1, min = 0;
    function X(i) { return pad + (i / (n - 1)) * gx; }
    function Y(v) { return 8 + (1 - (v - min) / (max - min)) * (gy - 8); }
    ctx.strokeStyle = "#18202c"; ctx.lineWidth = 1;
    for (var g = 0; g <= 3; g++) { var yy = 8 + (g / 3) * (gy - 8); ctx.beginPath(); ctx.moveTo(pad, yy); ctx.lineTo(pad + gx, yy); ctx.stroke(); }
    var grad = ctx.createLinearGradient(0, 0, 0, gy);
    grad.addColorStop(0, "rgba(77,212,224,.28)"); grad.addColorStop(1, "rgba(77,212,224,0)");
    ctx.beginPath(); ctx.moveTo(X(0), Y(vals[0]));
    for (var i = 1; i < n; i++) ctx.lineTo(X(i), Y(vals[i]));
    ctx.lineTo(X(n - 1), gy); ctx.lineTo(X(0), gy); ctx.closePath(); ctx.fillStyle = grad; ctx.fill();
    ctx.beginPath(); ctx.moveTo(X(0), Y(vals[0]));
    for (var i = 1; i < n; i++) ctx.lineTo(X(i), Y(vals[i]));
    ctx.strokeStyle = "#4dd4e0"; ctx.lineWidth = 2; ctx.lineJoin = "round"; ctx.stroke();
    // least-squares trend
    var sx = 0, sy = 0, sxy = 0, sxx = 0;
    for (var i = 0; i < n; i++) { sx += i; sy += vals[i]; sxy += i * vals[i]; sxx += i * i; }
    var b = (n * sxy - sx * sy) / (n * sxx - sx * sx), a = (sy - b * sx) / n;
    ctx.beginPath(); ctx.moveTo(X(0), Y(a)); ctx.lineTo(X(n - 1), Y(a + b * (n - 1)));
    ctx.strokeStyle = "rgba(167,139,250,.8)"; ctx.lineWidth = 1.4; ctx.setLineDash([5, 4]); ctx.stroke(); ctx.setLineDash([]);
    ctx.beginPath(); ctx.arc(X(n - 1), Y(vals[n - 1]), 3.2, 0, 7); ctx.fillStyle = "#4dd4e0"; ctx.fill();
    ctx.fillStyle = "#5c6675"; ctx.font = "10px ui-monospace,monospace"; ctx.textAlign = "center";
    (D.momentumLabels || []).forEach(function (l, i) { if (i % 2 === 0) ctx.fillText(l, X(i), h - 8); });
    // annotation
    var an = $("#momAnnot");
    if (an && D.momentumAnnot) {
      var idx = Math.max(0, Math.min(n - 1, D.momentumAnnot.index));
      an.textContent = D.momentumAnnot.text;
      an.style.left = Math.min(X(idx), w - 190) + "px";
      an.style.top = Y(vals[idx]) - 34 + "px";
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
