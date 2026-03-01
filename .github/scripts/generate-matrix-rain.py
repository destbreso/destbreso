#!/usr/bin/env python3
"""
MATRIX RAIN CONTRIBUTIONS — v3 (push / pull)
=============================================
Continuous Matrix-style code rain with a push/pull equilibrium:
  - Bars naturally DRAIN over time (gravity)
  - Rain FILLS the bars as drops fall on them
  - Rain intensity ∝ emptiness: more empty → heavier rain; full → faint rain
  - No interruptions, no on/off windows — smooth organic animation

Visual layers (bottom → top):
  1. Background + board
  2. Ghost silhouette (always visible, dim ~0.08)
  3. Fill bars (animated wave: quick fill / slow drain, cycles per column)
  4. Rain streams (real characters, opacity inverse of bar fill)
  5. Surface glow line
  6. Title + labels

SMIL-only anims (GitHub-safe, no CSS @keyframes / <style>).
Generates: dist/matrix-rain.svg
Requires:  GITHUB_TOKEN env variable
"""

import json, os, math, random, urllib.request

USERNAME = "destbreso"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
DIST = "dist"

# ── Palette ───────────────────────────────────────────────────
BG       = "#0a0a0f"
BORDER   = "#1e1e2a"
RAIN_BRT = "#00ff41"    # Bright head / fill
RAIN_MED = "#00cc33"    # Mid trail
RAIN_DIM = "#007722"    # Faint tail
CYAN     = "#22d3ee"
TEXT_DIM = "#55556a"
GHOST_C  = "#00ff41"    # Ghost silhouette colour

# ── Layout ────────────────────────────────────────────────────
COL_W     = 10
COL_GAP   = 3
COL_STEP  = COL_W + COL_GAP
SKY_H     = 120          # tall sky for rain to fall through
BAR_MAX_H = 120          # max contribution bar height
PAD       = 16
TITLE_H   = 28
LABEL_H   = 20
CYCLE     = 24.0         # full animation cycle (s)

# Character pool: Katakana + digits + XML-safe ASCII symbols
# NOTE: <, >, & are excluded — they break SVG/XML parsing
CHARS = list(
    "アイウエオカキクケコサシスセソタチツテトナニヌネノ"
    "ハヒフヘホマミムメモヤユヨラリルレロワヲン"
    "0123456789"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "{}[]|/:;=+-*#$%?!"
)
CHAR_SIZE = 6      # font-size px for characters
CHAR_STEP = 9      # vertical px spacing between chars


def xml_esc(ch):
    """Escape a character for safe SVG/XML text content."""
    if ch == '&':  return '&amp;'
    if ch == '<':  return '&lt;'
    if ch == '>':  return '&gt;'
    if ch == '"': return '&quot;'
    return ch


# ── helpers ───────────────────────────────────────────────────
def fetch_contributions():
    query = (
        '{ user(login: "%s") { contributionsCollection '
        "{ contributionCalendar { totalContributions "
        "weeks { contributionDays { contributionCount date weekday } } } } } }"
        % USERNAME
    )
    body = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def skt(times):
    """Normalize absolute seconds → 0..1 keyTimes (strictly increasing)."""
    kt = [max(0.0, min(1.0, round(t / CYCLE, 5))) for t in times]
    for i in range(1, len(kt)):
        if kt[i] <= kt[i - 1]:
            kt[i] = round(kt[i - 1] + 0.00005, 6)
    kt[0] = 0.0
    kt[-1] = 1.0
    return ";".join(str(k) for k in kt)


def gen_column_wave(norm, col_idx, n_samples=48):
    """Generate a smooth fill/drain wave for one column.

    Returns list of (t, v) where t ∈ [0,1] and v ∈ [0,1].
    v = fill fraction (0 = ghost residue, 1 = full bar).
    Loops seamlessly.

    Tall columns (high norm) are *slower* to fill: peak is compressed so
    they never jump to 100% instantly, and the fill ramp is more gradual.
    """
    rng = random.Random(col_idx * 7 + 13)
    n_bumps = max(2, min(4, round(2 + norm * 2)))

    # Compress peak for tall columns: norm=1→peak≈0.55, norm=0.2→peak≈0.18
    # This means tall bars fill to ~55 % of their max height per bump,
    # requiring multiple bumps to accumulate, which looks far more natural.
    raw_peak = norm + rng.uniform(-0.04, 0.04)
    peak = max(0.12, min(0.6, raw_peak * 0.55 + 0.02))

    bumps = []
    for b in range(n_bumps):
        c = (b + 0.5) / n_bumps + rng.uniform(-0.06, 0.06)
        c = c % 1.0
        w = 0.85 / n_bumps
        bumps.append((c, w))

    dt = 1.0 / n_samples
    pts = []
    for i in range(n_samples + 1):
        t = min(i * dt, 1.0)
        val = 0.0
        for (c, w) in bumps:
            d = t - c
            if d > 0.5:  d -= 1.0
            if d < -0.5: d += 1.0
            fw = w * 0.30          # fill ramp  (30 % of bump width — slower)
            dw = w * 0.70          # drain ramp (70 %)
            if -fw < d <= 0:
                frac = 1.0 - abs(d) / fw
                val = max(val, peak * frac ** 0.7)   # gentler curve
            elif 0 < d < dw:
                frac = d / dw
                val = max(val, peak * (1.0 - frac) ** 2.0)
        pts.append((t, val))

    pts[-1] = (1.0, pts[0][1])          # seamless loop
    return pts


# ── SVG generator ─────────────────────────────────────────────
def generate_svg(cal):
    weeks = cal["weeks"]
    nw = len(weeks)
    total = cal["totalContributions"]

    week_totals = [
        sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks
    ]
    max_week = max(week_totals) if week_totals else 1
    if max_week == 0:
        max_week = 1
    norms = [wt / max_week for wt in week_totals]

    # ── Pre-compute fill/drain wave per column ────────────────
    col_waves = []
    for ci, (n, wt) in enumerate(zip(norms, week_totals)):
        if wt == 0:
            col_waves.append(None)
        else:
            col_waves.append(gen_column_wave(n, ci))

    # ── dimensions ────────────────────────────────────────────
    grid_w    = nw * COL_STEP - COL_GAP
    content_h = SKY_H + BAR_MAX_H
    svg_w     = PAD * 2 + grid_w
    svg_h     = PAD + TITLE_H + content_h + LABEL_H + PAD

    gx       = PAD                       # left edge of grid
    sky_top  = PAD + TITLE_H             # top of sky zone
    bar_top  = sky_top + SKY_H           # top of bar zone
    base_y   = bar_top + BAR_MAX_H       # bottom of bars

    random.seed(42)
    s = []

    # ── root SVG ──────────────────────────────────────────────
    s.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {svg_w} {svg_h}" width="{svg_w}" height="{svg_h}">'
    )

    # ── defs ──────────────────────────────────────────────────
    s.append("<defs>")

    # Fill gradient for bars
    s.append(
        '<linearGradient id="bf" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%"   stop-color="{RAIN_BRT}" stop-opacity="0.75"/>'
        f'<stop offset="40%"  stop-color="#11998e" stop-opacity="0.5"/>'
        f'<stop offset="100%" stop-color="{CYAN}" stop-opacity="0.35"/>'
        "</linearGradient>"
    )

    # Glow filter (head chars)
    s.append(
        '<filter id="glo" x="-80%" y="-80%" width="260%" height="260%">'
        '<feGaussianBlur stdDeviation="2.5" result="b"/>'
        "<feMerge>"
        '<feMergeNode in="b"/><feMergeNode in="SourceGraphic"/>'
        "</feMerge></filter>"
    )

    # Clip for entire rain + bars area
    s.append(
        f'<clipPath id="rc">'
        f'<rect x="{gx}" y="{sky_top}" width="{grid_w}" height="{content_h}"/>'
        f"</clipPath>"
    )

    s.append("</defs>")

    # ── background ────────────────────────────────────────────
    s.append(f'<rect width="{svg_w}" height="{svg_h}" rx="10" fill="{BG}"/>')

    # ── title ─────────────────────────────────────────────────
    ts  = f"font-family:monospace;font-size:11px;font-weight:bold;fill:{RAIN_BRT};letter-spacing:2px"
    sub = f"font-family:monospace;font-size:7.5px;fill:{TEXT_DIM}"
    s.append(
        f'<text x="{PAD}" y="{PAD + 14}" style="{ts}">'
        f"▸ MATRIX RAIN // CONTRIBUTIONS</text>"
    )
    s.append(
        f'<text x="{svg_w - PAD}" y="{PAD + 14}" text-anchor="end" '
        f'style="{sub}">{total:,} commits</text>'
    )

    # ── bar zone background (same base color as sky, subtle animated tint) ─
    # Thin border — very faint
    s.append(
        f'<rect x="{gx - 1}" y="{bar_top - 1}" width="{grid_w + 2}" '
        f'height="{BAR_MAX_H + 2}" rx="2" fill="none" '
        f'stroke="{BORDER}" stroke-opacity="0.15"/>'
    )
    # Static base – same color as main BG so sky & bar zone are seamless
    s.append(
        f'<rect x="{gx}" y="{bar_top}" width="{grid_w}" '
        f'height="{BAR_MAX_H}" fill="{BG}" rx="1"/>'
    )
    # Subtle animated overlay: faint green tint that breathes
    s.append(
        f'<rect x="{gx}" y="{bar_top}" width="{grid_w}" '
        f'height="{BAR_MAX_H}" fill="{RAIN_DIM}" opacity="0.025" rx="1">'
        f'<animate attributeName="opacity" values="0.025;0.055;0.025" '
        f'dur="8s" repeatCount="indefinite"/>'
        f'</rect>'
    )

    # ── ghost silhouette (always visible) ─────────────────────
    for i, (h_norm, wt) in enumerate(zip(norms, week_totals)):
        if wt == 0:
            continue
        x  = gx + i * COL_STEP
        gh = max(h_norm * BAR_MAX_H, 2)
        gy = base_y - gh
        s.append(
            f'<rect x="{x}" y="{gy:.1f}" width="{COL_W}" '
            f'height="{gh:.1f}" rx="1" fill="{GHOST_C}" opacity="0.07"/>'
        )

    # ═══════════════════════════════════════════════════════════
    #  RAIN STREAMS  (clipped to sky+bar area)
    # ═══════════════════════════════════════════════════════════
    s.append(f'<g clip-path="url(#rc)">')

    # ── ambient background streams (very faint, always looping) ─
    for ai in range(0, nw, 3):
        ax = gx + ai * COL_STEP + COL_W // 2
        slen = random.randint(5, 12)
        fdur = 3.0 + random.random() * 4.0
        fdel = random.random() * 6.0
        fdist = content_h + slen * CHAR_STEP

        s.append(f'<g opacity="0.055">')
        s.append(
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0;0 {fdist}" dur="{fdur:.1f}s" '
            f'begin="{fdel:.1f}s" repeatCount="indefinite"/>'
        )
        for ci in range(slen):
            ch = xml_esc(random.choice(CHARS))
            cy = sky_top - slen * CHAR_STEP + ci * CHAR_STEP
            op = 0.25 + 0.75 * (ci / max(slen - 1, 1))
            s.append(
                f'<text x="{ax}" y="{cy}" text-anchor="middle" '
                f'style="font-family:monospace;font-size:{CHAR_SIZE}px;'
                f'fill:{RAIN_DIM}" opacity="{op:.2f}">{ch}</text>'
            )
        s.append("</g>")

    # ── main rain streams (continuous · opacity ∝ emptiness) ─
    for si in range(nw):
        wave = col_waves[si]
        # Skip empty columns most of the time
        if wave is None and random.random() > 0.25:
            continue

        col_cx = gx + si * COL_STEP + COL_W // 2

        # 1-3 streams per column
        n_streams = 1
        if si % 3 == 0:
            n_streams = 3
        elif si % 2 == 0:
            n_streams = 2

        # Column-level opacity animated from the DERIVATIVE of the wave:
        #   filling (dv > 0) → rain is heavy (high opacity)
        #   draining (dv ≤ 0) → rain fades out (low opacity)
        # This creates a direct causal feel: rain pours → bar rises.
        if wave is not None:
            o_kt_parts = []
            o_vs_parts = []
            for wi_idx in range(len(wave)):
                t_now, v_now = wave[wi_idx]
                t_nxt, v_nxt = wave[(wi_idx + 1) % len(wave)]
                dv = v_nxt - v_now
                if dv > 0:
                    # Filling phase: opacity proportional to fill speed
                    op = min(0.85, 0.25 + dv * 12.0)
                elif dv < 0:
                    # Draining phase: dim rain
                    op = max(0.04, 0.12 + dv * 2.0)
                else:
                    op = 0.08
                o_kt_parts.append(f"{t_now:.5f}")
                o_vs_parts.append(f"{op:.3f}")
            o_kt = ";".join(o_kt_parts)
            o_vs = ";".join(o_vs_parts)
            s.append(f'<g>')
            s.append(
                f'<animate attributeName="opacity" dur="{CYCLE}s" '
                f'repeatCount="indefinite" keyTimes="{o_kt}" values="{o_vs}"/>'
            )
        else:
            s.append(f'<g opacity="0.04">')

        for sn in range(n_streams):
            slen = random.randint(6, 18)
            fdur = 2.0 + random.random() * 3.0
            xoff = (sn - (n_streams - 1) / 2) * 3.5
            fdel = sn * 0.6 + random.random() * 1.2
            fdist = content_h + slen * CHAR_STEP

            # Falling motion (always looping — never pauses)
            s.append("<g>")
            s.append(
                f'<animateTransform attributeName="transform" type="translate" '
                f'values="0 0;0 {fdist}" dur="{fdur:.2f}s" '
                f'begin="{fdel:.1f}s" repeatCount="indefinite"/>'
            )

            for ci in range(slen):
                ch = xml_esc(random.choice(CHARS))
                cy = sky_top - slen * CHAR_STEP + ci * CHAR_STEP
                px = col_cx + xoff

                if ci == slen - 1:
                    s.append(
                        f'<text x="{px:.1f}" y="{cy}" text-anchor="middle" '
                        f'filter="url(#glo)" '
                        f'style="font-family:monospace;font-size:{CHAR_SIZE}px;'
                        f'fill:#ffffff">{ch}</text>'
                    )
                elif ci >= slen - 3:
                    a = 0.65 + 0.25 * ((ci - (slen - 3)) / 2)
                    s.append(
                        f'<text x="{px:.1f}" y="{cy}" text-anchor="middle" '
                        f'opacity="{a:.2f}" '
                        f'style="font-family:monospace;font-size:{CHAR_SIZE}px;'
                        f'fill:{RAIN_BRT}">{ch}</text>'
                    )
                elif ci >= slen // 2:
                    a = 0.2 + 0.35 * ((ci - slen // 2) / max(slen // 2, 1))
                    s.append(
                        f'<text x="{px:.1f}" y="{cy}" text-anchor="middle" '
                        f'opacity="{a:.2f}" '
                        f'style="font-family:monospace;font-size:{CHAR_SIZE}px;'
                        f'fill:{RAIN_MED}">{ch}</text>'
                    )
                else:
                    a = 0.06 + 0.12 * (ci / max(slen // 2, 1))
                    s.append(
                        f'<text x="{px:.1f}" y="{cy}" text-anchor="middle" '
                        f'opacity="{a:.2f}" '
                        f'style="font-family:monospace;font-size:{CHAR_SIZE}px;'
                        f'fill:{RAIN_DIM}">{ch}</text>'
                    )

            s.append("</g>")  # falling motion

        s.append("</g>")  # column opacity group

    s.append("</g>")  # rain clip group

    # ═══════════════════════════════════════════════════════════
    #  ANIMATED FILL BARS  (continuous wave: rain fills ↔ drain)
    # ═══════════════════════════════════════════════════════════
    for i, (h_norm, wt) in enumerate(zip(norms, week_totals)):
        if wt == 0:
            continue
        wave = col_waves[i]
        if wave is None:
            continue

        x = gx + i * COL_STEP
        bar_h   = max(h_norm * BAR_MAX_H, 4)
        ghost_h = max(bar_h * 0.12, 2)

        # Convert wave fill fractions → pixel heights / y positions
        h_kt = ";".join(f"{t:.5f}" for t, _ in wave)
        h_vs = ";".join(
            f"{ghost_h + (bar_h - ghost_h) * v:.1f}" for _, v in wave
        )
        y_vs = ";".join(
            f"{base_y - (ghost_h + (bar_h - ghost_h) * v):.1f}"
            for _, v in wave
        )

        init_h = ghost_h + (bar_h - ghost_h) * wave[0][1]
        init_y = base_y - init_h

        # Filled bar
        s.append(
            f'<rect x="{x}" y="{init_y:.1f}" width="{COL_W}" '
            f'height="{init_h:.1f}" fill="url(#bf)" rx="1">'
            f'<animate attributeName="height" dur="{CYCLE}s" '
            f'repeatCount="indefinite" keyTimes="{h_kt}" values="{h_vs}"/>'
            f'<animate attributeName="y" dur="{CYCLE}s" '
            f'repeatCount="indefinite" keyTimes="{h_kt}" values="{y_vs}"/>'
            f"</rect>"
        )

        # Surface glow line (brighter when bar is fuller)
        glow_vs = ";".join(f"{0.08 + 0.62 * v:.3f}" for _, v in wave)
        s.append(
            f'<rect x="{x}" y="{init_y:.1f}" width="{COL_W}" '
            f'height="2" fill="{RAIN_BRT}" opacity="0.08" rx="1">'
            f'<animate attributeName="y" dur="{CYCLE}s" '
            f'repeatCount="indefinite" keyTimes="{h_kt}" values="{y_vs}"/>'
            f'<animate attributeName="opacity" dur="{CYCLE}s" '
            f'repeatCount="indefinite" keyTimes="{h_kt}" values="{glow_vs}"/>'
            f"</rect>"
        )

    # ── month labels ──────────────────────────────────────────
    mo_style = f"font-family:monospace;font-size:6.5px;fill:{TEXT_DIM}"
    MONTHS = [
        "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]
    seen = {}
    for wi, w in enumerate(weeks):
        if w["contributionDays"]:
            m = int(w["contributionDays"][0]["date"][5:7])
            if m not in seen:
                seen[m] = wi
    for m, wi in seen.items():
        lx = gx + wi * COL_STEP
        ly = base_y + LABEL_H - 6
        s.append(f'<text x="{lx}" y="{ly}" style="{mo_style}">{MONTHS[m]}</text>')

    s.append("</svg>")
    return "\n".join(s)


# ── entry point ───────────────────────────────────────────────
def main():
    os.makedirs(DIST, exist_ok=True)
    cal = fetch_contributions()
    svg = generate_svg(cal)
    path = os.path.join(DIST, "matrix-rain.svg")
    with open(path, "w") as f:
        f.write(svg)
    print(f"✅ {path} — {cal['totalContributions']} contributions")


if __name__ == "__main__":
    main()
