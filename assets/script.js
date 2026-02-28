/* ================================================================
   David Estevez — Personal Site Scripts
   Terminal typing · Particle canvas · Scroll animations · Nav
   ================================================================ */

(function () {
  "use strict";

  // ── Initialize Lucide icons ───────────────────────────────────
  document.addEventListener("DOMContentLoaded", () => {
    if (window.lucide) lucide.createIcons();
    initCanvas();
    initTerminal();
    initScrollAnimations();
    initNavbar();
    initCounters();
    initGitHubInsights();
  });

  // ════════════════════════════════════════════════════════════════
  // 1. Particle Canvas Background
  // ════════════════════════════════════════════════════════════════
  function initCanvas() {
    const canvas = document.getElementById("bg-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let w, h, particles, mouse;

    const PARTICLE_COUNT = 80;
    const CONNECTION_DIST = 150;
    const MOUSE_DIST = 200;

    mouse = { x: -9999, y: -9999 };

    function resize() {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
    }

    function createParticles() {
      particles = [];
      for (let i = 0; i < PARTICLE_COUNT; i++) {
        particles.push({
          x: Math.random() * w,
          y: Math.random() * h,
          vx: (Math.random() - 0.5) * 0.5,
          vy: (Math.random() - 0.5) * 0.5,
          r: Math.random() * 2 + 0.5,
        });
      }
    }

    function draw() {
      ctx.clearRect(0, 0, w, h);

      // Connections
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < CONNECTION_DIST) {
            const alpha = (1 - dist / CONNECTION_DIST) * 0.15;
            ctx.strokeStyle = `rgba(34, 211, 238, ${alpha})`;
            ctx.lineWidth = 0.5;
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }
      }

      // Mouse connections
      for (const p of particles) {
        const dx = p.x - mouse.x;
        const dy = p.y - mouse.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < MOUSE_DIST) {
          const alpha = (1 - dist / MOUSE_DIST) * 0.3;
          ctx.strokeStyle = `rgba(34, 211, 238, ${alpha})`;
          ctx.lineWidth = 0.8;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(mouse.x, mouse.y);
          ctx.stroke();
        }
      }

      // Particles
      for (const p of particles) {
        ctx.fillStyle = "rgba(34, 211, 238, 0.5)";
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    function update() {
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;
      }
    }

    function loop() {
      update();
      draw();
      requestAnimationFrame(loop);
    }

    resize();
    createParticles();
    loop();

    window.addEventListener("resize", () => {
      resize();
      createParticles();
    });

    window.addEventListener("mousemove", (e) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    });
  }

  // ════════════════════════════════════════════════════════════════
  // 2. Terminal Typing Animation
  // ════════════════════════════════════════════════════════════════
  function initTerminal() {
    const cmdEl = document.getElementById("typed-cmd");
    const outEl = document.getElementById("terminal-output");
    if (!cmdEl || !outEl) return;

    const command = "cat about.json";
    const output = `{
  <span class="accent">"name"</span>:     <span class="green">"David Estevez"</span>,
  <span class="accent">"role"</span>:     <span class="green">"CTO @ Coverfleet"</span>,
  <span class="accent">"based"</span>:    <span class="green">"Miami, FL"</span>,
  <span class="accent">"focus"</span>:    <span class="green">"Architecture · AI · Distributed Systems"</span>,
  <span class="accent">"loves"</span>:    <span class="purple">["math", "clean code", "open source"]</span>,
  <span class="accent">"github"</span>:   <span class="green">"@destbreso"</span>
}`;

    let i = 0;
    const cursor = document.querySelector(".terminal-cursor");

    function typeCmd() {
      if (i < command.length) {
        cmdEl.textContent += command[i];
        i++;
        setTimeout(typeCmd, 60 + Math.random() * 40);
      } else {
        // Hide cursor briefly, show output
        setTimeout(() => {
          if (cursor) cursor.style.display = "none";
          outEl.innerHTML = `<pre>${output}</pre>`;
          outEl.style.opacity = "0";
          outEl.style.transform = "translateY(8px)";
          outEl.style.transition = "opacity .4s ease, transform .4s ease";
          requestAnimationFrame(() => {
            outEl.style.opacity = "1";
            outEl.style.transform = "translateY(0)";
          });
        }, 300);
      }
    }

    // Start after a short delay
    setTimeout(typeCmd, 800);
  }

  // ════════════════════════════════════════════════════════════════
  // 3. Scroll Animations (IntersectionObserver)
  // ════════════════════════════════════════════════════════════════
  function initScrollAnimations() {
    const els = document.querySelectorAll("[data-animate]");
    if (!els.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const delay = parseInt(entry.target.dataset.delay || "0", 10);
            setTimeout(() => entry.target.classList.add("visible"), delay);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -40px 0px" },
    );

    els.forEach((el) => observer.observe(el));
  }

  // ════════════════════════════════════════════════════════════════
  // 4. Navbar (scroll effect + mobile toggle + active link)
  // ════════════════════════════════════════════════════════════════
  function initNavbar() {
    const nav = document.getElementById("navbar");
    const toggle = document.getElementById("nav-toggle");
    const links = document.getElementById("nav-links");
    const navLinks = document.querySelectorAll(".nav-link");
    const sections = document.querySelectorAll("section[id]");

    // Scroll shadow
    window.addEventListener("scroll", () => {
      if (window.scrollY > 20) {
        nav.classList.add("scrolled");
      } else {
        nav.classList.remove("scrolled");
      }
    });

    // Mobile toggle
    if (toggle && links) {
      toggle.addEventListener("click", () => {
        toggle.classList.toggle("open");
        links.classList.toggle("open");
      });

      // Close on link click
      navLinks.forEach((link) => {
        link.addEventListener("click", () => {
          toggle.classList.remove("open");
          links.classList.remove("open");
        });
      });
    }

    // Active link on scroll
    const observerNav = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            navLinks.forEach((link) => {
              link.classList.toggle(
                "active",
                link.getAttribute("href") === `#${entry.target.id}`,
              );
            });
          }
        });
      },
      { threshold: 0.2, rootMargin: "-80px 0px -60% 0px" },
    );

    sections.forEach((s) => observerNav.observe(s));
  }

  // ════════════════════════════════════════════════════════════════
  // 5. Stat Counter Animations
  // ════════════════════════════════════════════════════════════════
  function initCounters() {
    const counters = document.querySelectorAll("[data-count]");
    if (!counters.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            animateCounter(entry.target);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.5 },
    );

    counters.forEach((c) => observer.observe(c));
  }

  function animateCounter(el) {
    const target = parseInt(el.dataset.count, 10);
    const duration = 1500;
    const start = performance.now();

    function tick(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(eased * target);
      if (progress < 1) requestAnimationFrame(tick);
    }

    requestAnimationFrame(tick);
  }

  // ════════════════════════════════════════════════════════════════
  // 6. GitHub Insights (Live API)
  // ════════════════════════════════════════════════════════════════
  const GH_USER = "destbreso";
  const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const ACCENT = "34, 211, 238";

  async function initGitHubInsights() {
    const events = await fetchAllEvents();
    if (!events.length) return;

    const pushEvents = events.filter((e) => e.type === "PushEvent");
    const commits = extractCommits(pushEvents);

    renderDistributionChart(commits, "days");
    initDistributionTabs(commits);
    renderHeatmap(commits);
    renderInsightCards(commits, events);

    // Re-init lucide for new icons
    if (window.lucide) lucide.createIcons();
  }

  // ── Fetch paginated events ──────────────────────────────────
  async function fetchAllEvents() {
    const all = [];
    try {
      for (let page = 1; page <= 10; page++) {
        const res = await fetch(
          `https://api.github.com/users/${GH_USER}/events?per_page=100&page=${page}`,
        );
        if (!res.ok) break;
        const data = await res.json();
        if (!data.length) break;
        all.push(...data);
      }
    } catch (e) {
      console.warn("GitHub API fetch failed:", e);
    }
    return all;
  }

  // ── Extract commit timestamps ───────────────────────────────
  function extractCommits(pushEvents) {
    const commits = [];
    for (const ev of pushEvents) {
      const payload = ev.payload || {};
      const count =
        payload.size || (payload.commits ? payload.commits.length : 1);
      const date = new Date(ev.created_at);
      // Add one entry per commit with the event timestamp
      for (let i = 0; i < count; i++) {
        commits.push(date);
      }
    }
    return commits;
  }

  // ── Distribution Chart ──────────────────────────────────────
  let currentRange = "days";

  function initDistributionTabs(commits) {
    const tabs = document.querySelectorAll("#dist-tabs .chart-tab");
    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        tabs.forEach((t) => t.classList.remove("active"));
        tab.classList.add("active");
        currentRange = tab.dataset.range;
        renderDistributionChart(commits, currentRange);
      });
    });
  }

  function renderDistributionChart(commits, range) {
    const canvas = document.getElementById("distribution-chart");
    const loading = document.getElementById("dist-loading");
    if (!canvas) return;
    if (loading) loading.classList.add("hidden");

    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const W = rect.width;
    const H = rect.height;

    ctx.clearRect(0, 0, W, H);

    const buckets = bucketize(commits, range);
    if (!buckets.length) return;

    const maxVal = Math.max(...buckets.map((b) => b.count), 1);
    const padding = { top: 20, right: 16, bottom: 36, left: 40 };
    const chartW = W - padding.left - padding.right;
    const chartH = H - padding.top - padding.bottom;
    const barW = Math.max(4, (chartW / buckets.length) * 0.7);
    const gap = chartW / buckets.length;

    // Grid lines
    ctx.strokeStyle = "rgba(255,255,255,0.04)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padding.top + (chartH / 4) * i;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(W - padding.right, y);
      ctx.stroke();
    }

    // Y-axis labels
    ctx.fillStyle = "rgba(255,255,255,0.25)";
    ctx.font = "10px 'JetBrains Mono', monospace";
    ctx.textAlign = "right";
    for (let i = 0; i <= 4; i++) {
      const val = Math.round((maxVal / 4) * (4 - i));
      const y = padding.top + (chartH / 4) * i;
      ctx.fillText(val, padding.left - 8, y + 3);
    }

    // Bars
    buckets.forEach((b, i) => {
      const x = padding.left + i * gap + (gap - barW) / 2;
      const barH = (b.count / maxVal) * chartH;
      const y = padding.top + chartH - barH;

      // Bar gradient
      const grad = ctx.createLinearGradient(x, y, x, y + barH);
      grad.addColorStop(0, `rgba(${ACCENT}, 0.9)`);
      grad.addColorStop(1, `rgba(${ACCENT}, 0.3)`);
      ctx.fillStyle = grad;

      // Rounded top
      const r = Math.min(barW / 2, 4);
      ctx.beginPath();
      ctx.moveTo(x + r, y);
      ctx.lineTo(x + barW - r, y);
      ctx.quadraticCurveTo(x + barW, y, x + barW, y + r);
      ctx.lineTo(x + barW, y + barH);
      ctx.lineTo(x, y + barH);
      ctx.lineTo(x, y + r);
      ctx.quadraticCurveTo(x, y, x + r, y);
      ctx.fill();

      // X-axis label (show every Nth)
      const showEvery = buckets.length > 20 ? 5 : buckets.length > 10 ? 3 : 1;
      if (i % showEvery === 0 || i === buckets.length - 1) {
        ctx.fillStyle = "rgba(255,255,255,0.25)";
        ctx.font = "9px 'JetBrains Mono', monospace";
        ctx.textAlign = "center";
        ctx.fillText(b.label, x + barW / 2, H - padding.bottom + 16);
      }
    });
  }

  function bucketize(commits, range) {
    const map = {};
    const now = new Date();

    if (range === "days") {
      // Last 20 days
      for (let i = 19; i >= 0; i--) {
        const d = new Date(now);
        d.setDate(d.getDate() - i);
        const key = d.toISOString().slice(0, 10);
        map[key] = { label: `${d.getMonth() + 1}/${d.getDate()}`, count: 0 };
      }
      commits.forEach((c) => {
        const key = c.toISOString().slice(0, 10);
        if (map[key]) map[key].count++;
      });
    } else if (range === "weeks") {
      // Last 12 weeks
      for (let i = 11; i >= 0; i--) {
        const d = new Date(now);
        d.setDate(d.getDate() - i * 7);
        const weekStart = new Date(d);
        weekStart.setDate(weekStart.getDate() - weekStart.getDay());
        const key = weekStart.toISOString().slice(0, 10);
        if (!map[key]) {
          map[key] = {
            label: `W${getWeekNumber(weekStart)}`,
            count: 0,
            start: weekStart,
          };
        }
      }
      commits.forEach((c) => {
        const ws = new Date(c);
        ws.setDate(ws.getDate() - ws.getDay());
        const key = ws.toISOString().slice(0, 10);
        if (map[key]) map[key].count++;
      });
    } else {
      // Last 6 months
      for (let i = 5; i >= 0; i--) {
        const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
        const key = d.toISOString().slice(0, 7);
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
        map[key] = { label: months[d.getMonth()], count: 0 };
      }
      commits.forEach((c) => {
        const key = c.toISOString().slice(0, 7);
        if (map[key]) map[key].count++;
      });
    }

    return Object.values(map);
  }

  function getWeekNumber(d) {
    const start = new Date(d.getFullYear(), 0, 1);
    const diff = d - start;
    return Math.ceil((diff / 86400000 + start.getDay() + 1) / 7);
  }

  // ── Heatmap (Day × Hour) ───────────────────────────────────
  function renderHeatmap(commits) {
    const grid = document.getElementById("heatmap-grid");
    const yLabels = document.getElementById("heatmap-y-labels");
    const xLabels = document.getElementById("heatmap-x-labels");
    const loading = document.getElementById("heatmap-loading");
    if (!grid) return;
    if (loading) loading.classList.add("hidden");

    // Build 7×24 matrix
    const matrix = Array.from({ length: 7 }, () => Array(24).fill(0));
    commits.forEach((c) => {
      matrix[c.getDay()][c.getHours()]++;
    });

    const maxVal = Math.max(...matrix.flat(), 1);

    // Day labels
    if (yLabels) {
      yLabels.innerHTML = "";
      DAYS.forEach((d) => {
        const s = document.createElement("span");
        s.textContent = d;
        yLabels.appendChild(s);
      });
    }

    // Hour labels (every 2 hours)
    if (xLabels) {
      xLabels.innerHTML = "";
      for (let h = 0; h < 24; h += 2) {
        const s = document.createElement("span");
        s.textContent =
          h === 0 ? "12a" : h < 12 ? `${h}a` : h === 12 ? "12p" : `${h - 12}p`;
        xLabels.appendChild(s);
      }
    }

    // Cells
    grid.innerHTML = "";
    for (let day = 0; day < 7; day++) {
      for (let hour = 0; hour < 24; hour++) {
        const cell = document.createElement("div");
        cell.className = "heatmap-cell";
        const val = matrix[day][hour];
        const intensity = val / maxVal;

        if (val > 0) {
          const alpha = 0.15 + intensity * 0.85;
          cell.style.background = `rgba(${ACCENT}, ${alpha})`;
          cell.style.borderColor = `rgba(${ACCENT}, ${alpha * 0.3})`;
        }

        const hStr =
          hour === 0
            ? "12am"
            : hour < 12
              ? `${hour}am`
              : hour === 12
                ? "12pm"
                : `${hour - 12}pm`;
        cell.setAttribute("data-tip", `${DAYS[day]} ${hStr}: ${val} commits`);
        grid.appendChild(cell);
      }
    }
  }

  // ── Insight Cards ──────────────────────────────────────────
  function renderInsightCards(commits, events) {
    if (!commits.length) return;

    // Peak hour
    const hourCounts = Array(24).fill(0);
    commits.forEach((c) => hourCounts[c.getHours()]++);
    const peakHour = hourCounts.indexOf(Math.max(...hourCounts));
    const peakHourStr =
      peakHour === 0
        ? "12 AM"
        : peakHour < 12
          ? `${peakHour} AM`
          : peakHour === 12
            ? "12 PM"
            : `${peakHour - 12} PM`;
    setText("insight-peak-hour", peakHourStr);

    // Peak day
    const dayCounts = Array(7).fill(0);
    commits.forEach((c) => dayCounts[c.getDay()]++);
    const peakDay = dayCounts.indexOf(Math.max(...dayCounts));
    const fullDays = [
      "Sunday",
      "Monday",
      "Tuesday",
      "Wednesday",
      "Thursday",
      "Friday",
      "Saturday",
    ];
    setText("insight-peak-day", fullDays[peakDay]);

    // Longest streak (consecutive days with commits)
    const daySet = new Set(commits.map((c) => c.toISOString().slice(0, 10)));
    const sortedDays = [...daySet].sort();
    let maxStreak = 1,
      streak = 1;
    for (let i = 1; i < sortedDays.length; i++) {
      const prev = new Date(sortedDays[i - 1]);
      const curr = new Date(sortedDays[i]);
      const diff = (curr - prev) / 86400000;
      if (diff === 1) {
        streak++;
        maxStreak = Math.max(maxStreak, streak);
      } else {
        streak = 1;
      }
    }
    setText("insight-streak", `${maxStreak} days`);

    // Avg commits per week
    const weeks = new Set(
      commits.map((c) => {
        const d = new Date(c);
        return `${d.getFullYear()}-W${getWeekNumber(d)}`;
      }),
    );
    const avgPerWeek = Math.round(commits.length / Math.max(weeks.size, 1));
    setText("insight-velocity", avgPerWeek.toString());

    // Night owl index (% of commits between 10pm-6am)
    const nightCommits = commits.filter((c) => {
      const h = c.getHours();
      return h >= 22 || h < 6;
    });
    const nightPct = Math.round((nightCommits.length / commits.length) * 100);
    setText("insight-night", `${nightPct}%`);

    // Focus score (% of commits in the peak 3-hour window)
    let maxWindow = 0;
    for (let start = 0; start < 24; start++) {
      const windowSum =
        hourCounts[start] +
        hourCounts[(start + 1) % 24] +
        hourCounts[(start + 2) % 24];
      maxWindow = Math.max(maxWindow, windowSum);
    }
    const focusPct = Math.round((maxWindow / commits.length) * 100);
    setText("insight-focus", `${focusPct}%`);
  }

  function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }
})();
