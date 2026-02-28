#!/usr/bin/env python3
"""
TETRIS CONTRIBUTIONS
====================
A Tetris-styled GitHub contribution graph — the first of its kind.
Each contribution day becomes a beveled Tetris block with drop animation,
scanline CRT overlay, and a retro score panel.

Generates: dist/tetris-contributions.svg
Requires:  GITHUB_TOKEN env variable
"""

import json
import os
import urllib.request
import hashlib
import datetime

# ── Config ─────────────────────────────────────────────────────────
USERNAME = "destbreso"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
DIST = "dist"

# ── Palette ────────────────────────────────────────────────────────
BG = "#0a0a0f"
BOARD = "#0d0d14"
GRID_LN = "#151522"
BORDER = "#1e1e2a"
ACCENT = "#22d3ee"
TEXT = "#e0e0e8"
DIM = "#55556a"
MUTED = "#8888a0"

#                 empty       L1         L2         L3         L4
FILL = [None, "#0b3d4a", "#0f6577", "#1590a5", "#22d3ee"]
HI   = [None, "#18606e", "#1c8497", "#29b0d8", "#60e8f7"]   # bevel highlight
LO   = [None, "#052228", "#073845", "#0b5f70", "#127a92"]   # bevel shadow

CELL = 13
GAP = 2
STEP = CELL + GAP  # 15

MONTHS = [
    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]
DAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""]


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


# ── SVG generation ─────────────────────────────────────────────────
def generate_svg(cal):
    weeks = cal["weeks"]
    total = cal["totalContributions"]
    nw = len(weeks)

    # ── Stats ──────────────────────────────────────────────────────
    all_days = [d for w in weeks for d in w["contributionDays"]]
    active_days = sum(1 for d in all_days if d["contributionCount"] > 0)

    mx_streak = streak = 0
    for d in all_days:
        if d["contributionCount"] > 0:
            streak += 1
            mx_streak = max(mx_streak, streak)
        else:
            streak = 0

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

    bx = pad + label_w  # board X origin
    by = pad + title_h + month_h  # board Y origin
    px = bx + board_w + panel_gap  # panel X origin
    py = by  # panel Y origin

    s = []

    # ── SVG open ───────────────────────────────────────────────────
    s.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {svg_w} {svg_h}" width="{svg_w}" height="{svg_h}">'
    )

    # ── Defs ───────────────────────────────────────────────────────
    s.append("<defs>")
    s.append(
        '<filter id="glow">'
        '<feGaussianBlur stdDeviation="2" result="g"/>'
        "<feMerge><feMergeNode in=\"g\"/>"
        '<feMergeNode in="SourceGraphic"/></feMerge></filter>'
    )
    s.append(
        '<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">'
        '<rect width="4" height="2" fill="rgba(255,255,255,0.008)"/>'
        "</pattern>"
    )
    s.append("</defs>")

    # ── Styles ─────────────────────────────────────────────────────
    s.append("<style>")
    s.append(
        f"text {{ font-family: 'Courier New','Lucida Console',monospace; }}\n"
        f".t {{ font-size:11px; font-weight:bold; fill:{ACCENT}; letter-spacing:2px; }}\n"
        f".lbl {{ font-size:7.5px; fill:{DIM}; }}\n"
        f".mo {{ font-size:7px; fill:{MUTED}; }}\n"
        f".sl {{ font-size:8px; fill:{DIM}; letter-spacing:1.5px; }}\n"
        f".sv {{ font-size:14px; font-weight:bold; fill:{TEXT}; }}\n"
        f".sa {{ fill:{ACCENT}; }}\n"
        f"@keyframes drop {{"
        f" 0%{{opacity:0;transform:translateY(-14px);}}"
        f" 70%{{opacity:1;transform:translateY(1px);}}"
        f" 100%{{opacity:1;transform:translateY(0);}}"
        f"}}\n"
        f".blk {{ animation: drop .35s ease-out both; }}\n"
        f"@keyframes blink {{ 0%,100%{{opacity:.3;}} 50%{{opacity:.7;}} }}\n"
        f".nb {{ animation: blink 2s ease-in-out infinite; }}"
    )
    s.append("</style>")

    # ── Background + scanline ──────────────────────────────────────
    s.append(f'<rect width="{svg_w}" height="{svg_h}" rx="10" fill="{BG}"/>')
    s.append(
        f'<rect width="{svg_w}" height="{svg_h}" rx="10" fill="url(#scan)"/>'
    )

    # ── Title ──────────────────────────────────────────────────────
    s.append(f'<text x="{bx}" y="{pad + 16}" class="t">▸ TETRIS CONTRIBUTIONS</text>')

    # ── Board frame (double line CRT border) ───────────────────────
    s.append(
        f'<rect x="{bx - 3}" y="{by - 3}" width="{board_w + 6}" '
        f'height="{board_h + 6}" rx="4" fill="none" stroke="{BORDER}"/>'
    )
    s.append(
        f'<rect x="{bx - 1}" y="{by - 1}" width="{board_w + 2}" '
        f'height="{board_h + 2}" rx="2" fill="{BOARD}"/>'
    )

    # ── Grid lines (faint) ─────────────────────────────────────────
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

    # ── Day labels (left) ──────────────────────────────────────────
    for i, name in enumerate(DAY_LABELS):
        if not name:
            continue
        y = by + i * STEP + CELL / 2 + 3
        s.append(
            f'<text x="{bx - 5}" y="{y}" text-anchor="end" class="lbl">{name}</text>'
        )

    # ── Month labels (top) ─────────────────────────────────────────
    seen = {}
    for wi, w in enumerate(weeks):
        if w["contributionDays"]:
            m = int(w["contributionDays"][0]["date"][5:7])
            if m not in seen:
                seen[m] = wi
    for m, wi in seen.items():
        x = bx + wi * STEP
        y = by - 4
        s.append(f'<text x="{x}" y="{y}" class="mo">{MONTHS[m]}</text>')

    # ── Tetris blocks ──────────────────────────────────────────────
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week["contributionDays"]):
            lv = level(day["contributionCount"])
            if lv == 0:
                continue

            x = bx + wi * STEP
            y = by + di * STEP
            delay = wi * 0.04

            s.append(f'<g class="blk" style="animation-delay:{delay:.2f}s">')
            # Main block
            s.append(
                f'  <rect x="{x}" y="{y}" width="{CELL}" '
                f'height="{CELL}" rx="2" fill="{FILL[lv]}"/>'
            )
            # Bevel: top highlight
            s.append(
                f'  <line x1="{x + 1}" y1="{y + .5}" '
                f'x2="{x + CELL - 1}" y2="{y + .5}" '
                f'stroke="{HI[lv]}" stroke-width="1" opacity=".6"/>'
            )
            # Bevel: left highlight
            s.append(
                f'  <line x1="{x + .5}" y1="{y + 1}" '
                f'x2="{x + .5}" y2="{y + CELL - 1}" '
                f'stroke="{HI[lv]}" stroke-width="1" opacity=".4"/>'
            )
            # Bevel: bottom shadow
            s.append(
                f'  <line x1="{x + 1}" y1="{y + CELL - .5}" '
                f'x2="{x + CELL - 1}" y2="{y + CELL - .5}" '
                f'stroke="{LO[lv]}" stroke-width="1" opacity=".6"/>'
            )
            # Bevel: right shadow
            s.append(
                f'  <line x1="{x + CELL - .5}" y1="{y + 1}" '
                f'x2="{x + CELL - .5}" y2="{y + CELL - 1}" '
                f'stroke="{LO[lv]}" stroke-width="1" opacity=".4"/>'
            )
            s.append("</g>")

    # ── Side panel ─────────────────────────────────────────────────
    s.append(
        f'<rect x="{px - 3}" y="{py - 3}" width="{panel_w + 6}" '
        f'height="{panel_h + 6}" rx="4" fill="none" stroke="{BORDER}"/>'
    )
    s.append(
        f'<rect x="{px - 1}" y="{py - 1}" width="{panel_w + 2}" '
        f'height="{panel_h + 2}" rx="2" fill="{BOARD}"/>'
    )

    cx = px + panel_w / 2

    # SCORE
    sy = py + 14
    s.append(f'<text x="{cx}" y="{sy}" text-anchor="middle" class="sl">SCORE</text>')
    s.append(
        f'<text x="{cx}" y="{sy + 20}" text-anchor="middle" '
        f'class="sv sa">{total:,}</text>'
    )

    # Divider
    sy += 30
    s.append(
        f'<line x1="{px + 12}" y1="{sy}" x2="{px + panel_w - 12}" '
        f'y2="{sy}" stroke="{BORDER}" stroke-width=".5"/>'
    )

    # STREAK
    sy += 14
    s.append(
        f'<text x="{cx}" y="{sy}" text-anchor="middle" class="sl">STREAK</text>'
    )
    s.append(
        f'<text x="{cx}" y="{sy + 20}" text-anchor="middle" '
        f'class="sv">{mx_streak}</text>'
    )

    # Divider
    sy += 30
    s.append(
        f'<line x1="{px + 12}" y1="{sy}" x2="{px + panel_w - 12}" '
        f'y2="{sy}" stroke="{BORDER}" stroke-width=".5"/>'
    )

    # ACTIVE DAYS
    sy += 14
    s.append(
        f'<text x="{cx}" y="{sy}" text-anchor="middle" class="sl">ACTIVE</text>'
    )
    s.append(
        f'<text x="{cx}" y="{sy + 20}" text-anchor="middle" '
        f'class="sv">{active_days}</text>'
    )

    # ── "NEXT" piece (decorative, bottom of panel) ─────────────────
    # Pick a piece deterministically from the date
    today = datetime.date.today().isoformat()
    pidx = int(hashlib.md5(today.encode()).hexdigest()[:4], 16) % 7
    pieces = [
        [(0, 0), (1, 0), (2, 0), (3, 0)],  # I
        [(0, 0), (1, 0), (0, 1), (1, 1)],  # O
        [(0, 0), (1, 0), (2, 0), (1, 1)],  # T
        [(1, 0), (2, 0), (0, 1), (1, 1)],  # S
        [(0, 0), (1, 0), (1, 1), (2, 1)],  # Z
        [(0, 0), (0, 1), (1, 1), (2, 1)],  # L
        [(2, 0), (0, 1), (1, 1), (2, 1)],  # J
    ]
    piece = pieces[pidx]
    ps = 8  # piece cell size
    pg = 1  # piece gap
    pstep = ps + pg
    max_px = max(p[0] for p in piece) + 1
    max_py = max(p[1] for p in piece) + 1
    pw = max_px * pstep
    ph = max_py * pstep
    ox = cx - pw / 2
    oy = py + panel_h - ph - 6

    for dx, dy in piece:
        rx = ox + dx * pstep
        ry = oy + dy * pstep
        s.append(
            f'<rect x="{rx}" y="{ry}" width="{ps}" height="{ps}" '
            f'rx="1.5" fill="{ACCENT}" opacity=".4" class="nb"/>'
        )

    # ── Close ──────────────────────────────────────────────────────
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
