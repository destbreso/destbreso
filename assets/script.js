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
  let allEventDates = []; // Date[] from ALL event types (max data)
  let contributions = []; // {date,count,level}[] from contributions API
  let contribTotal = 0;
  let repoLangsMap = {}; // repo → {lang: bytes}
  let repoWeeklyStats = {}; // repo → [{week, total}] from stats/commit_activity (52 weeks)

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
      "#contributions, #distribution, #analytics, #patterns, #repos, #projects, #insights, #daily-hours, footer",
    );
    const chars =
      "アイウエオカキクケコサシスセソタチツテトナニヌネノ0123456789ABCDEF{}[]";
    const colors = [
      "rgba(34,211,238,0.35)",
      "rgba(34,211,238,0.22)",
      "rgba(0,255,65,0.18)",
      "rgba(34,211,238,0.28)",
      "rgba(167,139,250,0.18)",
    ];

    targets.forEach((section) => {
      const wrap = document.createElement("div");
      wrap.className = "cascade-wrap";
      section.prepend(wrap);

      function spawnDrop() {
        if (document.hidden) return;
        const span = document.createElement("span");
        span.className = "cascade-char";
        span.textContent = chars[Math.floor(Math.random() * chars.length)];
        span.style.left = 5 + Math.random() * 90 + "%";
        span.style.color = colors[Math.floor(Math.random() * colors.length)];
        const dur = 0.8 + Math.random() * 1.2;
        span.style.animationDuration = dur + "s";
        wrap.appendChild(span);
        setTimeout(() => span.remove(), dur * 1000 + 50);
      }

      // Fewer drops (~3/sec) for subtlety
      setInterval(spawnDrop, 280 + Math.random() * 120);
    });
  }

  // ════════════════════════════════════════════════════════════
  // 4. GITHUB API
  // ════════════════════════════════════════════════════════════
  async function fetchGitHubData() {
    try {
      const [userData, reposData, contribData] = await Promise.all([
        fetch("https://api.github.com/users/" + GH_USER).then((r) =>
          r.ok ? r.json() : null,
        ),
        fetch(
          "https://api.github.com/users/" +
            GH_USER +
            "/repos?per_page=100&sort=pushed",
        ).then((r) => (r.ok ? r.json() : [])),
        fetch(
          "https://github-contributions-api.jogruber.de/v4/" +
            GH_USER +
            "?y=last",
        ).then((r) => (r.ok ? r.json() : null)),
      ]);

      ghUser = userData;
      ghRepos = Array.isArray(reposData)
        ? reposData.filter((r) => !r.fork)
        : [];

      // Parse contributions API
      if (contribData && contribData.contributions) {
        contributions = contribData.contributions;
        contribTotal = contribData.total
          ? contribData.total.lastYear ||
            contribData.total[Object.keys(contribData.total).pop()] ||
            0
          : contributions.reduce((s, c) => s + c.count, 0);
      }

      ghEvents = await fetchAllEvents();
      commits = extractCommits(ghEvents.filter((e) => e.type === "PushEvent"));
      // Build allEventDates: expand PushEvents by commit count for accurate volume
      allEventDates = [];
      ghEvents.forEach((ev) => {
        const d = new Date(ev.created_at);
        if (ev.type === "PushEvent") {
          const n =
            ev.payload?.size ||
            (ev.payload?.commits ? ev.payload.commits.length : 1);
          for (let i = 0; i < n; i++) allEventDates.push(d);
        } else {
          allEventDates.push(d);
        }
      });

      // Fetch per-repo language breakdowns for top repos (real bytes)
      repoLangsMap = await fetchRepoLanguages(ghRepos.slice(0, 20));

      // Fetch yearly commit stats per repo (52 weeks of data)
      repoWeeklyStats = await fetchRepoCommitStats(ghRepos.slice(0, 15));

      renderContribGraph();
      renderStats();
      renderDistribution("days");
      initDistTabs();
      renderHeatmap();
      renderLanguages();
      renderRadar();
      renderTimeline();
      renderRepos();
      renderProjectAnalytics();
      renderInsights();
      renderDailyHours();

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

  async function fetchRepoLanguages(repos) {
    const map = {};
    // Batch fetch in parallel (max 20 repos)
    const promises = repos.map((r) =>
      fetch(
        "https://api.github.com/repos/" + GH_USER + "/" + r.name + "/languages",
      )
        .then((res) => (res.ok ? res.json() : {}))
        .then((langs) => {
          map[r.name] = langs;
        })
        .catch(() => {
          map[r.name] = {};
        }),
    );
    await Promise.all(promises);
    return map;
  }

  async function fetchRepoCommitStats(repos) {
    // Returns {repoName: [{week: unixTs, total: N, days: [Sun..Sat]}]}
    const map = {};
    const promises = repos.map((r) =>
      fetch(
        "https://api.github.com/repos/" +
          GH_USER +
          "/" +
          r.name +
          "/stats/commit_activity",
      )
        .then((res) => (res.ok ? res.json() : []))
        .then((data) => {
          map[r.name] = Array.isArray(data) ? data : [];
        })
        .catch(() => {
          map[r.name] = [];
        }),
    );
    await Promise.all(promises);
    return map;
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
  // 4b. CONTRIBUTION GRAPH (GitHub-style)
  // ════════════════════════════════════════════════════════════
  function renderContribGraph() {
    const grid = document.getElementById("contrib-grid");
    const monthsEl = document.getElementById("contrib-months");
    const daysEl = document.getElementById("contrib-days");
    const totalEl = document.getElementById("contrib-total");
    const loading = document.getElementById("contrib-loading");
    if (!grid) return;
    if (loading) loading.classList.add("hidden");

    if (!contributions.length) {
      grid.innerHTML =
        '<span style="color:var(--text-dim);font-size:.8rem">No contribution data</span>';
      return;
    }

    // Show total
    if (totalEl) {
      totalEl.textContent = contribTotal.toLocaleString() + " in the last year";
    }

    // Sort contributions ascending by date
    const sorted = [...contributions].sort((a, b) =>
      a.date.localeCompare(b.date),
    );

    // Find the first Sunday on or before the first date to align the grid
    const firstDate = new Date(sorted[0].date + "T00:00:00");
    const startDate = new Date(firstDate);
    startDate.setDate(startDate.getDate() - startDate.getDay()); // back to Sunday

    const lastDate = new Date(sorted[sorted.length - 1].date + "T00:00:00");

    // Build date->contrib lookup
    const lookup = {};
    sorted.forEach((c) => {
      lookup[c.date] = c;
    });

    // Day labels (Mon, Wed, Fri)
    if (daysEl) {
      const dayLabels = ["", "Mon", "", "Wed", "", "Fri", ""];
      daysEl.innerHTML = dayLabels
        .map((d) => "<span>" + d + "</span>")
        .join("");
    }

    // Build weeks and cells
    grid.innerHTML = "";
    const weeks = [];
    const cur = new Date(startDate);

    while (cur <= lastDate) {
      const dateStr =
        cur.getFullYear() +
        "-" +
        String(cur.getMonth() + 1).padStart(2, "0") +
        "-" +
        String(cur.getDate()).padStart(2, "0");

      const entry = lookup[dateStr];
      const count = entry ? entry.count : 0;
      const level = entry ? entry.level : 0;

      const cell = document.createElement("div");
      cell.className = "contrib-cell" + (level > 0 ? " lv-" + level : "");

      // Format tooltip date
      const monthNames = [
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
      const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
      const tipDate =
        dayNames[cur.getDay()] +
        ", " +
        monthNames[cur.getMonth()] +
        " " +
        cur.getDate() +
        ", " +
        cur.getFullYear();
      cell.setAttribute(
        "data-tip",
        count === 0
          ? "No contributions on " + tipDate
          : count + " contribution" + (count > 1 ? "s" : "") + " on " + tipDate,
      );

      // Track week for month labels
      const weekIdx = Math.floor((cur - startDate) / (7 * 86400000));
      if (!weeks[weekIdx])
        weeks[weekIdx] = {
          month: cur.getMonth(),
          year: cur.getFullYear(),
          day: cur.getDate(),
        };

      grid.appendChild(cell);
      cur.setDate(cur.getDate() + 1);
    }

    // Month labels
    if (monthsEl) {
      const monthNames = [
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
      const totalWeeks = weeks.length;

      // Calculate width per week
      monthsEl.innerHTML = "";
      let lastMonth = -1;
      const monthSpans = [];

      for (let w = 0; w < totalWeeks; w++) {
        const wk = weeks[w];
        if (!wk) continue;
        if (wk.month !== lastMonth) {
          monthSpans.push({ month: wk.month, startWeek: w });
          lastMonth = wk.month;
        }
      }

      // Render month labels with proportional widths
      monthSpans.forEach((ms, idx) => {
        const nextStart =
          idx + 1 < monthSpans.length
            ? monthSpans[idx + 1].startWeek
            : totalWeeks;
        const span = document.createElement("span");
        span.textContent = monthNames[ms.month];
        // Each week is one column: cell-size + gap
        const weekCols = nextStart - ms.startWeek;
        span.style.width =
          "calc((" + weekCols + " * (var(--cell-size, 13px) + 3px)))";
        monthsEl.appendChild(span);
      });
    }
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

    // Streak from contributions (real data)
    let maxStreak = 0,
      curStreak = 0;
    if (contributions.length) {
      const sorted = [...contributions].sort((a, b) =>
        a.date.localeCompare(b.date),
      );
      for (let i = 0; i < sorted.length; i++) {
        if (sorted[i].count > 0) {
          curStreak++;
          maxStreak = Math.max(maxStreak, curStreak);
        } else {
          curStreak = 0;
        }
      }
    } else {
      // Fallback to events
      const daySet = new Set(commits.map((c) => c.toISOString().slice(0, 10)));
      const sortedDays = [...daySet].sort();
      maxStreak = sortedDays.length ? 1 : 0;
      let cur = 1;
      for (let i = 1; i < sortedDays.length; i++) {
        const diff =
          (new Date(sortedDays[i]) - new Date(sortedDays[i - 1])) / 86400000;
        if (diff === 1) {
          cur++;
          maxStreak = Math.max(maxStreak, cur);
        } else cur = 1;
      }
    }

    // Avg per week from contributions
    const totalContribs = contribTotal || commits.length;
    const weeksOfData = contributions.length
      ? Math.ceil(contributions.length / 7)
      : 1;
    const avgPerWeek = Math.round(totalContribs / Math.max(weeksOfData, 1));

    // Current streak (from end)
    let currentStreak = 0;
    if (contributions.length) {
      const sorted = [...contributions].sort((a, b) =>
        b.date.localeCompare(a.date),
      );
      // skip today if 0 (day not over)
      const startIdx = sorted[0].count === 0 ? 1 : 0;
      for (let i = startIdx; i < sorted.length; i++) {
        if (sorted[i].count > 0) currentStreak++;
        else break;
      }
    }

    const stats = [
      { icon: "folder-git-2", value: ghRepos.length, label: "Public Repos" },
      {
        icon: "git-commit-horizontal",
        value: totalContribs,
        label: "Contributions (1y)",
      },
      { icon: "star", value: totalStars, label: "Total Stars" },
      { icon: "flame", value: maxStreak, label: "Best Streak", suffix: "d" },
      {
        icon: "zap",
        value: currentStreak,
        label: "Current Streak",
        suffix: "d",
      },
      { icon: "trending-up", value: avgPerWeek, label: "Avg / Week" },
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

  function localDateKey(d) {
    return (
      d.getFullYear() +
      "-" +
      String(d.getMonth() + 1).padStart(2, "0") +
      "-" +
      String(d.getDate()).padStart(2, "0")
    );
  }

  function bucketize(data, range) {
    const map = {};
    const now = new Date();

    // Build a lookup from contributions for quick access
    const contribMap = {};
    contributions.forEach((c) => {
      contribMap[c.date] = c.count;
    });
    const hasContrib = contributions.length > 0;

    if (range === "days") {
      for (let i = 29; i >= 0; i--) {
        const d = new Date(now);
        d.setDate(d.getDate() - i);
        const k = localDateKey(d);
        const count = hasContrib ? contribMap[k] || 0 : 0;
        map[k] = { label: d.getMonth() + 1 + "/" + d.getDate(), count: count };
      }
      if (!hasContrib) {
        data.forEach((c) => {
          const k = localDateKey(c);
          if (map[k]) map[k].count++;
        });
      }
    } else if (range === "weeks") {
      // Generate 12 week buckets
      for (let i = 11; i >= 0; i--) {
        const d = new Date(now);
        d.setDate(d.getDate() - i * 7);
        // Find start of week (Sunday)
        const ws = new Date(d);
        ws.setDate(ws.getDate() - ws.getDay());
        const k = localDateKey(ws);
        if (!map[k]) map[k] = { label: "W" + getWeekNum(ws), count: 0 };
      }
      if (hasContrib) {
        contributions.forEach((c) => {
          const d = new Date(c.date + "T00:00:00");
          const ws = new Date(d);
          ws.setDate(ws.getDate() - ws.getDay());
          const k = localDateKey(ws);
          if (map[k]) map[k].count += c.count;
        });
      } else {
        data.forEach((c) => {
          const ws = new Date(c);
          ws.setDate(ws.getDate() - ws.getDay());
          const k = localDateKey(ws);
          if (map[k]) map[k].count++;
        });
      }
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
      for (let i = 11; i >= 0; i--) {
        const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
        const k =
          d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0");
        map[k] = { label: months[d.getMonth()], count: 0 };
      }
      if (hasContrib) {
        contributions.forEach((c) => {
          const k = c.date.slice(0, 7);
          if (map[k]) map[k].count += c.count;
        });
      } else {
        data.forEach((c) => {
          const k =
            c.getFullYear() + "-" + String(c.getMonth() + 1).padStart(2, "0");
          if (map[k]) map[k].count++;
        });
      }
    }
    return Object.values(map);
  }

  function getWeekNum(d) {
    const s = new Date(d.getFullYear(), 0, 1);
    return Math.ceil(((d - s) / 86400000 + s.getDay() + 1) / 7);
  }

  // ════════════════════════════════════════════════════════════
  // 7. ACTIVITY HEATMAP (uses ALL events for maximum data)
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

    // Strategy: combine contributions (full year, day-level) with
    // event timestamps (limited but has hour precision) to synthesize
    // a rich Day×Hour heatmap.

    // Step 1: Build hour distribution per day-of-week from events
    const eventDayHour = Array.from({ length: 7 }, () => Array(24).fill(0));
    allEventDates.forEach((d) => eventDayHour[d.getDay()][d.getHours()]++);

    // Step 2: Build day-of-week totals from contributions (full year)
    const contribDayTotals = Array(7).fill(0);
    if (contributions.length) {
      contributions.forEach((c) => {
        if (c.count > 0) {
          const d = new Date(c.date + "T00:00:00");
          contribDayTotals[d.getDay()] += c.count;
        }
      });
    }

    // Step 3: For each day-of-week, distribute contribution total
    // across hours using the observed event hour pattern for that day.
    // If no event data for a day, use global hour distribution.
    const globalHour = Array(24).fill(0);
    allEventDates.forEach((d) => globalHour[d.getHours()]++);
    const globalHourTotal = globalHour.reduce((s, v) => s + v, 0) || 1;

    for (let day = 0; day < 7; day++) {
      const dayEventTotal = eventDayHour[day].reduce((s, v) => s + v, 0);
      const contribTotal = contribDayTotals[day];

      if (contribTotal > 0 && dayEventTotal > 0) {
        // Distribute contributions across hours using event hour pattern for this day
        for (let h = 0; h < 24; h++) {
          const hourShare = eventDayHour[day][h] / dayEventTotal;
          matrix[day][h] = Math.round(contribTotal * hourShare);
        }
      } else if (contribTotal > 0) {
        // No event data for this day — use global hour distribution
        for (let h = 0; h < 24; h++) {
          const hourShare = globalHour[h] / globalHourTotal;
          matrix[day][h] = Math.round(contribTotal * hourShare);
        }
      } else {
        // No contribution data — use raw event counts (fallback)
        for (let h = 0; h < 24; h++) {
          matrix[day][h] = eventDayHour[day][h];
        }
      }
    }

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

    // Aggregate from per-repo language API data (real bytes per language)
    const counts = {};
    const hasLangApi = Object.keys(repoLangsMap).length > 0;
    if (hasLangApi) {
      Object.values(repoLangsMap).forEach((langs) => {
        Object.entries(langs).forEach(([lang, bytes]) => {
          counts[lang] = (counts[lang] || 0) + bytes;
        });
      });
    } else {
      // Fallback: primary language per repo
      ghRepos.forEach((r) => {
        if (r.language)
          counts[r.language] = (counts[r.language] || 0) + (r.size || 1);
      });
    }
    const sorted = Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8);
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
    if (!canvas || !allEventDates.length) return;

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
    // Use ALL event timestamps for maximum data
    allEventDates.forEach((d) => {
      slots[Math.floor(d.getHours() / 3)]++;
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
  // 11b. PROJECT ANALYTICS
  // ════════════════════════════════════════════════════════════

  function getRepoEventsMap() {
    // Map repo name → array of event dates (expand PushEvents by commit count)
    // Enriched with yearly stats/commit_activity data
    const map = {};

    // 1. Seed from events API (recent, has hour precision)
    ghEvents.forEach((ev) => {
      const repo = ev.repo ? ev.repo.name.split("/")[1] : null;
      if (!repo) return;
      if (!map[repo]) map[repo] = [];
      const d = new Date(ev.created_at);
      if (ev.type === "PushEvent") {
        const n =
          ev.payload?.size ||
          (ev.payload?.commits ? ev.payload.commits.length : 1);
        for (let i = 0; i < n; i++) map[repo].push(d);
      } else {
        map[repo].push(d);
      }
    });

    // 2. Enrich with yearly stats/commit_activity (52 weeks, day-of-week precision)
    //    For each repo, add synthetic dates for commits not covered by events
    Object.entries(repoWeeklyStats).forEach(([repoName, weeks]) => {
      if (!weeks.length) return;
      if (!map[repoName]) map[repoName] = [];

      // Count events we already have per week-start for this repo
      const existingByWeek = {};
      map[repoName].forEach((d) => {
        const ws = new Date(d);
        ws.setDate(ws.getDate() - ws.getDay());
        const k = localDateKey(ws);
        existingByWeek[k] = (existingByWeek[k] || 0) + 1;
      });

      weeks.forEach((weekData) => {
        if (!weekData.week || !weekData.days) return;
        const weekStart = new Date(weekData.week * 1000);
        const wk = localDateKey(weekStart);
        const existingCount = existingByWeek[wk] || 0;
        const statsTotal = weekData.total || 0;

        // Only add extra if stats reports more than what events gave us
        const extra = Math.max(0, statsTotal - existingCount);
        if (extra <= 0) return;

        // Distribute extra commits across days proportionally to weekData.days
        const daysTotal = weekData.days.reduce((s, v) => s + v, 0) || 1;
        for (let dayIdx = 0; dayIdx < 7; dayIdx++) {
          const dayCommits = Math.round(
            (weekData.days[dayIdx] / daysTotal) * extra,
          );
          if (dayCommits <= 0) continue;
          const dayDate = new Date(weekStart);
          dayDate.setDate(dayDate.getDate() + dayIdx);
          // Set a reasonable hour (midday) since stats don't have hour data
          dayDate.setHours(12, 0, 0, 0);
          for (let c = 0; c < dayCommits; c++) {
            map[repoName].push(dayDate);
          }
        }
      });
    });

    return map;
  }

  function topReposByEvents(repoMap, limit) {
    return Object.entries(repoMap)
      .map(([name, dates]) => ({ name, dates, count: dates.length }))
      .sort((a, b) => b.count - a.count)
      .slice(0, limit);
  }

  function renderProjectEffort() {
    const canvas = document.getElementById("proj-effort-chart");
    const loading = document.getElementById("proj-effort-loading");
    if (!canvas) return;
    if (loading) loading.classList.add("hidden");

    const repoMap = getRepoEventsMap();
    const topRepos = topReposByEvents(repoMap, 10);
    if (!topRepos.length) return;

    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const W = rect.width,
      H = rect.height;
    ctx.clearRect(0, 0, W, H);

    const max = Math.max(...topRepos.map((r) => r.count), 1);
    const pad = { top: 12, right: 20, bottom: 8, left: 110 };
    const cW = W - pad.left - pad.right;
    const cH = H - pad.top - pad.bottom;
    const barH = Math.min(22, (cH / topRepos.length) * 0.65);
    const gap = cH / topRepos.length;

    topRepos.forEach((repo, idx) => {
      const y = pad.top + idx * gap + (gap - barH) / 2;
      const bW = (repo.count / max) * cW;

      // Label
      ctx.fillStyle = "rgba(" + AC + ",.5)";
      ctx.font = '10px "JetBrains Mono",monospace';
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      const label =
        repo.name.length > 14 ? repo.name.slice(0, 13) + "…" : repo.name;
      ctx.fillText(label, pad.left - 8, y + barH / 2);

      // Bar glow
      if (bW > 2) {
        ctx.save();
        ctx.shadowColor = "rgba(" + AC + ",.25)";
        ctx.shadowBlur = 6;
        ctx.fillStyle = "rgba(" + AC + ",.08)";
        ctx.fillRect(pad.left, y + 1, bW, barH - 2);
        ctx.restore();

        const grad = ctx.createLinearGradient(pad.left, 0, pad.left + bW, 0);
        grad.addColorStop(0, "rgba(" + AC + ",.7)");
        grad.addColorStop(1, "rgba(" + AC + ",.2)");
        ctx.fillStyle = grad;
        const r = Math.min(barH / 2, 4);
        ctx.beginPath();
        ctx.moveTo(pad.left, y + r);
        ctx.lineTo(pad.left, y + barH - r);
        ctx.quadraticCurveTo(pad.left, y + barH, pad.left + r, y + barH);
        ctx.lineTo(pad.left + bW - r, y + barH);
        ctx.quadraticCurveTo(
          pad.left + bW,
          y + barH,
          pad.left + bW,
          y + barH - r,
        );
        ctx.lineTo(pad.left + bW, y + r);
        ctx.quadraticCurveTo(pad.left + bW, y, pad.left + bW - r, y);
        ctx.lineTo(pad.left + r, y);
        ctx.quadraticCurveTo(pad.left, y, pad.left, y + r);
        ctx.fill();
      }

      // Count
      ctx.fillStyle = "rgba(" + AC + ",.4)";
      ctx.font = '9px "JetBrains Mono",monospace';
      ctx.textAlign = "left";
      ctx.fillText(repo.count, pad.left + bW + 6, y + barH / 2);
    });
  }

  function renderProjectDayHeatmap() {
    const grid = document.getElementById("proj-day-grid");
    const labels = document.getElementById("proj-day-labels");
    const xAxis = document.getElementById("proj-day-x");
    const loading = document.getElementById("proj-day-loading");
    if (!grid) return;
    if (loading) loading.classList.add("hidden");

    const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const repoMap = getRepoEventsMap();
    const topRepos = topReposByEvents(repoMap, 8);
    if (!topRepos.length) return;

    // Build matrix: repo × day
    const matrix = topRepos.map((repo) => {
      const row = Array(7).fill(0);
      repo.dates.forEach((d) => {
        const day = d.getDay();
        // Convert Sun=0..Sat=6 → Mon=0..Sun=6
        row[day === 0 ? 6 : day - 1]++;
      });
      return row;
    });

    const max = Math.max(...matrix.flat(), 1);

    // Labels
    if (labels) {
      labels.innerHTML = topRepos
        .map((r) => {
          const n = r.name.length > 12 ? r.name.slice(0, 11) + "…" : r.name;
          return '<span title="' + r.name + '">' + n + "</span>";
        })
        .join("");
    }

    // Grid
    grid.style.gridTemplateRows = "repeat(" + topRepos.length + ", 18px)";
    grid.innerHTML = "";
    for (let ri = 0; ri < topRepos.length; ri++) {
      for (let di = 0; di < 7; di++) {
        const cell = document.createElement("div");
        cell.className = "hm-cell";
        const val = matrix[ri][di];
        if (val > 0) {
          const alpha = 0.12 + (val / max) * 0.88;
          cell.style.background = "rgba(" + AC + "," + alpha.toFixed(2) + ")";
          if (val / max > 0.7) cell.classList.add("glow-hi");
          else if (val / max > 0.4) cell.classList.add("glow-md");
        }
        cell.setAttribute(
          "data-tip",
          topRepos[ri].name + " · " + DAYS[di] + ": " + val + " events",
        );
        grid.appendChild(cell);
      }
    }

    // X axis
    if (xAxis) {
      xAxis.innerHTML = DAYS.map((d) => "<span>" + d + "</span>").join("");
    }
  }

  function renderProjectHourHeatmap() {
    const grid = document.getElementById("proj-hour-grid");
    const labels = document.getElementById("proj-hour-labels");
    const xAxis = document.getElementById("proj-hour-x");
    const loading = document.getElementById("proj-hour-loading");
    if (!grid) return;
    if (loading) loading.classList.add("hidden");

    const SLOTS = ["00–04", "04–08", "08–12", "12–16", "16–20", "20–24"];
    const repoMap = getRepoEventsMap();
    const topRepos = topReposByEvents(repoMap, 8);
    if (!topRepos.length) return;

    // Build matrix: repo × time-slot (4h buckets)
    const matrix = topRepos.map((repo) => {
      const row = Array(6).fill(0);
      repo.dates.forEach((d) => {
        row[Math.floor(d.getHours() / 4)]++;
      });
      return row;
    });

    const max = Math.max(...matrix.flat(), 1);

    // Labels
    if (labels) {
      labels.innerHTML = topRepos
        .map((r) => {
          const n = r.name.length > 12 ? r.name.slice(0, 11) + "…" : r.name;
          return '<span title="' + r.name + '">' + n + "</span>";
        })
        .join("");
    }

    // Grid
    grid.style.gridTemplateRows = "repeat(" + topRepos.length + ", 18px)";
    grid.innerHTML = "";
    for (let ri = 0; ri < topRepos.length; ri++) {
      for (let si = 0; si < 6; si++) {
        const cell = document.createElement("div");
        cell.className = "hm-cell";
        const val = matrix[ri][si];
        if (val > 0) {
          const alpha = 0.12 + (val / max) * 0.88;
          cell.style.background = "rgba(" + AC + "," + alpha.toFixed(2) + ")";
          if (val / max > 0.7) cell.classList.add("glow-hi");
          else if (val / max > 0.4) cell.classList.add("glow-md");
        }
        cell.setAttribute(
          "data-tip",
          topRepos[ri].name + " · " + SLOTS[si] + "h: " + val + " events",
        );
        grid.appendChild(cell);
      }
    }

    // X axis
    if (xAxis) {
      xAxis.innerHTML = SLOTS.map((s) => "<span>" + s + "</span>").join("");
    }
  }

  function renderProjectInsights() {
    const container = document.getElementById("proj-insights");
    const loading = document.getElementById("proj-ins-loading");
    if (!container) return;
    if (loading) loading.classList.add("hidden");

    const repoMap = getRepoEventsMap();
    const topRepos = topReposByEvents(repoMap, 20);
    if (!topRepos.length) {
      container.innerHTML =
        '<span style="color:var(--text-dim);font-size:.8rem">No project data</span>';
      return;
    }

    const DAYS = [
      "Sunday",
      "Monday",
      "Tuesday",
      "Wednesday",
      "Thursday",
      "Friday",
      "Saturday",
    ];
    const insights = [];

    // 1. Most focused project (highest event count)
    const top = topRepos[0];
    insights.push({
      icon: "target",
      title: "Most Focused",
      desc:
        top.name +
        " has " +
        top.count +
        " events — your primary project right now",
      badge: top.count + " events",
    });

    // 2. Project diversity (how many repos active)
    const activeCount = topRepos.filter((r) => r.count >= 2).length;
    const totalEvents = topRepos.reduce((s, r) => s + r.count, 0);
    insights.push({
      icon: "layers",
      title: "Project Spread",
      desc:
        activeCount +
        " active repos out of " +
        topRepos.length +
        " in recent history",
      badge: activeCount + " repos",
    });

    // 3. Focus ratio (top project % of total)
    const focusPct = Math.round((top.count / totalEvents) * 100);
    insights.push({
      icon: "pie-chart",
      title: "Focus Ratio",
      desc:
        focusPct +
        "% of effort on " +
        top.name +
        (focusPct > 60
          ? " — deep work mode"
          : focusPct > 35
            ? " — balanced focus"
            : " — multitasking"),
      badge: focusPct + "%",
    });

    // 4. Preferred day per top project
    if (topRepos.length >= 2) {
      const repo = topRepos[0];
      const dayTotals = Array(7).fill(0);
      repo.dates.forEach((d) => dayTotals[d.getDay()]++);
      const peakDay = dayTotals.indexOf(Math.max(...dayTotals));
      insights.push({
        icon: "calendar",
        title: top.name + " Day",
        desc: DAYS[peakDay] + " is your preferred day for " + top.name,
        badge: DAYS[peakDay].slice(0, 3),
      });
    }

    // 5. Night vs Day per top project
    if (top.dates.length) {
      const nightCount = top.dates.filter((d) => {
        const h = d.getHours();
        return h >= 22 || h < 6;
      }).length;
      const nightPct = Math.round((nightCount / top.dates.length) * 100);
      insights.push({
        icon: nightPct > 40 ? "moon" : "sun",
        title: "Work Pattern",
        desc:
          top.name +
          ": " +
          nightPct +
          "% night sessions" +
          (nightPct > 40 ? " — night owl" : " — daytime coder"),
        badge: nightPct + "% night",
      });
    }

    // 6. Weekend warrior
    const weekendEvents = topRepos.reduce((s, r) => {
      return (
        s + r.dates.filter((d) => d.getDay() === 0 || d.getDay() === 6).length
      );
    }, 0);
    const weekendPct = Math.round((weekendEvents / totalEvents) * 100);
    insights.push({
      icon: "coffee",
      title: "Weekend Warrior",
      desc: weekendPct + "% of your activity happens on weekends",
      badge: weekendPct + "%",
    });

    container.innerHTML = insights
      .map(
        (ins) =>
          '<div class="proj-insight-row">' +
          '<div class="proj-insight-icon"><i data-lucide="' +
          ins.icon +
          '"></i></div>' +
          '<div class="proj-insight-text">' +
          '<span class="proj-insight-title">' +
          ins.title +
          "</span>" +
          '<span class="proj-insight-desc">' +
          ins.desc +
          "</span>" +
          "</div>" +
          '<span class="proj-insight-badge">' +
          ins.badge +
          "</span>" +
          "</div>",
      )
      .join("");

    if (window.lucide) lucide.createIcons();
  }

  function renderProjectAnalytics() {
    renderProjectEffort();
    renderProjectDayHeatmap();
    renderProjectHourHeatmap();
    renderProjectInsights();
  }

  // ════════════════════════════════════════════════════════════
  // 12. INSIGHTS
  // ════════════════════════════════════════════════════════════
  function renderInsights() {
    const grid = document.getElementById("insights-grid");
    if (!grid) return;

    // Use ALL event timestamps for time-based insights (max data)
    const hasTime = allEventDates.length > 0;

    // Peak hour (from ALL events)
    let peakStr = "—";
    if (hasTime) {
      const hours = Array(24).fill(0);
      allEventDates.forEach((d) => hours[d.getHours()]++);
      const peakH = hours.indexOf(Math.max(...hours));
      peakStr =
        peakH === 0
          ? "12 AM"
          : peakH < 12
            ? peakH + " AM"
            : peakH === 12
              ? "12 PM"
              : peakH - 12 + " PM";
    }

    // Peak day — prefer contributions (full year), fallback to events
    const dayNames = [
      "Sunday",
      "Monday",
      "Tuesday",
      "Wednesday",
      "Thursday",
      "Friday",
      "Saturday",
    ];
    let peakDayName = "—";
    if (contributions.length) {
      const dayTotals = Array(7).fill(0);
      contributions.forEach((c) => {
        const d = new Date(c.date + "T00:00:00");
        dayTotals[d.getDay()] += c.count;
      });
      const peakD = dayTotals.indexOf(Math.max(...dayTotals));
      peakDayName = dayNames[peakD];
    } else if (hasTime) {
      const days = Array(7).fill(0);
      allEventDates.forEach((d) => days[d.getDay()]++);
      peakDayName = dayNames[days.indexOf(Math.max(...days))];
    }

    // Night owl (10pm–6am) from ALL events
    let nightPct = 0;
    if (hasTime) {
      const night = allEventDates.filter((d) => {
        const h = d.getHours();
        return h >= 22 || h < 6;
      });
      nightPct = Math.round((night.length / allEventDates.length) * 100);
    }

    // Most active month from contributions
    let bestMonth = "—";
    if (contributions.length) {
      const monthTotals = {};
      const monthNames = [
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
      contributions.forEach((c) => {
        const m = c.date.slice(0, 7);
        monthTotals[m] = (monthTotals[m] || 0) + c.count;
      });
      const sorted = Object.entries(monthTotals).sort((a, b) => b[1] - a[1]);
      if (sorted.length) {
        const d = new Date(sorted[0][0] + "-01T00:00:00");
        bestMonth = monthNames[d.getMonth()];
      }
    }

    // Top language from per-repo language data
    const langCounts = {};
    const hasLangApi = Object.keys(repoLangsMap).length > 0;
    if (hasLangApi) {
      Object.values(repoLangsMap).forEach((langs) => {
        Object.entries(langs).forEach(([lang, bytes]) => {
          langCounts[lang] = (langCounts[lang] || 0) + bytes;
        });
      });
    } else {
      ghRepos.forEach((r) => {
        if (r.language)
          langCounts[r.language] =
            (langCounts[r.language] || 0) + (r.size || 1);
      });
    }
    const topLang =
      Object.entries(langCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || "—";

    // Active days % from contributions
    let activeDaysPct = 0;
    if (contributions.length) {
      const activeDays = contributions.filter((c) => c.count > 0).length;
      activeDaysPct = Math.round((activeDays / contributions.length) * 100);
    }

    // Total events tracked
    const totalEvents = allEventDates.length;

    // Average active hours per day (from contributions: days with count>0,
    // estimate unique hours from event hour distribution)
    let avgActiveHours = "—";
    if (allEventDates.length > 0) {
      // Group events by date string, count unique hours per day
      const dayHours = {};
      allEventDates.forEach((d) => {
        const dk = d.toISOString().slice(0, 10);
        if (!dayHours[dk]) dayHours[dk] = new Set();
        dayHours[dk].add(d.getHours());
      });
      const days = Object.values(dayHours);
      const totalUniqueHours = days.reduce((s, set) => s + set.size, 0);
      avgActiveHours = (totalUniqueHours / days.length).toFixed(1) + "h";
    }

    const items = [
      { icon: "clock", value: peakStr, label: "Peak Coding Hour" },
      { icon: "calendar", value: peakDayName, label: "Most Active Day" },
      { icon: "timer", value: avgActiveHours, label: "Avg Active Hours/Day" },
      { icon: "moon", value: nightPct + "%", label: "Night Owl Index" },
      { icon: "trophy", value: bestMonth, label: "Best Month" },
      { icon: "code-2", value: topLang, label: "Top Language" },
      { icon: "percent", value: activeDaysPct + "%", label: "Active Days" },
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

  // ════════════════════════════════════════════════════════════
  // 13. DAILY ACTIVE HOURS TREND
  // ════════════════════════════════════════════════════════════
  function renderDailyHours() {
    const canvas = document.getElementById("daily-hours-chart");
    const loading = document.getElementById("daily-hours-loading");
    const badge = document.getElementById("avg-hours-badge");
    if (!canvas) return;
    if (loading) loading.classList.add("hidden");

    // Prefer contributions for full-year day coverage,
    // combined with event hour patterns to estimate unique active hours per day.

    // Step 1: From events, compute unique active hours per date
    const eventDayHours = {};
    allEventDates.forEach((d) => {
      const dk = d.toISOString().slice(0, 10);
      if (!eventDayHours[dk]) eventDayHours[dk] = new Set();
      eventDayHours[dk].add(d.getHours());
    });

    // Step 2: Compute average unique hours per day from events
    // (how many distinct hours we code on an active day)
    const eventDaysArr = Object.values(eventDayHours);
    const eventAvgHours = eventDaysArr.length
      ? eventDaysArr.reduce((s, set) => s + set.size, 0) / eventDaysArr.length
      : 3; // fallback estimate

    // Step 3: Build 30-day series from contributions (most recent 30 days)
    // For days with contributions, estimate active hours based on contribution count
    // scaled by the event-derived average.
    const now = new Date();
    const buckets = [];

    // Build contribution lookup
    const contribMap = {};
    contributions.forEach((c) => {
      contribMap[c.date] = c.count;
    });

    // Find max daily contribution to normalize
    const last30Contribs = [];
    for (let i = 29; i >= 0; i--) {
      const d = new Date(now);
      d.setDate(d.getDate() - i);
      const dk =
        d.getFullYear() +
        "-" +
        String(d.getMonth() + 1).padStart(2, "0") +
        "-" +
        String(d.getDate()).padStart(2, "0");
      last30Contribs.push({ date: d, key: dk, count: contribMap[dk] || 0 });
    }
    const maxDailyContrib = Math.max(...last30Contribs.map((b) => b.count), 1);

    for (const entry of last30Contribs) {
      let hours = 0;
      // If we have exact event data for this day, use it
      if (eventDayHours[entry.key]) {
        hours = eventDayHours[entry.key].size;
      } else if (entry.count > 0) {
        // Estimate: scale contributions → hours
        // A day with max contributions ≈ eventAvgHours * 1.5 (busy day)
        // A day with few contributions ≈ 1h minimum
        const scale = entry.count / maxDailyContrib;
        hours = Math.max(1, Math.round(scale * eventAvgHours * 1.5 * 10) / 10);
      }
      buckets.push({
        label: entry.date.getMonth() + 1 + "/" + entry.date.getDate(),
        value: hours,
      });
    }

    // Average
    const activeDays = buckets.filter((b) => b.value > 0);
    const avg = activeDays.length
      ? (
          activeDays.reduce((s, b) => s + b.value, 0) / activeDays.length
        ).toFixed(1)
      : "0";
    if (badge) badge.textContent = "Avg: " + avg + "h / active day (last 30d)";

    // Draw area chart
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const W = rect.width,
      H = rect.height;
    ctx.clearRect(0, 0, W, H);

    const pad = { top: 16, right: 16, bottom: 28, left: 36 };
    const cW = W - pad.left - pad.right;
    const cH = H - pad.top - pad.bottom;
    const max = Math.max(...buckets.map((b) => b.value), 1);
    const step = cW / (buckets.length - 1 || 1);

    // Grid lines
    for (let i = 0; i <= 4; i++) {
      const y = pad.top + (cH / 4) * i;
      ctx.strokeStyle = "rgba(" + AC + ",.04)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(W - pad.right, y);
      ctx.stroke();
      const val = ((max / 4) * (4 - i)).toFixed(0);
      ctx.fillStyle = "rgba(" + AC + ",.3)";
      ctx.font = '9px "JetBrains Mono",monospace';
      ctx.textAlign = "right";
      ctx.fillText(val + "h", pad.left - 6, y + 3);
    }

    // Avg line
    const avgY = pad.top + cH - (parseFloat(avg) / max) * cH;
    ctx.save();
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = "rgba(" + AC + ",.3)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(pad.left, avgY);
    ctx.lineTo(W - pad.right, avgY);
    ctx.stroke();
    ctx.restore();
    ctx.fillStyle = "rgba(" + AC + ",.4)";
    ctx.font = '8px "JetBrains Mono",monospace';
    ctx.textAlign = "left";
    ctx.fillText("avg " + avg + "h", W - pad.right + 2, avgY + 3);

    // Build path points
    const points = buckets.map((b, i) => ({
      x: pad.left + i * step,
      y: pad.top + cH - (b.value / max) * cH,
    }));

    // Area fill
    const grad = ctx.createLinearGradient(0, pad.top, 0, pad.top + cH);
    grad.addColorStop(0, "rgba(" + AC + ",.18)");
    grad.addColorStop(1, "rgba(" + AC + ",.01)");
    ctx.beginPath();
    ctx.moveTo(points[0].x, pad.top + cH);
    points.forEach((p) => ctx.lineTo(p.x, p.y));
    ctx.lineTo(points[points.length - 1].x, pad.top + cH);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // Line
    ctx.beginPath();
    points.forEach((p, i) =>
      i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y),
    );
    ctx.strokeStyle = "rgba(" + AC + ",.7)";
    ctx.lineWidth = 2;
    ctx.lineJoin = "round";
    ctx.stroke();

    // Glow under line
    ctx.save();
    ctx.shadowColor = "rgba(" + AC + ",.4)";
    ctx.shadowBlur = 6;
    ctx.stroke();
    ctx.restore();

    // Dots
    points.forEach((p, i) => {
      if (buckets[i].value > 0) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = "#22d3ee";
        ctx.shadowColor = "#22d3ee";
        ctx.shadowBlur = 5;
        ctx.fill();
        ctx.shadowBlur = 0;
      }
    });

    // X labels (every 5 days)
    buckets.forEach((b, i) => {
      if (i % 5 === 0 || i === buckets.length - 1) {
        ctx.fillStyle = "rgba(" + AC + ",.25)";
        ctx.font = '8px "JetBrains Mono",monospace';
        ctx.textAlign = "center";
        ctx.fillText(b.label, pad.left + i * step, H - pad.bottom + 14);
      }
    });
  }
})();
