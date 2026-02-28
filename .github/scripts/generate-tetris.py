#!/usr/bin/env python3
"""
TETRIS CONTRIBUTIONS — Animated Loop
=====================================
The contribution graph visualised as a Tetris board that builds itself,
flashes a CRT line-clear, dissolves, then rebuilds with a completely
different drop pattern — forever.

Pattern 1  →  columns left-to-right  (classic Tetris feel)
Pattern 2  →  center-outward spiral  (radial burst)

Generates: dist/tetris-contributions.svg
Requires:  GITHUB_TOKEN env variable
"""

import json
import os
import urllib.request
import hashlib
import datetime
import math

# ── Config ─────────────────────────────────────────────────────────
USERNAME = "destbreso"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
DIST = "dist"

# ── Palette ────────────────────────────────────────────────────────
BG      = "#0a0a0f"
BOARD   = "#0d0d14"
GRID_LN = "#151522"
BORDER  = "#1e1e2a"
ACCENT  = "#22d3ee"
TEXT    = "#e0e0e8"
DIM     = "#55556a"
MUTED   = "#8888a0"

FILL = [None, "#0b3d4a", "#0f6577", "#1590a5", "#22d3ee"]
HI   = [None, "#18606e", "#1c8497", "#29b0d8", "#60e8f7"]
LO   = [None, "#052228", "#073845", "#0b5f70", "#127a92"]

CELL = 13
GAP  = 2
STEP = CELL + GAP

MONTHS = [
    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]
DAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""]

# animation total loop duration (seconds)
CYCLE = 16


# ── Data fetching ──────────────────────────────────────────────────
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


def level(count):
    if count == 0:
        return 0
    if count <= 3:
        return 1
    if count <= 7:
        return 2
    if count <= 12:
        return 3
    return 4


# ── Helper: quantise to nearest step value ─────────────────────────
def _q(val, step=3):
    return int(round(val / step) * step)


# ── SVG generation ─────────────────────────────────────────────────
def generate_svg(cal):
    weeks = cal["weeks"]
    total = cal["totalContributions"]
    nw = len(weeks)

    # Stats
    all_days = [d for w in weeks for d in w["contributionDays"]]
    active_days = sum(1 for d in all_days if d["contributionCount"] > 0)
    mx_streak = streak = 0
    for d in all_days:
        if d["contributionCount"] > 0:
            streak += 1
            mx_streak = max(mx_streak, streak)
        else:
            streak = 0

    # Active cells
    cells = []
    for wi, w in enumerate(weeks):
        for di, day in enumerate(w["contributionDays"]):
            lv = level(day["contributionCount"])
            if lv > 0:
                cells.append((wi, di, lv))

    # ── Layout ─────────────────────────────────────────────────────
    pad = 16
    title_h = 28
    month_h = 14
    label_w = 28
    panel_gap = 14
    panel_w = 136
    panel_extra = 25

    board_w = nw * STEP
    board_h = 7 * STEP
    panel_h = board_h + panel_extra
    content_h = max(board_h, panel_h)

    svg_w = pad + label_w + board_w + panel_gap + panel_w + pad
    svg_h = pad + title_h + month_h + content_h + pad

    bx = pad + label_w
    by = pad + title_h + month_h
    px = bx + board_w + panel_gap
    py = by

    # ── Compute per-cell animation keyframe groups ─────────────────
    # Pattern 1: left → right  (t1 ∈ [2%, 32%])
    # Pattern 2: centre → out  (t2 ∈ [52%, 82%])
    max_col = max(nw - 1, 1)
    centre_x = nw / 2
    centre_y = 3.5
    max_dist = math.sqrt(centre_x ** 2 + centre_y ** 2) or 1

    kf_groups: dict[tuple[int, int], list] = {}
    cell_kf: dict[tuple[int, int], str] = {}

    for col, row, lv in cells:
        t1_raw = 2 + (col / max_col) * 30
        dist = math.sqrt((col - centre_x) ** 2 + (row - centre_y) ** 2)
        t2_raw = 52 + (dist / max_dist) * 30

        t1 = max(2, min(_q(t1_raw), 32))
        t2 = max(52, min(_q(t2_raw), 82))

        key = (t1, t2)
        kf_groups.setdefault(key, []).append((col, row, lv))
        cell_kf[(col, row)] = f"kf_{t1}_{t2}"

    # ── Start building SVG ─────────────────────────────────────────
    s = []
    s.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {svg_w} {svg_h}" width="{svg_w}" height="{svg_h}">'
    )

    # Defs
    s.append("<defs>")
    s.append(
        '<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">'
        '<rect width="4" height="2" fill="rgba(255,255,255,0.008)"/>'
        "</pattern>"
    )
    s.append("</defs>")

    # ── Styles + per-group keyframes ───────────────────────────────
    s.append("<style>")
    s.append(
        f"text{{font-family:'Courier New','Lucida Console',monospace}}"
        f".t{{font-size:11px;font-weight:bold;fill:{ACCENT};letter-spacing:2px}}"
        f".lbl{{font-size:7.5px;fill:{DIM}}}"
        f".mo{{font-size:7px;fill:{MUTED}}}"
        f".sl{{font-size:8px;fill:{DIM};letter-spacing:1.5px}}"
        f".sv{{font-size:14px;font-weight:bold;fill:{TEXT}}}"
        f".sa{{fill:{ACCENT}}}"
    )
    s.append(
        f"@keyframes blink{{0%,100%{{opacity:.3}}50%{{opacity:.7}}}}"
        f".nb{{animation:blink 2s ease-in-out infinite}}"
    )

    # Generate one @keyframes per (t1, t2) group
    # Timeline (% of CYCLE):
    #   Build-1: t1 → t1+3  (drop in)
    #   Hold-1 : until 37%
    #   Clear-1: 37→40 (flash) 40→46 (fade)
    #   Pause  : 46→50
    #   Build-2: t2 → t2+3  (drop in)
    #   Hold-2 : until 87%
    #   Clear-2: 87→90 (flash) 90→96 (fade)
    #   Pause  : 96→100
    for (t1, t2) in sorted(kf_groups.keys()):
        name = f"kf_{t1}_{t2}"
        t1e = min(t1 + 3, 35)
        t2e = min(t2 + 3, 85)
        s.append(f"@keyframes {name}{{")
        s.append(f"0%{{opacity:0;transform:translateY(-14px)}}")
        s.append(f"{t1}%{{opacity:0;transform:translateY(-14px)}}")
        s.append(f"{t1e}%{{opacity:1;transform:translateY(0)}}")
        s.append(f"37%{{opacity:1;transform:translateY(0)}}")
        s.append(f"40%{{opacity:1;transform:translateY(0);filter:brightness(2.5)}}")
        s.append(f"46%{{opacity:0;transform:translateY(0)}}")
        s.append(f"50%{{opacity:0;transform:translateY(-14px)}}")
        s.append(f"{t2}%{{opacity:0;transform:translateY(-14px)}}")
        s.append(f"{t2e}%{{opacity:1;transform:translateY(0)}}")
        s.append(f"87%{{opacity:1;transform:translateY(0)}}")
        s.append(f"90%{{opacity:1;transform:translateY(0);filter:brightness(2.5)}}")
        s.append(f"96%{{opacity:0;transform:translateY(0)}}")
        s.append(f"100%{{opacity:0;transform:translateY(-14px)}}")
        s.append("}")

    s.append("</style>")

    # ── Background + scanline overlay ──────────────────────────────
    s.append(f'<rect width="{svg_w}" height="{svg_h}" rx="10" fill="{BG}"/>')
    s.append(f'<rect width="{svg_w}" height="{svg_h}" rx="10" fill="url(#scan)"/>')

    # ── Title ──────────────────────────────────────────────────────
    s.append(
        f'<text x="{bx}" y="{pad + 16}" class="t">'
        f"▸ TETRIS CONTRIBUTIONS</text>"
    )

    # ── Board frame (CRT double border) ────────────────────────────
    s.append(
        f'<rect x="{bx - 3}" y="{by - 3}" width="{board_w + 6}" '
        f'height="{board_h + 6}" rx="4" fill="none" stroke="{BORDER}"/>'
    )
    s.append(
        f'<rect x="{bx - 1}" y="{by - 1}" width="{board_w + 2}" '
        f'height="{board_h + 2}" rx="2" fill="{BOARD}"/>'
    )

    # Grid lines
    for r in range(8):
        y = by + r * STEP
        s.append(
            f'<line x1="{bx}" y1="{y}" x2="{bx + board_w - GAP}" '
            f'y2="{y}" stroke="{GRID_LN}" stroke-width=".5"/>'
        )
    for c in range(nw + 1):
        x = bx + c * STEP
        s.append(
            f'<line x1="{x}" y1="{by}" x2="{x}" '
            f'y2="{by + board_h - GAP}" stroke="{GRID_LN}" stroke-width=".5"/>'
        )

    # Day labels
    for i, name in enumerate(DAY_LABELS):
        if not name:
            continue
        y = by + i * STEP + CELL / 2 + 3
        s.append(
            f'<text x="{bx - 5}" y="{y}" text-anchor="end" class="lbl">'
            f"{name}</text>"
        )

    # Month labels
    seen: dict[int, int] = {}
    for wi, w in enumerate(weeks):
        if w["contributionDays"]:
            m = int(w["contributionDays"][0]["date"][5:7])
            if m not in seen:
                seen[m] = wi
    for m, wi in seen.items():
        x = bx + wi * STEP
        y = by - 4
        s.append(f'<text x="{x}" y="{y}" class="mo">{MONTHS[m]}</text>')

    # ── Animated Tetris blocks ─────────────────────────────────────
    for col, row, lv in cells:
        x = bx + col * STEP
        y = by + row * STEP
        anim = cell_kf[(col, row)]

        s.append(
            f'<g style="animation:{anim} {CYCLE}s ease-in-out infinite">'
        )
        # main block
        s.append(
            f'  <rect x="{x}" y="{y}" width="{CELL}" '
            f'height="{CELL}" rx="2" fill="{FILL[lv]}"/>'
        )
        # bevel highlights / shadows
        s.append(
            f'  <line x1="{x+1}" y1="{y+.5}" x2="{x+CELL-1}" '
            f'y2="{y+.5}" stroke="{HI[lv]}" stroke-width="1" opacity=".6"/>'
        )
        s.append(
            f'  <line x1="{x+.5}" y1="{y+1}" x2="{x+.5}" '
            f'y2="{y+CELL-1}" stroke="{HI[lv]}" stroke-width="1" opacity=".4"/>'
        )
        s.append(
            f'  <line x1="{x+1}" y1="{y+CELL-.5}" x2="{x+CELL-1}" '
            f'y2="{y+CELL-.5}" stroke="{LO[lv]}" stroke-width="1" opacity=".6"/>'
        )
        s.append(
            f'  <line x1="{x+CELL-.5}" y1="{y+1}" x2="{x+CELL-.5}" '
            f'y2="{y+CELL-1}" stroke="{LO[lv]}" stroke-width="1" opacity=".4"/>'
        )
        s.append("</g>")

    # ── Side panel (static) ────────────────────────────────────────
    s.append(
        f'<rect x="{px-3}" y="{py-3}" width="{panel_w+6}" '
        f'height="{panel_h+6}" rx="4" fill="none" stroke="{BORDER}"/>'
    )
    s.append(
        f'<rect x="{px-1}" y="{py-1}" width="{panel_w+2}" '
        f'height="{panel_h+2}" rx="2" fill="{BOARD}"/>'
    )

    cx_p = px + panel_w / 2

    # SCORE
    sy = py + 14
    s.append(
        f'<text x="{cx_p}" y="{sy}" text-anchor="middle" class="sl">'
        f"SCORE</text>"
    )
    s.append(
        f'<text x="{cx_p}" y="{sy+20}" text-anchor="middle" '
        f'class="sv sa">{total:,}</text>'
    )

    sy += 30
    s.append(
        f'<line x1="{px+12}" y1="{sy}" x2="{px+panel_w-12}" '
        f'y2="{sy}" stroke="{BORDER}" stroke-width=".5"/>'
    )

    # STREAK
    sy += 14
    s.append(
        f'<text x="{cx_p}" y="{sy}" text-anchor="middle" class="sl">'
        f"STREAK</text>"
    )
    s.append(
        f'<text x="{cx_p}" y="{sy+20}" text-anchor="middle" '
        f'class="sv">{mx_streak}</text>'
    )

    sy += 30
    s.append(
        f'<line x1="{px+12}" y1="{sy}" x2="{px+panel_w-12}" '
        f'y2="{sy}" stroke="{BORDER}" stroke-width=".5"/>'
    )

    # ACTIVE
    sy += 14
    s.append(
        f'<text x="{cx_p}" y="{sy}" text-anchor="middle" class="sl">'
        f"ACTIVE</text>"
    )
    s.append(
        f'<text x="{cx_p}" y="{sy+20}" text-anchor="middle" '
        f'class="sv">{active_days}</text>'
    )

    # ── NEXT piece (decorative, bottom of panel) ───────────────────
    today = datetime.date.today().isoformat()
    pidx = int(hashlib.md5(today.encode()).hexdigest()[:4], 16) % 7
    pieces = [
        [(0, 0), (1, 0), (2, 0), (3, 0)],
        [(0, 0), (1, 0), (0, 1), (1, 1)],
        [(0, 0), (1, 0), (2, 0), (1, 1)],
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(2, 0), (0, 1), (1, 1), (2, 1)],
    ]
    piece = pieces[pidx]
    ps, pg = 8, 1
    pstep = ps + pg
    pw = (max(p[0] for p in piece) + 1) * pstep
    ph = (max(p[1] for p in piece) + 1) * pstep
    ox = cx_p - pw / 2
    oy = py + panel_h - ph - 6

    for dx, dy in piece:
        rx = ox + dx * pstep
        ry = oy + dy * pstep
        s.append(
            f'<rect x="{rx}" y="{ry}" width="{ps}" height="{ps}" '
            f'rx="1.5" fill="{ACCENT}" opacity=".4" class="nb"/>'
        )

    s.append("</svg>")
    return "\n".join(s)


# ── Main ───────────────────────────────────────────────────────────
def main():
    os.makedirs(DIST, exist_ok=True)
    cal = fetch_contributions()
    svg = generate_svg(cal)
    path = os.path.join(DIST, "tetris-contributions.svg")
    with open(path, "w") as f:
        f.write(svg)
    print(f"✅ {path} — {cal['totalContributions']} contributions")


if __name__ == "__main__":
    main()
