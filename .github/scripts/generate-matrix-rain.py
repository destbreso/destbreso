#!/usr/bin/env python3
"""
MATRIX RAIN CONTRIBUTIONS — v2
===============================
Full Matrix-style code rain with real characters (Katakana, Latin, digits)
that falls through a tall sky zone and accumulates to reveal the weekly
contribution graph.  The silhouette is ALWAYS visible as a dim ghost
shadow, so the shape is never fully lost.  Rain fills the bars with bright
green, holds, then partially drains — but the ghost residue always remains.

Visual layers (bottom → top):
  1. Background + board
  2. Ghost silhouette (always visible, dim ~0.08)
  3. Fill bars (animated, green→cyan, ghost_h → bar_h → ghost_h)
  4. Rain streams (real characters: bright head, fading tail)
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
BOARD    = "#0d0d14"
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
CHAR_SIZE = 9       # font-size px for characters
CHAR_STEP = 11      # vertical px spacing between chars


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

    # ── board frame (bar zone only) ───────────────────────────
    s.append(
        f'<rect x="{gx - 1}" y="{bar_top - 1}" width="{grid_w + 2}" '
        f'height="{BAR_MAX_H + 2}" rx="2" fill="none" '
        f'stroke="{BORDER}" stroke-opacity="0.25"/>'
    )
    s.append(
        f'<rect x="{gx}" y="{bar_top}" width="{grid_w}" '
        f'height="{BAR_MAX_H}" fill="{BOARD}" rx="1"/>'
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

    # ── main rain streams ─────────────────────────────────────
    # Two rain windows per cycle:
    #   Window-1  0.2 → 8.0   (heavy, fills bars)
    #   Window-2  13.0 → 18.0 (lighter, decorative while draining)
    R1_ON = 0.2;  R1_OFF = 8.0
    R2_ON = 13.0; R2_OFF = 18.0

    for si in range(nw):
        # Skip empty columns most of the time
        if week_totals[si] == 0 and random.random() > 0.25:
            continue

        col_cx = gx + si * COL_STEP + COL_W // 2  # column center-x

        # 1-3 streams per column
        n_streams = 1
        if si % 3 == 0:
            n_streams = 3
        elif si % 2 == 0:
            n_streams = 2

        for sn in range(n_streams):
            slen = random.randint(6, 18)
            fdur = 2.0 + random.random() * 3.0
            xoff = (sn - (n_streams - 1) / 2) * 3.5  # spread around col center
            fdel = sn * 0.6 + random.random() * 1.2
            fdist = content_h + slen * CHAR_STEP

            # Opacity envelope: visible in rain windows, hidden otherwise
            rt = [0, R1_ON, R1_OFF - 0.5, R1_OFF,
                  R2_ON, R2_ON + 0.4, R2_OFF - 0.4, R2_OFF, CYCLE]
            rv = [0, 0.8, 0.8, 0,
                  0, 0.5, 0.5, 0, 0]
            rkt = skt(rt)
            rvs = ";".join(str(v) for v in rv)

            s.append(f'<g opacity="0">')
            s.append(
                f'<animate attributeName="opacity" dur="{CYCLE}s" '
                f'repeatCount="indefinite" keyTimes="{rkt}" values="{rvs}"/>'
            )

            # Falling motion (continuous loop independent of opacity)
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
                    # HEAD — white, glow filter
                    s.append(
                        f'<text x="{px:.1f}" y="{cy}" text-anchor="middle" '
                        f'filter="url(#glo)" '
                        f'style="font-family:monospace;font-size:{CHAR_SIZE}px;'
                        f'fill:#ffffff">{ch}</text>'
                    )
                elif ci >= slen - 3:
                    # Near-head — bright green
                    a = 0.65 + 0.25 * ((ci - (slen - 3)) / 2)
                    s.append(
                        f'<text x="{px:.1f}" y="{cy}" text-anchor="middle" '
                        f'opacity="{a:.2f}" '
                        f'style="font-family:monospace;font-size:{CHAR_SIZE}px;'
                        f'fill:{RAIN_BRT}">{ch}</text>'
                    )
                elif ci >= slen // 2:
                    # Mid — medium green
                    a = 0.2 + 0.35 * ((ci - slen // 2) / max(slen // 2, 1))
                    s.append(
                        f'<text x="{px:.1f}" y="{cy}" text-anchor="middle" '
                        f'opacity="{a:.2f}" '
                        f'style="font-family:monospace;font-size:{CHAR_SIZE}px;'
                        f'fill:{RAIN_MED}">{ch}</text>'
                    )
                else:
                    # Tail — dim
                    a = 0.06 + 0.12 * (ci / max(slen // 2, 1))
                    s.append(
                        f'<text x="{px:.1f}" y="{cy}" text-anchor="middle" '
                        f'opacity="{a:.2f}" '
                        f'style="font-family:monospace;font-size:{CHAR_SIZE}px;'
                        f'fill:{RAIN_DIM}">{ch}</text>'
                    )

            s.append("</g>")  # falling motion
            s.append("</g>")  # opacity envelope

    s.append("</g>")  # rain clip group

    # ═══════════════════════════════════════════════════════════
    #  ANIMATED FILL BARS  (bars never go to 0; ghost_h remains)
    # ═══════════════════════════════════════════════════════════
    # Timeline per bar:
    #   0      → fill_start  : ghost_h  (residue visible)
    #   fill_s → fill_end    : grow to bar_h
    #   fill_e → 11.0        : hold at bar_h
    #   11.0   → drain_end   : shrink to ghost_h
    #   drain  → CYCLE       : stay at ghost_h (ready for next loop)

    for i, (h_norm, wt) in enumerate(zip(norms, week_totals)):
        if wt == 0:
            continue

        x = gx + i * COL_STEP
        bar_h   = max(h_norm * BAR_MAX_H, 4)
        ghost_h = max(bar_h * 0.12, 2)

        fill_s  = 0.5
        fill_d  = 1.8 + h_norm * 5.5
        fill_e  = fill_s + fill_d
        hold_e  = 11.0
        drain_d = 1.5 + h_norm * 4.5
        drain_e = min(hold_e + drain_d, 19.5)

        bt  = [0,       fill_s,  fill_e, hold_e, drain_e, CYCLE]
        bhv = [ghost_h, ghost_h, bar_h,  bar_h,  ghost_h, ghost_h]
        byv = [base_y - ghost_h, base_y - ghost_h,
               base_y - bar_h,   base_y - bar_h,
               base_y - ghost_h, base_y - ghost_h]

        bkt = skt(bt)
        bhs = ";".join(f"{v:.1f}" for v in bhv)
        bys = ";".join(f"{v:.1f}" for v in byv)

        # Filled bar
        s.append(
            f'<rect x="{x}" y="{base_y - ghost_h:.1f}" width="{COL_W}" '
            f'height="{ghost_h:.1f}" fill="url(#bf)" rx="1">'
            f'<animate attributeName="height" dur="{CYCLE}s" '
            f'repeatCount="indefinite" keyTimes="{bkt}" values="{bhs}"/>'
            f'<animate attributeName="y" dur="{CYCLE}s" '
            f'repeatCount="indefinite" keyTimes="{bkt}" values="{bys}"/>'
            f"</rect>"
        )

        # Surface glow line at top of bar
        gov = [0.12, 0.12, 0.7, 0.7, 0.12, 0.12]
        gos = ";".join(str(v) for v in gov)
        s.append(
            f'<rect x="{x}" y="{base_y - ghost_h:.1f}" width="{COL_W}" '
            f'height="2" fill="{RAIN_BRT}" opacity="0.12" rx="1">'
            f'<animate attributeName="y" dur="{CYCLE}s" '
            f'repeatCount="indefinite" keyTimes="{bkt}" values="{bys}"/>'
            f'<animate attributeName="opacity" dur="{CYCLE}s" '
            f'repeatCount="indefinite" keyTimes="{bkt}" values="{gos}"/>'
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
