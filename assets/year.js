/* ================================================================
   The year as threads, on the page: the README's figure (year.svg,
   .github/scripts/generate-year.py) drawn with the same geometry from
   series.json, here to read. Point at a thread to read the project,
   and at a week to read that week; the arrow keys move between
   threads (up and down) and weeks (left and right).
   ================================================================ */
(function () {
  "use strict";
  var SERIES_URL = "https://raw.githubusercontent.com/destbreso/destbreso/output/series.json";
  // the generator's geometry: change one, change both
  var W = 1200, LEFT = 200, RIGHT = 24, TOP = 24, ROW = 16, BOTTOM = 34, HMAX = 6.8, K = 1.6;
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var INK = { grid: "#141b26", pub: "#4dd4e0", priv: "#a78bfa", small: "#5c6675", label: "#c9d1d9", plabel: "#a78bfa", dim: "#5c6675", now: "#4dd4e0", hover: "rgba(201,247,251,.06)" };
  var NS = "http://www.w3.org/2000/svg";
  var MONO = "ui-monospace,SFMono-Regular,Menlo,monospace";

  var box = document.getElementById("yearfig");
  var read = document.getElementById("year-read");
  if (!box) return;

  var rows = [], weeks = [], step = (W - LEFT - RIGHT) / 51, H = 0;
  var at = { row: 0, week: 51 };
  var svg, hoverRow, hoverCol, threadEls = [];

  function el(name, attrs, parent) {
    var e = document.createElementNS(NS, name);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function smooth(pts) {
    var d = "M" + pts[0][0].toFixed(1) + " " + pts[0][1].toFixed(1);
    for (var i = 0; i < pts.length - 1; i++) {
      var p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
      d += "C" + [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6, p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6, p2[0], p2[1]].map(function (v) { return v.toFixed(1); }).join(" ");
    }
    return d;
  }
  function half(c) { return c ? Math.min(HMAX, K * Math.sqrt(c)) : 0; }
  function commits(n) { return n === 1 ? "1 commit" : n.toLocaleString("en-US") + " commits"; }
  function weekLabel(i) {
    var d = weeks[i];
    return "the week of " + MONTHS[d.getUTCMonth()] + " " + d.getUTCDate() + (i === 51 ? " (this one, so far)" : "");
  }
  function describe() {
    var r = rows[at.row];
    if (!r) return "";
    var total = r.w.reduce(function (a, b) { return a + b; }, 0);
    var active = r.w.filter(function (c) { return c; }).length;
    var who = r.name || "private work";
    var c = r.w[at.week];
    return who + ": " + commits(total) + " in " + active + (active === 1 ? " week" : " weeks") + "; " + weekLabel(at.week) + ", " + (c ? commits(c) : "none");
  }
  function show() {
    var text = describe();
    if (read) read.textContent = text;
    var y = TOP + at.row * ROW;
    hoverRow.setAttribute("y", y);
    hoverCol.setAttribute("x", (LEFT + at.week * step - step / 2).toFixed(1));
    threadEls.forEach(function (g, i) { g.setAttribute("opacity", i === at.row ? "1" : ".55"); });
  }
  function rest() {
    threadEls.forEach(function (g) { g.setAttribute("opacity", "1"); });
    hoverRow.setAttribute("y", -100);
    hoverCol.setAttribute("x", -100);
  }

  function draw() {
    H = TOP + ROW * rows.length + BOTTOM;
    svg = el("svg", { viewBox: "0 0 " + W + " " + H, width: "100%", "aria-hidden": "true" });
    var first = weeks[0];
    for (var k = 0; k < 52; k++) {
      var a = weeks[k], b = new Date(a.getTime() + 6 * 864e5);
      if (k === 0 || a.getUTCMonth() !== b.getUTCMonth() || a.getUTCDate() === 1) {
        var m = a.getUTCMonth() !== b.getUTCMonth() ? b : a, x = LEFT + k * step;
        el("path", { d: "M" + x.toFixed(1) + " " + (TOP - 8) + "V" + (H - BOTTOM + 8), stroke: INK.grid }, svg);
        el("text", { x: (x + 4).toFixed(1), y: H - 12, fill: INK.dim, "font-size": 12, "font-family": MONO }, svg).textContent = MONTHS[m.getUTCMonth()];
      }
    }
    el("rect", { x: (LEFT + 51 * step - step / 2).toFixed(1), y: TOP - 8, width: step.toFixed(1), height: H - TOP - BOTTOM + 16, fill: INK.now, "fill-opacity": ".08" }, svg);
    hoverCol = el("rect", { x: -100, y: TOP - 8, width: step.toFixed(1), height: H - TOP - BOTTOM + 16, fill: INK.hover }, svg);
    hoverRow = el("rect", { x: 0, y: -100, width: W, height: ROW, fill: INK.hover }, svg);
    rows.forEach(function (r, i) {
      var y = TOP + i * ROW + ROW / 2, w = r.w, f = -1, l = -1;
      for (var k = 0; k < 52; k++) if (w[k]) { if (f < 0) f = k; l = k; }
      var col = INK[r.kind], x0 = LEFT + f * step, x1 = LEFT + l * step;
      var g = el("g", {}, svg);
      threadEls.push(g);
      el("path", { d: "M" + x0.toFixed(1) + " " + y + "H" + x1.toFixed(1), stroke: col, "stroke-opacity": ".45" }, g);
      if (l > f) {
        var top = [[x0 - step * 0.6, y]];
        for (var k2 = f; k2 <= l; k2++) top.push([LEFT + k2 * step, y - half(w[k2])]);
        top.push([Math.min(W - RIGHT, x1 + step * 0.6), y]);
        var bot = top.map(function (p) { return [p[0], 2 * y - p[1]]; }).reverse();
        el("path", { d: smooth(top) + "L" + smooth(bot).slice(1) + "Z", fill: col }, g);
      } else {
        el("circle", { cx: x0.toFixed(1), cy: y, r: Math.max(1.8, half(w[f])).toFixed(1), fill: col }, g);
      }
      if (r.name) {
        var lc = r.kind === "pub" ? INK.label : r.kind === "priv" ? INK.plabel : INK.dim;
        el("text", { x: (x0 - step * 0.6 - 5).toFixed(1), y: (y + 4.4).toFixed(1), "text-anchor": "end", fill: lc, "font-size": 13, "font-family": MONO }, g).textContent = r.name;
      }
    });
    box.appendChild(svg);
  }

  function pointAt(ev) {
    var r = svg.getBoundingClientRect();
    var ux = (ev.clientX - r.left) / r.width * W, uy = (ev.clientY - r.top) / r.height * H;
    at.week = Math.max(0, Math.min(51, Math.round((ux - LEFT) / step)));
    at.row = Math.max(0, Math.min(rows.length - 1, Math.floor((uy - TOP) / ROW)));
    show();
  }

  function start(S) {
    rows = S.threads.map(function (t) { return { name: t.n, kind: t.private ? "priv" : "pub", w: t.w.slice(-52) }; });
    if (S.small && S.small.count) rows.push({ name: S.small.count + (S.small.count === 1 ? " small one" : " small ones"), kind: "small", w: S.small.w.slice(-52) });
    rows = rows.filter(function (r) { return r.w.some(function (c) { return c; }); });
    var first = new Date(S.weekStart + "T00:00:00Z");
    for (var i = 0; i < 52; i++) weeks.push(new Date(first.getTime() + i * 7 * 864e5));
    draw();
    box.hidden = false;
    if (read) read.textContent = "Point at a thread to read it.";
    svg.addEventListener("pointermove", pointAt);
    svg.addEventListener("pointerleave", function () { rest(); if (read) read.textContent = "Point at a thread to read it."; });
    box.addEventListener("focus", show);
    box.addEventListener("blur", rest);
    box.addEventListener("keydown", function (ev) {
      var k = ev.key;
      if (k === "ArrowUp") at.row = Math.max(0, at.row - 1);
      else if (k === "ArrowDown") at.row = Math.min(rows.length - 1, at.row + 1);
      else if (k === "ArrowLeft") at.week = Math.max(0, at.week - 1);
      else if (k === "ArrowRight") at.week = Math.min(51, at.week + 1);
      else if (k === "Home") at.week = 0;
      else if (k === "End") at.week = 51;
      else return;
      ev.preventDefault();
      show();
    });
  }

  fetch(SERIES_URL, { cache: "no-store" })
    .then(function (r) { if (!r.ok) throw new Error("no series"); return r.json(); })
    .then(function (S) {
      if (!S || !S.threads || !S.threads.length || !S.weekStart) throw new Error("no threads");
      start(S);
    })
    .catch(function () {
      var sec = document.getElementById("year-section");
      if (sec) sec.hidden = true;
    });
})();
