#!/usr/bin/env python3
"""
MATRIX RAIN CONTRIBUTIONS
=========================
Matrix-style code rain that falls and accumulates to form the
contribution graph silhouette. Shorter bars fill and drain first,
creating an organic infinite rain cycle.

Timeline per 20s cycle:
  FILL   0.5s → 2-7s   (rain falls, bars grow bottom-up; short fill fast)
  HOLD   → 9s           (full graph visible, no rain)
  DRAIN  9s → 10.5-15.5s (bars shrink; short columns drain first)
  EMPTY  → 20s          (pause before next cycle)

Uses only SMIL animations (GitHub-safe, no CSS @keyframes).
Generates: dist/matrix-rain.svg
Requires:  GITHUB_TOKEN env variable
"""

import json, os, math, random, urllib.request

USERNAME = "destbreso"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
DIST = "dist"

# Colors
BG       = "#0a0a0f"
BOARD    = "#0d0d14"
BORDER   = "#1e1e2a"
RAIN     = "#00ff41"     # Classic Matrix green
CYAN     = "#22d3ee"
TEXT_DIM = "#55556a"

# Layout
COL_W    = 11
COL_GAP  = 3
COL_STEP = COL_W + COL_GAP
MAX_BAR_H = 130
PAD      = 16
TITLE_H  = 28
LABEL_H  = 18
CYCLE    = 20.0


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
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def safe_keytimes(times):
    """Normalize absolute times to 0..1 keyTimes, ensure strictly increasing."""
    kt = [max(0.0, min(1.0, round(t / CYCLE, 5))) for t in times]
    for i in range(1, len(kt)):
        if kt[i] <= kt[i - 1]:
            kt[i] = round(kt[i - 1] + 0.0001, 5)
    kt[0] = 0
    kt[-1] = 1
    return kt


def generate_svg(cal):
    weeks = cal["weeks"]
    nw = len(weeks)
    total = cal["totalContributions"]

    # Weekly totals
    week_totals = []
    for w in weeks:
        wt = sum(d["contributionCount"] for d in w["contributionDays"])
        week_totals.append(wt)

    max_week = max(week_totals) if week_totals else 1
    if max_week == 0:
        max_week = 1

    norms = [wt / max_week for wt in week_totals]

    # Dimensions
    grid_w = nw * COL_STEP - COL_GAP
    svg_w = PAD * 2 + grid_w
    svg_h = PAD + TITLE_H + MAX_BAR_H + LABEL_H + PAD

    gx = PAD
    gy = PAD + TITLE_H
    base_y = gy + MAX_BAR_H

    s = []
    s.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {svg_w} {svg_h}" width="{svg_w}" height="{svg_h}">'
    )

    # ── Defs ──────────────────────────────────────────────────────
    s.append("<defs>")

    # Rain trail gradient (transparent → green)
    s.append(
        '<linearGradient id="rt" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{RAIN}" stop-opacity="0"/>'
        f'<stop offset="50%" stop-color="{RAIN}" stop-opacity="0.12"/>'
        f'<stop offset="100%" stop-color="{RAIN}" stop-opacity="0.55"/>'
        "</linearGradient>"
    )

    # Bar fill gradient (green top → cyan bottom)
    s.append(
        '<linearGradient id="bf" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{RAIN}" stop-opacity="0.7"/>'
        f'<stop offset="35%" stop-color="#11998e" stop-opacity="0.55"/>'
        f'<stop offset="100%" stop-color="{CYAN}" stop-opacity="0.4"/>'
        "</linearGradient>"
    )

    # Clip paths per column
    for i in range(nw):
        cx = gx + i * COL_STEP
        s.append(
            f'<clipPath id="c{i}">'
            f'<rect x="{cx}" y="{gy}" width="{COL_W}" height="{MAX_BAR_H}"/>'
            f"</clipPath>"
        )

    s.append("</defs>")

    # ── Background ────────────────────────────────────────────────
    s.append(f'<rect width="{svg_w}" height="{svg_h}" rx="10" fill="{BG}"/>')

    # ── Title ─────────────────────────────────────────────────────
    ts = f"font-family:monospace;font-size:11px;font-weight:bold;fill:{RAIN};letter-spacing:2px"
    sub = f"font-family:monospace;font-size:7.5px;fill:{TEXT_DIM}"
    s.append(f'<text x="{PAD}" y="{PAD + 14}" style="{ts}">▸ MATRIX RAIN // CONTRIBUTIONS</text>')
    s.append(f'<text x="{svg_w - PAD}" y="{PAD + 14}" text-anchor="end" style="{sub}">{total:,} commits</text>')

    # ── Board frame ───────────────────────────────────────────────
    s.append(
        f'<rect x="{gx - 2}" y="{gy - 2}" width="{grid_w + 4}" '
        f'height="{MAX_BAR_H + 4}" rx="3" fill="none" stroke="{BORDER}" stroke-opacity="0.4"/>'
    )
    s.append(
        f'<rect x="{gx}" y="{gy}" width="{grid_w}" '
        f'height="{MAX_BAR_H}" rx="2" fill="{BOARD}"/>'
    )

    # ── Ambient background rain (very dim, always-on) ─────────────
    random.seed(42)
    for ai in range(0, nw, 4):
        ax = gx + ai * COL_STEP + COL_W // 2
        a_dur = 2.5 + random.random() * 2.0
        a_delay = random.random() * 4.0
        a_h = 14 + random.randint(0, 18)
        s.append(
            f'<rect x="{ax}" y="{gy}" width="1" height="{a_h}" '
            f'fill="{RAIN}" opacity="0.05">'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0;0 {MAX_BAR_H}" dur="{a_dur:.1f}s" '
            f'begin="{a_delay:.1f}s" repeatCount="indefinite"/>'
            f"</rect>"
        )

    # ── Per-column animations ─────────────────────────────────────
    # Timing design:
    #   fill_end   = 0.5 + (1.5 + h*5.0)  → 2.0s (short) to 7.0s (tall)
    #   hold_end   = 9.0 (fixed — full graph visible from ~7s to 9s)
    #   drain_end  = 9.0 + (1.5 + h*5.0)  → 10.5s (short) to 15.5s (tall)

    for i, (h_norm, wt) in enumerate(zip(norms, week_totals)):
        if wt == 0:
            continue

        x = gx + i * COL_STEP
        bar_h = max(h_norm * MAX_BAR_H, 3)

        fill_start = 0.5
        fill_dur = 1.5 + h_norm * 5.0
        fill_end = fill_start + fill_dur    # 2.0 → 7.0
        hold_end = 9.0                      # fixed for all
        drain_dur = 1.5 + h_norm * 5.0
        drain_end = min(hold_end + drain_dur, CYCLE - 0.5)  # 10.5 → 15.5

        # ── Column group (clipped) ────────────────────────────────
        s.append(f'<g clip-path="url(#c{i})">')

        # ── Rain streams (behind bar) ─────────────────────────────
        num_streams = 2
        for d in range(num_streams):
            dx = x + 2 + d * (COL_W // num_streams)
            stream_h = 14 + (d * 9 + i * 3) % 16
            fall_dur = 1.1 + d * 0.35 + (i % 4) * 0.12
            fall_delay = d * 0.35

            # Rain visible from 0.3 → fill_end, then fades
            r_times = [0, 0.3, max(fill_end - 0.5, 0.5), fill_end, CYCLE]
            r_vals =  [0, 0.65, 0.65, 0, 0]
            r_kt = safe_keytimes(r_times)
            r_kt_s = ";".join(str(k) for k in r_kt)
            r_v_s = ";".join(str(v) for v in r_vals)

            # Trail
            s.append(
                f'<rect x="{dx}" y="{gy}" width="2" height="{stream_h}" '
                f'fill="url(#rt)" opacity="0">'
                f'<animate attributeName="opacity" dur="{CYCLE}s" '
                f'repeatCount="indefinite" keyTimes="{r_kt_s}" values="{r_v_s}"/>'
                f'<animateTransform attributeName="transform" type="translate" '
                f'values="0 0;0 {MAX_BAR_H}" dur="{fall_dur:.2f}s" '
                f'begin="{fall_delay:.1f}s" repeatCount="indefinite"/>'
                f"</rect>"
            )

            # Bright head dot (first stream only)
            if d == 0:
                s.append(
                    f'<rect x="{dx}" y="{gy + stream_h - 3}" width="2" height="3" '
                    f'rx="1" fill="{RAIN}" opacity="0">'
                    f'<animate attributeName="opacity" dur="{CYCLE}s" '
                    f'repeatCount="indefinite" keyTimes="{r_kt_s}" '
                    f'values="{";".join(str(min(v*1.3, 1)) for v in r_vals)}"/>'
                    f'<animateTransform attributeName="transform" type="translate" '
                    f'values="0 0;0 {MAX_BAR_H}" dur="{fall_dur:.2f}s" '
                    f'begin="{fall_delay:.1f}s" repeatCount="indefinite"/>'
                    f"</rect>"
                )

        # ── Fill bar (in front — covers drops at bottom) ──────────
        bar_times = [0, fill_start, fill_end, hold_end, drain_end, CYCLE]
        bar_h_vals = [0, 0, bar_h, bar_h, 0, 0]
        bar_y_vals = [base_y, base_y, base_y - bar_h, base_y - bar_h, base_y, base_y]

        b_kt = safe_keytimes(bar_times)
        b_kt_s = ";".join(str(k) for k in b_kt)
        bh_s = ";".join(f"{v:.1f}" for v in bar_h_vals)
        by_s = ";".join(f"{v:.1f}" for v in bar_y_vals)

        s.append(
            f'<rect x="{x}" y="{base_y}" width="{COL_W}" height="0" '
            f'fill="url(#bf)" rx="1">'
            f'<animate attributeName="height" dur="{CYCLE}s" '
            f'repeatCount="indefinite" keyTimes="{b_kt_s}" values="{bh_s}"/>'
            f'<animate attributeName="y" dur="{CYCLE}s" '
            f'repeatCount="indefinite" keyTimes="{b_kt_s}" values="{by_s}"/>'
            f"</rect>"
        )

        # ── Surface glow (thin bright line at top of bar) ─────────
        glow_opacity = [0, 0, 0.6, 0.6, 0, 0]
        go_s = ";".join(str(v) for v in glow_opacity)
        s.append(
            f'<rect x="{x}" y="{base_y}" width="{COL_W}" height="2" '
            f'fill="{RAIN}" opacity="0" rx="1">'
            f'<animate attributeName="y" dur="{CYCLE}s" '
            f'repeatCount="indefinite" keyTimes="{b_kt_s}" values="{by_s}"/>'
            f'<animate attributeName="opacity" dur="{CYCLE}s" '
            f'repeatCount="indefinite" keyTimes="{b_kt_s}" values="{go_s}"/>'
            f"</rect>"
        )

        s.append("</g>")

    # ── Month labels ──────────────────────────────────────────────
    mo_style = f"font-family:monospace;font-size:6.5px;fill:{TEXT_DIM}"
    MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    seen = {}
    for wi, w in enumerate(weeks):
        if w["contributionDays"]:
            m = int(w["contributionDays"][0]["date"][5:7])
            if m not in seen:
                seen[m] = wi
    for m, wi in seen.items():
        lx = gx + wi * COL_STEP
        ly = base_y + LABEL_H - 4
        s.append(f'<text x="{lx}" y="{ly}" style="{mo_style}">{MONTHS[m]}</text>')

    s.append("</svg>")
    return "\n".join(s)


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
