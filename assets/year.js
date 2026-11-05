/* ================================================================
   The year in pixels, on the page: the README's figure (year.svg,
   .github/scripts/generate-year.py) drawn on a canvas with the same
   geometry and the same blueprint robot (assets/robot.json), here
   to play with. Point at a week to read it, click one to send the
   robot there, click the robot, or move it with the arrow keys.
   With reduced motion it steps instead of walking, and never blinks.
   ================================================================ */
(function () {
  "use strict";
  var SERIES_URL = "https://raw.githubusercontent.com/destbreso/destbreso/output/series.json";
  // the README figure's geometry, in pixels of the art
  var PITCH = 4, BAR = 3, HMAX = 34, LEFT = 6, TOP = 26;
  var W = LEFT * 2 + 52 * PITCH - 1, GROUND = TOP + HMAX, H = GROUND + 6;
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var INK = { bg: "#0b0e14", grid: "#141c28", ground: "#263243", pub: "#4dd4e0", priv: "#a78bfa", line: "#4dd4e0", face: "#0b0e14", eye: "#c9f7fb", cap: "rgba(255,255,255,.28)", hover: "rgba(201,247,251,.16)" };

  var box = document.getElementById("yearfig");
  var read = document.getElementById("year-read");
  var walkBtn = document.getElementById("year-walk");
  if (!box) return;
  var still = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var canvas = document.createElement("canvas");
  canvas.setAttribute("aria-hidden", "true");
  box.appendChild(canvas);
  var ctx = canvas.getContext("2d");
  var scale = 4;

  var S = null, R = null; // the series and the robot's pixels
  var heights = [], pubH = [], weeks = [];
  var bot = { x: 0, y: 0, week: 51, eyes: "front", legs: "a", hop: 0, path: [], t: 0, happyUntil: 0, blinkAt: 0, blinkUntil: 0, look: null };
  var hover = -1, frame = 0, timer = 0, last = 0, lastAct = 0;
  // what moves by itself (the cursor, the antenna, the blinks) moves only for a few seconds after the visitor does
  // something, then holds still (WCAG 2.2.2); a walk or a hop runs to its end
  function ambient(now) { return !still && now - lastAct < 6000; }
  function touch() { lastAct = performance.now(); kick(); }

  function weekLabel(i) {
    var d = weeks[i];
    if (!d) return "Week " + (i + 1);
    return "Week of " + MONTHS[d.getUTCMonth()] + " " + d.getUTCDate() + (i === 51 ? " (this week, so far)" : "");
  }
  function describe(i) {
    var c = S.weekly[i], p = S.weeklyPublic ? S.weeklyPublic[i] : null;
    var n = c === 1 ? "1 commit" : c.toLocaleString("en-US") + " commits";
    if (!c) return weekLabel(i) + ": no commits";
    return weekLabel(i) + ": " + n + (p == null ? "" : ", " + p + " public and " + (c - p) + " private");
  }
  function setRead(i) {
    var text = describe(i);
    if (read) read.textContent = text;
    box.setAttribute("aria-valuenow", String(i + 1));
    box.setAttribute("aria-valuetext", text);
  }

  // the robot stands on the highest of the three columns under its body, as in the README
  function groundAt(i) { return Math.max(heights[Math.max(0, i - 1)] || 0, heights[i] || 0, heights[Math.min(51, i + 1)] || 0); }
  function spot(i) { return { x: LEFT + i * PITCH + 1 - R.w / 2 + 1, y: GROUND - groundAt(i) - R.h }; }

  function walkTo(target, opts) {
    target = Math.max(0, Math.min(51, target));
    var from = bot.week, steps = [], dir = target > from ? 1 : -1;
    for (var i = from; i !== target; i += dir) steps.push(i + dir);
    bot.week = target;
    setRead(target);
    if (still || !steps.length) {
      var s = spot(target); bot.x = s.x; bot.y = s.y; bot.path = []; bot.eyes = "front";
      return kick();
    }
    var per = (opts && opts.per) || 0.11, t = 0, prev = spot(from);
    bot.path = [];
    steps.forEach(function (w) {
      var a = prev, b = spot(w), arc = 2 + Math.max(0, a.y - b.y) / 3;
      for (var k = 1; k <= 4; k++) {
        var f = k / 4;
        bot.path.push({ at: t + per * f, x: Math.round(a.x + (b.x - a.x) * f), y: Math.round(a.y + (b.y - a.y) * f - arc * Math.sin(Math.PI * f)), legs: k % 2 ? "b" : "a", pause: opts && opts.pauseAt === w ? 1.6 : 0 });
      }
      t += per + (opts && opts.pauseAt === w ? 1.6 : 0);
      prev = b;
    });
    bot.eyes = dir > 0 ? "right" : "left";
    bot.t = 0;
    kick();
  }

  function draw(now, live) {
    var s = scale;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = INK.bg; ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.setTransform(s, 0, 0, s, 0, 0);
    ctx.fillStyle = INK.grid;
    for (var gx = 0; gx < W; gx += 8) ctx.fillRect(gx, 0, 1 / s, H);
    for (var gy = 0; gy < H; gy += 8) ctx.fillRect(0, gy, W, 1 / s);
    ctx.fillStyle = INK.ground; ctx.fillRect(LEFT - 2, GROUND, 52 * PITCH + 3, 1);
    for (var t = 0; t < 52; t++) {
      var a = weeks[t], b = a && new Date(a.getTime() + 6 * 864e5);
      if (a && (a.getUTCMonth() !== b.getUTCMonth() || a.getUTCDate() === 1)) ctx.fillRect(LEFT + t * PITCH + 1, GROUND + 2, 1, 2);
    }
    if (hover >= 0) { ctx.fillStyle = INK.hover; ctx.fillRect(LEFT + hover * PITCH - 1, 0, BAR + 2, GROUND); }
    for (var i = 0; i < 52; i++) {
      var h = heights[i]; if (!h) continue;
      var x = LEFT + i * PITCH, ph = pubH[i];
      ctx.fillStyle = INK.pub; ctx.fillRect(x, GROUND - ph, BAR, ph);
      ctx.fillStyle = INK.priv; ctx.fillRect(x, GROUND - h, BAR, h - ph);
      ctx.fillStyle = INK.cap; ctx.fillRect(x, GROUND - h, BAR, 1);
    }
    // this week is still being written: its top pixel blinks (held lit with reduced motion)
    if (!live || Math.floor(now / 500) % 2 === 0) { ctx.fillStyle = INK.line; ctx.fillRect(LEFT + 51 * PITCH, GROUND - heights[51] - 2, BAR, 1); }
    // the robot
    var bx = bot.x, by = bot.y - bot.hop;
    var eyes = now < bot.blinkUntil ? "closed" : now < bot.happyUntil ? "happy" : bot.eyes;
    sprite(R.head, bx, by, { O: INK.line, F: INK.face, A: INK.eye }, !live || Math.floor(now / 750) % 2 === 0 ? null : "A");
    sprite(R.eyes[eyes] || R.eyes.front, bx, by, { E: INK.eye });
    sprite(R.legs[bot.legs], bx, by + 11, { O: INK.line });
  }

  function sprite(rows, ox, oy, inks, skip) {
    for (var y = 0; y < rows.length; y++)
      for (var x = 0; x < rows[y].length; x++) {
        var c = rows[y][x];
        if (c === "." || c === skip || !inks[c]) continue;
        ctx.fillStyle = inks[c]; ctx.fillRect(ox + x, oy + y, 1, 1);
      }
  }

  function tick(now) {
    frame = 0;
    var dt = last ? Math.min(0.1, (now - last) / 1000) : 0;
    last = now;
    var busy = false;
    if (bot.path.length) {
      bot.t += dt;
      while (bot.path.length && bot.path[0].at <= bot.t) {
        var p = bot.path.shift();
        bot.x = p.x; bot.y = p.y; bot.legs = p.legs;
        if (p.pause) bot.eyes = "up";
      }
      if (!bot.path.length) { bot.legs = "a"; bot.eyes = "front"; }
      else if (bot.eyes === "up" && bot.path[0].at - bot.t < 0.2) bot.eyes = bot.path[0].x >= bot.x ? "right" : "left";
      busy = true;
    }
    if (bot.hop > 0) { bot.hop = Math.max(0, bot.hop - dt * 14); busy = true; }
    var live = ambient(now) || busy;
    if (live && !still) {
      if (!bot.blinkAt) bot.blinkAt = now + 1500 + Math.random() * 2500;
      if (now >= bot.blinkAt) { bot.blinkUntil = now + 140; bot.blinkAt = now + 3000 + Math.random() * 4000; }
    }
    draw(now, live);
    // every frame while it walks or hops; ten a second while it idles; none once it holds still
    if (busy) frame = requestAnimationFrame(tick);
    else if (live) timer = setTimeout(function () { timer = 0; frame = requestAnimationFrame(tick); }, 100);
  }
  function kick() {
    if (timer) { clearTimeout(timer); timer = 0; }
    if (!frame) { last = 0; frame = requestAnimationFrame(tick); }
  }

  // drawn at a whole number of device pixels a pixel of the art, shown at the card's full width (pixelated, so it stays crisp)
  function fit() {
    var dpr = window.devicePixelRatio || 1;
    scale = Math.max(1, Math.ceil((Math.max(200, box.clientWidth) * dpr) / W));
    canvas.width = W * scale; canvas.height = H * scale;
    canvas.style.width = "100%";
    canvas.style.height = "auto";
    if (S) draw(performance.now(), false);
  }

  function weekAt(ev) {
    var r = canvas.getBoundingClientRect();
    var ux = (ev.clientX - r.left) / r.width * W, uy = (ev.clientY - r.top) / r.height * H;
    return { week: Math.max(0, Math.min(51, Math.floor((ux - LEFT + 0.5) / PITCH))), ux: ux, uy: uy };
  }
  function onBot(p) { return p.ux >= bot.x && p.ux <= bot.x + R.w && p.uy >= bot.y && p.uy <= bot.y + R.h; }

  function start(series, robot) {
    S = series; R = robot;
    var weekly = S.weekly.slice(-52), peak = Math.max.apply(null, weekly) || 1, per = peak / HMAX;
    S.weekly = weekly;
    if (S.weeklyPublic) S.weeklyPublic = S.weeklyPublic.slice(-52);
    heights = weekly.map(function (c) { return c ? Math.max(1, Math.round(c / per)) : 0; });
    // without the public share (a snapshot older than it) every column is drawn in one tone
    pubH = weekly.map(function (c, i) {
      if (!S.weeklyPublic) return heights[i];
      return c ? Math.min(heights[i], Math.round(S.weeklyPublic[i] / per)) : 0;
    });
    var first = S.weekStart ? new Date(S.weekStart + "T00:00:00Z") : null;
    if (!first) { var n = new Date(); first = new Date(Date.UTC(n.getUTCFullYear(), n.getUTCMonth(), n.getUTCDate() - ((n.getUTCDay() + 6) % 7) - 51 * 7)); }
    for (var i = 0; i < 52; i++) weeks.push(new Date(first.getTime() + i * 7 * 864e5));
    var s0 = spot(51); bot.x = s0.x; bot.y = s0.y;
    box.hidden = false;
    if (walkBtn) walkBtn.hidden = false;
    setRead(51);
    fit();
    touch();

    canvas.addEventListener("pointermove", function (ev) {
      var p = weekAt(ev);
      if (p.week !== hover) { hover = p.week; setRead(hover); }
      // its eyes follow the pointer when it stands still
      if (!bot.path.length) bot.eyes = p.ux < bot.x - 2 ? "left" : p.ux > bot.x + R.w + 2 ? "right" : p.uy < bot.y ? "up" : "front";
      touch();
    });
    canvas.addEventListener("pointerleave", function () { hover = -1; setRead(bot.week); if (!bot.path.length) bot.eyes = "front"; touch(); });
    canvas.addEventListener("click", function (ev) {
      var p = weekAt(ev);
      touch();
      if (onBot(p)) { bot.hop = still ? 0 : 4; bot.happyUntil = performance.now() + 1100; return kick(); }
      walkTo(p.week);
    });
    box.addEventListener("keydown", function (ev) {
      var k = ev.key, to = null;
      if (k === "ArrowRight") to = bot.week + 1;
      else if (k === "ArrowLeft") to = bot.week - 1;
      else if (k === "PageUp") to = bot.week - 4;
      else if (k === "PageDown") to = bot.week + 4;
      else if (k === "Home") to = 0;
      else if (k === "End") to = 51;
      if (to === null) return;
      ev.preventDefault();
      touch();
      walkTo(to, { per: 0.07 });
    });
    if (walkBtn) walkBtn.addEventListener("click", function () {
      // the README's walk: from the oldest week to this one, a look up at the busiest on the way
      var busiest = 0;
      for (var i = 1; i < 52; i++) if (weekly[i] > weekly[busiest]) busiest = i;
      var s = spot(0); bot.x = s.x; bot.y = s.y; bot.week = 0; bot.path = [];
      touch();
      walkTo(51, { per: 0.34, pauseAt: busiest });
    });
    window.addEventListener("resize", fit);
  }

  Promise.all([
    fetch(SERIES_URL, { cache: "no-store" }).then(function (r) { if (!r.ok) throw new Error("no series"); return r.json(); }),
    fetch("assets/robot.json").then(function (r) { return r.json(); })
  ]).then(function (v) {
    if (!v[0] || !v[0].weekly || v[0].weekly.length < 52) throw new Error("short series");
    start(v[0], v[1]);
  }).catch(function () {
    var sec = document.getElementById("year-section");
    if (sec) sec.hidden = true;
  });
})();
