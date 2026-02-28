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
})();
