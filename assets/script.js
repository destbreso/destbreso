/* ================================================================
   destbreso — GitHub Dashboard Scripts
   Matrix Rain · Charts · Live API data · Scroll animations
   ================================================================ */
(function () {
  "use strict";

  const GH_USER = "destbreso";
  const AC = "34,211,238";

  // ── State ──────────────────────────────────────────────────
  let ghUser = null;
  let ghRepos = [];
  let ghEvents = [];
  let commits = [];

  document.addEventListener("DOMContentLoaded", () => {
    if (window.lucide) lucide.createIcons();
    initMatrixRain();
    initTerminal();
    initNav();
    initScrollAnimations();
    initCascadeDividers();
    fetchGitHubData();
  });

  // ════════════════════════════════════════════════════════════
  // 1. MATRIX RAIN CANVAS (interactive)
  // ════════════════════════════════════════════════════════════
  function initMatrixRain() {
    const c = document.getElementById("matrix-canvas");
    if (!c) return;
    const ctx = c.getContext("2d");
    const chars =
      "アイウエオカキクケコサシスセソタチツテトナニヌネノ" +
      "ハヒフヘホマミムメモヤユヨラリルレロワヲン" +
      "0123456789ABCDEF{}[]|:;=+-*#$%?!";
    const fs = 14;
    let w, h, cols, drops;
    let mx = -9999,
      my = -9999;

    // Full-page: size to viewport
    function resize() {
      w = c.width = window.innerWidth;
      h = c.height = window.innerHeight;
      cols = Math.floor(w / fs) + 1;
      drops = Array.from({ length: cols }, () => Math.random() * (h / fs) * -1);
    }

    function frame() {
      // Faster fade → more subtle trails
      ctx.fillStyle = "rgba(10,10,15,0.12)";
      ctx.fillRect(0, 0, w, h);
      ctx.font = fs + "px monospace";

      for (let i = 0; i < cols; i++) {
        // Only render ~40% of columns each frame for sparsity
        if (Math.random() > 0.4) {
          drops[i] += 0.25 + Math.random() * 0.25;
          continue;
        }

        const x = i * fs;
        const y = drops[i] * fs;
        const ch = chars[Math.floor(Math.random() * chars.length)];

        const dx = x - mx,
          dy = y - my;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 150) {
          // Mouse proximity: brighter cyan glow
          ctx.shadowColor = "#22d3ee";
          ctx.shadowBlur = 12;
          ctx.fillStyle = "rgba(34,211,238,0.7)";
        } else {
          ctx.shadowBlur = 0;
          // Subtle muted green — visible but not distracting
          ctx.fillStyle =
            Math.random() > 0.985
              ? "rgba(255,255,255,0.22)"
              : "rgba(0,255,65,0.12)";
        }

        ctx.fillText(ch, x, y);
        ctx.shadowBlur = 0;

        if (y > h && Math.random() > 0.98) drops[i] = 0;
        drops[i] += 0.25 + Math.random() * 0.25;
      }
      requestAnimationFrame(frame);
    }

    resize();
    ctx.fillStyle = "#0a0a0f";
    ctx.fillRect(0, 0, w, h);
    frame();

    window.addEventListener("resize", () => {
      resize();
      ctx.fillStyle = "#0a0a0f";
      ctx.fillRect(0, 0, w, h);
    });

    // Mouse interaction on full page (canvas has pointer-events:none)
    document.addEventListener("mousemove", (e) => {
      mx = e.clientX;
      my = e.clientY;
    });
  }

  // ════════════════════════════════════════════════════════════
  // 2. TERMINAL TYPING
  // ════════════════════════════════════════════════════════════
  function initTerminal() {
    const cmdEl = document.getElementById("typed-cmd");
    const outEl = document.getElementById("terminal-output");
    if (!cmdEl || !outEl) return;

    const cmd = "gh dashboard @destbreso --live";
    let i = 0;

    function type() {
      if (i < cmd.length) {
        cmdEl.textContent += cmd[i++];
        setTimeout(type, 45 + Math.random() * 30);
      } else {
        setTimeout(() => {
          const cur = document.querySelector(".cursor");
          if (cur) cur.style.display = "none";
          outEl.innerHTML =
            '<p class="t-line"><span class="t-ok">▸</span> Connecting to GitHub API...</p>' +
            '<p class="t-line"><span class="t-ok">▸</span> Rendering live dashboard</p>' +
            '<p class="t-line"><span class="t-ok">✓</span> <span class="t-accent">Dashboard ready</span></p>';
          outEl.style.opacity = "0";
          outEl.style.transition = "opacity .4s ease";
          requestAnimationFrame(() => (outEl.style.opacity = "1"));
        }, 300);
      }
    }
    setTimeout(type, 800);
  }

  // ════════════════════════════════════════════════════════════
  // 3. NAV + SCROLL ANIMATIONS
  // ════════════════════════════════════════════════════════════
  function initNav() {
    const nav = document.getElementById("navbar");
    window.addEventListener("scroll", () => {
      nav.classList.toggle("scrolled", window.scrollY > 20);
    });
  }

  function initScrollAnimations() {
    const els = document.querySelectorAll("[data-animate]");
    if (!els.length) return;
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            const delay = parseInt(e.target.dataset.delay || "0", 10);
            setTimeout(() => e.target.classList.add("visible"), delay);
            obs.unobserve(e.target);
          }
        });
      },
      { threshold: 0.1 },
    );
    els.forEach((el) => obs.observe(el));
  }

  // ════════════════════════════════════════════════════════════
  // 3b. CASCADE SECTION DIVIDERS
  // ════════════════════════════════════════════════════════════
  function initCascadeDividers() {
    const targets = document.querySelectorAll(
      '#distribution, #analytics, #patterns, #repos, #insights, footer'
    );
    const chars = 'アイウエオカキクケコサシスセソタチツテトナニヌネノ0123456789ABCDEF{}[]';
    const colors = [
      'rgba(34,211,238,0.55)',
      'rgba(34,211,238,0.35)',
      'rgba(0,255,65,0.3)',
      'rgba(34,211,238,0.45)',
      'rgba(167,139,250,0.3)',
    ];

    targets.forEach((section) => {
      const wrap = document.createElement('div');
      wrap.className = 'cascade-wrap';
      section.prepend(wrap);

      function spawnDrop() {
        if (document.hidden) return;
        const span = document.createElement('span');
        span.className = 'cascade-char';
        span.textContent = chars[Math.floor(Math.random() * chars.length)];
        span.style.left = (3 + Math.random() * 94) + '%';
        span.style.color = colors[Math.floor(Math.random() * colors.length)];
        const dur = 1.0 + Math.random() * 1.8;
        span.style.animationDuration = dur + 's';
        wrap.appendChild(span);
        setTimeout(() => span.remove(), dur * 1000 + 50);
      }

      // Spawn at staggered intervals — ~5 drops/sec per section
      setInterval(spawnDrop, 180 + Math.random() * 80);
    });
  }

  // ════════════════════════════════════════════════════════════
  // 4. GITHUB API
  // ════════════════════════════════════════════════════════════
  async function fetchGitHubData() {
    try {
      const [userData, reposData] = await Promise.all([
        fetch("https://api.github.com/users/" + GH_USER).then((r) =>
          r.ok ? r.json() : null,
        ),
        fetch(
          "https://api.github.com/users/" +
            GH_USER +
            "/repos?per_page=100&sort=pushed",
        ).then((r) => (r.ok ? r.json() : [])),
      ]);

      ghUser = userData;
      ghRepos = Array.isArray(reposData)
        ? reposData.filter((r) => !r.fork)
        : [];

      ghEvents = await fetchAllEvents();
      commits = extractCommits(ghEvents.filter((e) => e.type === "PushEvent"));

      renderStats();
      renderDistribution("days");
      initDistTabs();
      renderHeatmap();
      renderLanguages();
      renderRadar();
      renderTimeline();
      renderRepos();
      renderInsights();

      if (window.lucide) lucide.createIcons();
    } catch (err) {
      console.error("GitHub API error:", err);
      hideAllLoaders();
    }
  }

  async function fetchAllEvents() {
    const all = [];
    for (let p = 1; p <= 10; p++) {
      try {
        const res = await fetch(
          "https://api.github.com/users/" +
            GH_USER +
            "/events?per_page=100&page=" +
            p,
        );
        if (!res.ok) break;
        const data = await res.json();
        if (!data.length) break;
        all.push(...data);
      } catch {
        break;
      }
    }
    return all;
  }

  function extractCommits(pushEvents) {
    const arr = [];
    for (const ev of pushEvents) {
      const n =
        ev.payload?.size ||
        (ev.payload?.commits ? ev.payload.commits.length : 1);
      const date = new Date(ev.created_at);
      for (let i = 0; i < n; i++) arr.push(date);
    }
    return arr;
  }

  function hideAllLoaders() {
    document
      .querySelectorAll(".chart-loading")
      .forEach((el) => el.classList.add("hidden"));
  }

  // ════════════════════════════════════════════════════════════
  // 5. STATS CARDS
  // ════════════════════════════════════════════════════════════
  function renderStats() {
    const grid = document.getElementById("stats-grid");
    if (!grid) return;

    const totalStars = ghRepos.reduce(
      (s, r) => s + (r.stargazers_count || 0),
      0,
    );

    // Streak
    const daySet = new Set(commits.map((c) => c.toISOString().slice(0, 10)));
    const sorted = [...daySet].sort();
    let maxStreak = sorted.length ? 1 : 0,
      cur = 1;
    for (let i = 1; i < sorted.length; i++) {
      const diff = (new Date(sorted[i]) - new Date(sorted[i - 1])) / 86400000;
      if (diff === 1) {
        cur++;
        maxStreak = Math.max(maxStreak, cur);
      } else cur = 1;
    }

    // Avg per week
    const weeks = new Set(
      commits.map((c) => {
        const d = new Date(c);
        return d.getFullYear() + "-W" + getWeekNum(d);
      }),
    );
    const avgPerWeek = weeks.size ? Math.round(commits.length / weeks.size) : 0;

    const stats = [
      { icon: "folder-git-2", value: ghRepos.length, label: "Public Repos" },
      {
        icon: "git-commit-horizontal",
        value: commits.length,
        label: "Recent Commits",
      },
      { icon: "star", value: totalStars, label: "Total Stars" },
      { icon: "flame", value: maxStreak, label: "Day Streak", suffix: "d" },
      { icon: "trending-up", value: avgPerWeek, label: "Commits / Week" },
      {
        icon: "users",
        value: ghUser ? ghUser.followers : 0,
        label: "Followers",
      },
    ];

    grid.innerHTML = stats
      .map(
        (s) => `
      <div class="stat-card" data-animate="fade-up">
        <div class="stat-icon"><i data-lucide="${s.icon}"></i></div>
        <div class="stat-info">
          <span class="stat-value" data-count="${s.value}" data-suffix="${s.suffix || ""}">${s.value}${s.suffix || ""}</span>
          <span class="stat-label">${s.label}</span>
        </div>
      </div>`,
      )
      .join("");

    grid.querySelectorAll("[data-count]").forEach((el) => {
      animateNum(el, parseInt(el.dataset.count, 10), el.dataset.suffix || "");
    });

    if (window.lucide) lucide.createIcons();
  }

  function animateNum(el, target, suffix) {
    const dur = 1200;
    const start = performance.now();
    function tick(now) {
      const p = Math.min((now - start) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(eased * target) + suffix;
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  // ════════════════════════════════════════════════════════════
  // 6. COMMIT DISTRIBUTION (bar chart)
  // ════════════════════════════════════════════════════════════
  function initDistTabs() {
    const tabs = document.querySelectorAll("#dist-tabs .chart-tab");
    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        tabs.forEach((t) => t.classList.remove("active"));
        tab.classList.add("active");
        renderDistribution(tab.dataset.range);
      });
    });
  }

  function renderDistribution(range) {
    const canvas = document.getElementById("dist-chart");
    const loading = document.getElementById("dist-loading");
    if (!canvas) return;
    if (loading) loading.classList.add("hidden");

    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const W = rect.width,
      H = rect.height;
    ctx.clearRect(0, 0, W, H);

    const buckets = bucketize(commits, range);
    if (!buckets.length) return;

    const max = Math.max(...buckets.map((b) => b.count), 1);
    const pad = { top: 16, right: 16, bottom: 32, left: 44 };
    const cW = W - pad.left - pad.right;
    const cH = H - pad.top - pad.bottom;
    const barW = Math.max(3, (cW / buckets.length) * 0.6);
    const gap = cW / buckets.length;

    // Grid
    for (let i = 0; i <= 4; i++) {
      const y = pad.top + (cH / 4) * i;
      ctx.strokeStyle = "rgba(" + AC + ",.04)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(W - pad.right, y);
      ctx.stroke();

      const val = Math.round((max / 4) * (4 - i));
      ctx.fillStyle = "rgba(" + AC + ",.3)";
      ctx.font = '9px "JetBrains Mono",monospace';
      ctx.textAlign = "right";
      ctx.fillText(val, pad.left - 8, y + 3);
    }

    // Bars
    buckets.forEach((b, idx) => {
      const x = pad.left + idx * gap + (gap - barW) / 2;
      const bH = (b.count / max) * cH;
      const y = pad.top + cH - bH;

      if (bH > 0) {
        ctx.save();
        ctx.shadowColor = "rgba(" + AC + ",.3)";
        ctx.shadowBlur = 8;
        ctx.fillStyle = "rgba(" + AC + ",.12)";
        ctx.fillRect(x - 1, y + 2, barW + 2, bH - 2);
        ctx.restore();

        const grad = ctx.createLinearGradient(x, y, x, y + bH);
        grad.addColorStop(0, "rgba(" + AC + ",.9)");
        grad.addColorStop(1, "rgba(" + AC + ",.2)");
        ctx.fillStyle = grad;

        const r = Math.min(barW / 2, 3);
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.lineTo(x + barW - r, y);
        ctx.quadraticCurveTo(x + barW, y, x + barW, y + r);
        ctx.lineTo(x + barW, y + bH);
        ctx.lineTo(x, y + bH);
        ctx.lineTo(x, y + r);
        ctx.quadraticCurveTo(x, y, x + r, y);
        ctx.fill();
      }

      const every = buckets.length > 20 ? 5 : buckets.length > 12 ? 3 : 1;
      if (idx % every === 0 || idx === buckets.length - 1) {
        ctx.fillStyle = "rgba(" + AC + ",.25)";
        ctx.font = '8px "JetBrains Mono",monospace';
        ctx.textAlign = "center";
        ctx.fillText(b.label, x + barW / 2, H - pad.bottom + 14);
      }
    });

    ctx.strokeStyle = "rgba(" + AC + ",.08)";
    ctx.beginPath();
    ctx.moveTo(pad.left, pad.top + cH);
    ctx.lineTo(W - pad.right, pad.top + cH);
    ctx.stroke();
  }

  function bucketize(data, range) {
    const map = {};
    const now = new Date();

    if (range === "days") {
      for (let i = 29; i >= 0; i--) {
        const d = new Date(now);
        d.setDate(d.getDate() - i);
        const k = d.toISOString().slice(0, 10);
        map[k] = { label: d.getMonth() + 1 + "/" + d.getDate(), count: 0 };
      }
      data.forEach((c) => {
        const k = c.toISOString().slice(0, 10);
        if (map[k]) map[k].count++;
      });
    } else if (range === "weeks") {
      for (let i = 11; i >= 0; i--) {
        const d = new Date(now);
        d.setDate(d.getDate() - i * 7);
        const ws = new Date(d);
        ws.setDate(ws.getDate() - ws.getDay());
        const k = ws.toISOString().slice(0, 10);
        if (!map[k]) map[k] = { label: "W" + getWeekNum(ws), count: 0 };
      }
      data.forEach((c) => {
        const ws = new Date(c);
        ws.setDate(ws.getDate() - ws.getDay());
        const k = ws.toISOString().slice(0, 10);
        if (map[k]) map[k].count++;
      });
    } else {
      const months = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
      ];
      for (let i = 5; i >= 0; i--) {
        const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
        const k = d.toISOString().slice(0, 7);
        map[k] = { label: months[d.getMonth()], count: 0 };
      }
      data.forEach((c) => {
        const k = c.toISOString().slice(0, 7);
        if (map[k]) map[k].count++;
      });
    }
    return Object.values(map);
  }

  function getWeekNum(d) {
    const s = new Date(d.getFullYear(), 0, 1);
    return Math.ceil(((d - s) / 86400000 + s.getDay() + 1) / 7);
  }

  // ════════════════════════════════════════════════════════════
  // 7. ACTIVITY HEATMAP
  // ════════════════════════════════════════════════════════════
  function renderHeatmap() {
    const grid = document.getElementById("hm-grid");
    const yLab = document.getElementById("hm-y");
    const xLab = document.getElementById("hm-x");
    const loading = document.getElementById("hm-loading");
    if (!grid) return;
    if (loading) loading.classList.add("hidden");

    const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    const matrix = Array.from({ length: 7 }, () => Array(24).fill(0));
    commits.forEach((c) => matrix[c.getDay()][c.getHours()]++);
    const max = Math.max(...matrix.flat(), 1);

    if (yLab)
      yLab.innerHTML = DAYS.map((d) => "<span>" + d + "</span>").join("");

    if (xLab) {
      xLab.innerHTML = "";
      for (let h = 0; h < 24; h += 2) {
        const s =
          h === 0 ? "12a" : h < 12 ? h + "a" : h === 12 ? "12p" : h - 12 + "p";
        xLab.innerHTML += "<span>" + s + "</span>";
      }
    }

    grid.innerHTML = "";
    for (let d = 0; d < 7; d++) {
      for (let h = 0; h < 24; h++) {
        const cell = document.createElement("div");
        cell.className = "hm-cell";
        const val = matrix[d][h];
        const intensity = val / max;

        if (val > 0) {
          const alpha = 0.12 + intensity * 0.88;
          cell.style.background = "rgba(" + AC + "," + alpha.toFixed(2) + ")";
          if (intensity > 0.7) cell.classList.add("glow-hi");
          else if (intensity > 0.4) cell.classList.add("glow-md");
        }

        const hStr =
          h === 0
            ? "12am"
            : h < 12
              ? h + "am"
              : h === 12
                ? "12pm"
                : h - 12 + "pm";
        cell.setAttribute("data-tip", DAYS[d] + " " + hStr + ": " + val);
        grid.appendChild(cell);
      }
    }
  }

  // ════════════════════════════════════════════════════════════
  // 8. LANGUAGE DONUT
  // ════════════════════════════════════════════════════════════
  function renderLanguages() {
    const canvas = document.getElementById("lang-chart");
    const list = document.getElementById("lang-list");
    const loading = document.getElementById("lang-loading");
    if (!canvas || !ghRepos.length) return;
    if (loading) loading.classList.add("hidden");

    const counts = {};
    ghRepos.forEach((r) => {
      if (r.language)
        counts[r.language] = (counts[r.language] || 0) + (r.size || 1);
    });
    const sorted = Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 7);
    const total = sorted.reduce((s, x) => s + x[1], 0);

    const langColors = {
      TypeScript: "#3178c6",
      JavaScript: "#f1e05a",
      Python: "#3572a5",
      HTML: "#e34c26",
      CSS: "#563d7c",
      Shell: "#89e051",
      Dockerfile: "#384d54",
      Vue: "#41b883",
      Go: "#00add8",
      Rust: "#dea584",
      Java: "#b07219",
    };
    const fallback = [
      "#22d3ee",
      "#a78bfa",
      "#4ade80",
      "#f87171",
      "#facc15",
      "#fb923c",
      "#38bdf8",
    ];

    const ctx = canvas.getContext("2d");
    const size = Math.min(canvas.width, canvas.height);
    const cx = size / 2,
      cy = size / 2;
    const outer = size / 2 - 8;
    const inner = outer * 0.55;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    let angle = -Math.PI / 2;
    sorted.forEach(([lang, val], i) => {
      const sweep = (val / total) * Math.PI * 2;
      const color = langColors[lang] || fallback[i % fallback.length];

      ctx.beginPath();
      ctx.arc(cx, cy, outer, angle, angle + sweep);
      ctx.arc(cx, cy, inner, angle + sweep, angle, true);
      ctx.closePath();
      ctx.fillStyle = color;
      ctx.fill();

      ctx.shadowColor = color;
      ctx.shadowBlur = 6;
      ctx.fill();
      ctx.shadowBlur = 0;

      angle += sweep;
    });

    ctx.fillStyle = "#e0e0e8";
    ctx.font = "bold 16px Inter,sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(sorted.length, cx, cy - 6);
    ctx.fillStyle = "#55556a";
    ctx.font = '9px "JetBrains Mono",monospace';
    ctx.fillText("langs", cx, cy + 8);

    if (list) {
      list.innerHTML = sorted
        .map(([lang, val], i) => {
          const color = langColors[lang] || fallback[i % fallback.length];
          const pct = ((val / total) * 100).toFixed(1);
          return (
            '<div class="lang-item">' +
            '<span class="lang-dot" style="background:' +
            color +
            '"></span>' +
            '<span class="lang-name">' +
            lang +
            "</span>" +
            '<span class="lang-pct">' +
            pct +
            "%</span>" +
            "</div>"
          );
        })
        .join("");
    }
  }

  // ════════════════════════════════════════════════════════════
  // 9. CODING PATTERNS RADAR
  // ════════════════════════════════════════════════════════════
  function renderRadar() {
    const canvas = document.getElementById("radar-chart");
    if (!canvas || !commits.length) return;

    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const W = rect.width,
      H = rect.height;
    ctx.clearRect(0, 0, W, H);

    const slots = Array(8).fill(0);
    const labels = [
      "00–03",
      "03–06",
      "06–09",
      "09–12",
      "12–15",
      "15–18",
      "18–21",
      "21–24",
    ];
    commits.forEach((c) => {
      slots[Math.floor(c.getHours() / 3)]++;
    });

    const n = 8;
    const max = Math.max(...slots, 1);
    const cx = W / 2,
      cy = H / 2;
    const R = Math.min(W, H) / 2 - 38;

    // Grid circles
    for (let lv = 1; lv <= 4; lv++) {
      const r = (R / 4) * lv;
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(" + AC + ",.06)";
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // Axes + labels
    for (let i = 0; i < n; i++) {
      const a = ((Math.PI * 2) / n) * i - Math.PI / 2;
      const ex = cx + Math.cos(a) * R;
      const ey = cy + Math.sin(a) * R;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(ex, ey);
      ctx.strokeStyle = "rgba(" + AC + ",.08)";
      ctx.stroke();

      const lx = cx + Math.cos(a) * (R + 24);
      const ly = cy + Math.sin(a) * (R + 24);
      ctx.fillStyle = "rgba(" + AC + ",.4)";
      ctx.font = '9px "JetBrains Mono",monospace';
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(labels[i], lx, ly);
    }

    // Data polygon
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
      const a = ((Math.PI * 2) / n) * i - Math.PI / 2;
      const r = (slots[i] / max) * R;
      const px = cx + Math.cos(a) * r;
      const py = cy + Math.sin(a) * r;
      i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
    }
    ctx.closePath();
    ctx.fillStyle = "rgba(" + AC + ",.1)";
    ctx.fill();
    ctx.strokeStyle = "rgba(" + AC + ",.7)";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Data points
    for (let i = 0; i < n; i++) {
      const a = ((Math.PI * 2) / n) * i - Math.PI / 2;
      const r = (slots[i] / max) * R;
      const px = cx + Math.cos(a) * r;
      const py = cy + Math.sin(a) * r;
      ctx.beginPath();
      ctx.arc(px, py, 4, 0, Math.PI * 2);
      ctx.fillStyle = "#22d3ee";
      ctx.shadowColor = "#22d3ee";
      ctx.shadowBlur = 8;
      ctx.fill();
      ctx.shadowBlur = 0;
    }
  }

  // ════════════════════════════════════════════════════════════
  // 10. TIMELINE
  // ════════════════════════════════════════════════════════════
  function renderTimeline() {
    const feed = document.getElementById("timeline-feed");
    const loading = document.getElementById("tl-loading");
    if (!feed) return;
    if (loading) loading.classList.add("hidden");

    const icons = {
      PushEvent: "git-commit-horizontal",
      CreateEvent: "git-branch-plus",
      DeleteEvent: "trash-2",
      WatchEvent: "star",
      ForkEvent: "git-fork",
      IssuesEvent: "circle-dot",
      PullRequestEvent: "git-pull-request",
      ReleaseEvent: "tag",
      IssueCommentEvent: "message-circle",
      PullRequestReviewEvent: "eye",
    };

    const recent = ghEvents.slice(0, 25);

    feed.innerHTML = recent
      .map((ev) => {
        const icon = icons[ev.type] || "activity";
        const repo = ev.repo ? ev.repo.name.split("/")[1] : "?";
        const time = relativeTime(new Date(ev.created_at));
        let desc = ev.type.replace("Event", "");
        if (ev.type === "PushEvent") {
          const n =
            ev.payload?.size ||
            (ev.payload?.commits ? ev.payload.commits.length : 1);
          desc = n + " commit" + (n > 1 ? "s" : "");
        } else if (ev.type === "CreateEvent") {
          desc = "Created " + (ev.payload?.ref_type || "ref");
        } else if (ev.type === "WatchEvent") {
          desc = "Starred";
        } else if (ev.type === "ForkEvent") {
          desc = "Forked";
        }

        return (
          '<div class="tl-item">' +
          '<div class="tl-icon"><i data-lucide="' +
          icon +
          '"></i></div>' +
          '<div class="tl-body">' +
          '<span class="tl-repo">' +
          repo +
          "</span>" +
          '<span class="tl-desc">' +
          desc +
          "</span>" +
          "</div>" +
          '<span class="tl-time">' +
          time +
          "</span>" +
          "</div>"
        );
      })
      .join("");
  }

  function relativeTime(date) {
    const s = Math.floor((Date.now() - date.getTime()) / 1000);
    if (s < 60) return "now";
    if (s < 3600) return Math.floor(s / 60) + "m";
    if (s < 86400) return Math.floor(s / 3600) + "h";
    if (s < 604800) return Math.floor(s / 86400) + "d";
    return Math.floor(s / 604800) + "w";
  }

  // ════════════════════════════════════════════════════════════
  // 11. TOP REPOS
  // ════════════════════════════════════════════════════════════
  function renderRepos() {
    const grid = document.getElementById("repos-grid");
    const loading = document.getElementById("repos-loading");
    if (!grid) return;
    if (loading) loading.classList.add("hidden");

    const langColors = {
      TypeScript: "#3178c6",
      JavaScript: "#f1e05a",
      Python: "#3572a5",
      HTML: "#e34c26",
      CSS: "#563d7c",
      Shell: "#89e051",
    };

    const top = ghRepos
      .sort(
        (a, b) =>
          b.stargazers_count +
          b.forks_count * 2 -
          (a.stargazers_count + a.forks_count * 2),
      )
      .slice(0, 9);

    grid.innerHTML = top
      .map((r) => {
        const lang = r.language || "—";
        const color = langColors[lang] || "#8888a0";
        return (
          '<a href="' +
          r.html_url +
          '" target="_blank" rel="noopener" class="repo-card">' +
          '<div class="repo-header">' +
          '<i data-lucide="folder-git-2" class="repo-icon"></i>' +
          "<h3>" +
          r.name +
          "</h3>" +
          "</div>" +
          '<p class="repo-desc">' +
          (r.description || "No description") +
          "</p>" +
          '<div class="repo-meta">' +
          '<span class="repo-lang"><span class="lang-dot" style="background:' +
          color +
          '"></span>' +
          lang +
          "</span>" +
          (r.stargazers_count
            ? '<span class="repo-stat"><i data-lucide="star"></i>' +
              r.stargazers_count +
              "</span>"
            : "") +
          (r.forks_count
            ? '<span class="repo-stat"><i data-lucide="git-fork"></i>' +
              r.forks_count +
              "</span>"
            : "") +
          "</div>" +
          "</a>"
        );
      })
      .join("");
  }

  // ════════════════════════════════════════════════════════════
  // 12. INSIGHTS
  // ════════════════════════════════════════════════════════════
  function renderInsights() {
    const grid = document.getElementById("insights-grid");
    if (!grid || !commits.length) return;

    // Peak hour
    const hours = Array(24).fill(0);
    commits.forEach((c) => hours[c.getHours()]++);
    const peakH = hours.indexOf(Math.max(...hours));
    const peakStr =
      peakH === 0
        ? "12 AM"
        : peakH < 12
          ? peakH + " AM"
          : peakH === 12
            ? "12 PM"
            : peakH - 12 + " PM";

    // Peak day
    const days = Array(7).fill(0);
    const dayNames = [
      "Sunday",
      "Monday",
      "Tuesday",
      "Wednesday",
      "Thursday",
      "Friday",
      "Saturday",
    ];
    commits.forEach((c) => days[c.getDay()]++);
    const peakD = days.indexOf(Math.max(...days));

    // Night owl (10pm–6am)
    const night = commits.filter((c) => {
      const h = c.getHours();
      return h >= 22 || h < 6;
    });
    const nightPct = Math.round((night.length / commits.length) * 100);

    // Focus (best 3h window)
    let maxWin = 0;
    for (let s = 0; s < 24; s++) {
      const w = hours[s] + hours[(s + 1) % 24] + hours[(s + 2) % 24];
      maxWin = Math.max(maxWin, w);
    }
    const focusPct = Math.round((maxWin / commits.length) * 100);

    // Top language
    const langCounts = {};
    ghRepos.forEach((r) => {
      if (r.language)
        langCounts[r.language] = (langCounts[r.language] || 0) + (r.size || 1);
    });
    const topLang =
      Object.entries(langCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || "—";

    const items = [
      { icon: "clock", value: peakStr, label: "Peak Coding Hour" },
      { icon: "calendar", value: dayNames[peakD], label: "Most Active Day" },
      { icon: "moon", value: nightPct + "%", label: "Night Owl Index" },
      { icon: "target", value: focusPct + "%", label: "Focus Score" },
      { icon: "code-2", value: topLang, label: "Top Language" },
      { icon: "activity", value: ghEvents.length, label: "API Events" },
    ];

    grid.innerHTML = items
      .map(
        (it) =>
          '<div class="insight-card">' +
          '<div class="insight-icon"><i data-lucide="' +
          it.icon +
          '"></i></div>' +
          '<span class="insight-value">' +
          it.value +
          "</span>" +
          '<span class="insight-label">' +
          it.label +
          "</span>" +
          "</div>",
      )
      .join("");

    if (window.lucide) lucide.createIcons();
  }
})();
