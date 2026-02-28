#!/usr/bin/env python3
"""
TETRIS CONTRIBUTIONS — SMIL Animated Loop
==========================================
GitHub strips CSS animations from SVGs in README. We use SMIL
(<animate>, <animateTransform>) which GitHub allows.

Loop cycle (20s total):
  Pattern 1 (L→R columns drop in)  →  hold  →  flash+dissolve
  Pattern 2 (center→out radial)    →  hold  →  flash+dissolve  →  repeat

Generates: dist/tetris-contributions.svg
Requires:  GITHUB_TOKEN env variable
"""

import json, os, math, hashlib, datetime, urllib.request

USERNAME = "destbreso"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
DIST = "dist"

# Palette
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

MONTHS = ["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
DAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""]

# Animation timing (seconds)
CYCLE = 20.0


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


def level(count):
    if count == 0: return 0
    if count <= 3: return 1
    if count <= 7: return 2
    if count <= 12: return 3
    return 4


def generate_svg(cal):
    weeks = cal["weeks"]
    total = cal["totalContributions"]
    nw = len(weeks)

    all_days = [d for w in weeks for d in w["contributionDays"]]
    active_days = sum(1 for d in all_days if d["contributionCount"] > 0)
    mx_streak = streak = 0
    for d in all_days:
        if d["contributionCount"] > 0:
            streak += 1
            mx_streak = max(mx_streak, streak)
        else:
            streak = 0

    cells = []
    for wi, w in enumerate(weeks):
        for di, day in enumerate(w["contributionDays"]):
            lv = level(day["contributionCount"])
            if lv > 0:
                cells.append((wi, di, lv))

    # Layout
    pad = 16; title_h = 28; month_h = 14; label_w = 28
    panel_gap = 14; panel_w = 136; panel_extra = 25

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

    # Compute delays: pattern1 (L→R), pattern2 (center→out)
    max_col = max(nw - 1, 1)
    cx = nw / 2.0
    cy = 3.5
    max_dist = math.sqrt(cx**2 + cy**2) or 1

    # Build SVG
    s = []
    s.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {svg_w} {svg_h}" width="{svg_w}" height="{svg_h}">'
    )

    # Defs: scanline pattern
    s.append("<defs>")
    s.append(
        '<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">'
        '<rect width="4" height="2" fill="rgba(255,255,255,0.008)"/></pattern>'
    )
    s.append("</defs>")

    # Background
    s.append(f'<rect width="{svg_w}" height="{svg_h}" rx="10" fill="{BG}"/>')
    s.append(f'<rect width="{svg_w}" height="{svg_h}" rx="10" fill="url(#scan)"/>')

    # Title  (using style attribute instead of class — GitHub strips <style>)
    title_style = f"font-family:monospace;font-size:11px;font-weight:bold;fill:{ACCENT};letter-spacing:2px"
    lbl_style = f"font-family:monospace;font-size:7.5px;fill:{DIM}"
    mo_style = f"font-family:monospace;font-size:7px;fill:{MUTED}"
    sl_style = f"font-family:monospace;font-size:8px;fill:{DIM};letter-spacing:1.5px"
    sv_style = f"font-family:monospace;font-size:14px;font-weight:bold;fill:{TEXT}"

    s.append(f'<text x="{bx}" y="{pad+16}" style="{title_style}">▸ TETRIS CONTRIBUTIONS</text>')

    # Board frame
    s.append(f'<rect x="{bx-3}" y="{by-3}" width="{board_w+6}" height="{board_h+6}" rx="4" fill="none" stroke="{BORDER}"/>')
    s.append(f'<rect x="{bx-1}" y="{by-1}" width="{board_w+2}" height="{board_h+2}" rx="2" fill="{BOARD}"/>')

    # Grid lines
    for r in range(8):
        yl = by + r * STEP
        s.append(f'<line x1="{bx}" y1="{yl}" x2="{bx+board_w-GAP}" y2="{yl}" stroke="{GRID_LN}" stroke-width=".5"/>')
    for c in range(nw + 1):
        xl = bx + c * STEP
        s.append(f'<line x1="{xl}" y1="{by}" x2="{xl}" y2="{by+board_h-GAP}" stroke="{GRID_LN}" stroke-width=".5"/>')

    # Day labels
    for i, name in enumerate(DAY_LABELS):
        if not name: continue
        yl = by + i * STEP + CELL / 2 + 3
        s.append(f'<text x="{bx-5}" y="{yl}" text-anchor="end" style="{lbl_style}">{name}</text>')

    # Month labels
    seen = {}
    for wi, w in enumerate(weeks):
        if w["contributionDays"]:
            m = int(w["contributionDays"][0]["date"][5:7])
            if m not in seen: seen[m] = wi
    for m, wi in seen.items():
        xl = bx + wi * STEP
        yl = by - 4
        s.append(f'<text x="{xl}" y="{yl}" style="{mo_style}">{MONTHS[m]}</text>')

    # ── Animated Tetris blocks (SMIL) ──────────────────────────────
    # Full cycle = 20s, two halves of 10s each.
    # Half timeline (absolute seconds within half):
    #   0→delay       : invisible, held at Y-14
    #   delay→delay+.4: drop in (opacity 0→1, Y -14→0)
    #   delay+.4→7.0  : hold visible at Y 0
    #   7.0→8.0       : fade out (opacity 1→0)
    #   8.0→10.0      : invisible
    # Pattern 1 (L→R) = half 1 [0..10s], Pattern 2 (center→out) = half 2 [10..20s]

    half = CYCLE / 2.0  # 10s

    for col, row, lv in cells:
        x = bx + col * STEP
        y = by + row * STEP

        # Pattern 1 delay: left→right (0 .. 3s)
        d1 = (col / max_col) * 3.0
        # Pattern 2 delay: center→out (0 .. 3s)
        dist = math.sqrt((col - cx)**2 + (row - cy)**2)
        d2 = (dist / max_dist) * 3.0

        # Build merged opacity keyTimes + values for the full 20s cycle
        # Each half produces 6 keyframes, we merge removing the duplicate at boundary
        def opacity_half(delay, offset):
            return (
                [offset, offset + delay, offset + delay + 0.4,
                 offset + 7.0, offset + 8.0, offset + half],
                [0, 0, 1, 1, 0, 0]
            )

        kt1, v1 = opacity_half(d1, 0)
        kt2, v2 = opacity_half(d2, half)
        o_kt = kt1 + kt2[1:]
        o_v  = v1  + v2[1:]
        # Normalize to 0..1
        o_kt = [round(t / CYCLE, 4) for t in o_kt]
        o_kt[-1] = 1.0

        o_kt_str = ";".join(str(k) for k in o_kt)
        o_v_str  = ";".join(str(v) for v in o_v)

        # Build merged translate keyTimes + values
        # translate values are "0 dy" pairs for animateTransform type="translate"
        def translate_half(delay, offset):
            return (
                [offset, offset + delay, offset + delay + 0.4, offset + half],
                ["0 -14", "0 -14", "0 0", "0 0"]
            )

        tkt1, tv1 = translate_half(d1, 0)
        tkt2, tv2 = translate_half(d2, half)
        t_kt = tkt1 + tkt2[1:]
        t_v  = tv1  + tv2[1:]
        t_kt = [round(t / CYCLE, 4) for t in t_kt]
        t_kt[-1] = 1.0

        t_kt_str = ";".join(str(k) for k in t_kt)
        t_v_str  = ";".join(t_v)

        s.append(f'<g opacity="0">')

        # Opacity SMIL
        s.append(
            f'  <animate attributeName="opacity" '
            f'dur="{CYCLE}s" repeatCount="indefinite" '
            f'keyTimes="{o_kt_str}" values="{o_v_str}"/>'
        )
        # Translate SMIL (drop-in effect)
        s.append(
            f'  <animateTransform attributeName="transform" type="translate" '
            f'dur="{CYCLE}s" repeatCount="indefinite" '
            f'keyTimes="{t_kt_str}" values="{t_v_str}"/>'
        )

        # Main block
        s.append(f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{FILL[lv]}"/>')
        # Bevel highlights / shadows
        s.append(f'  <line x1="{x+1}" y1="{y+.5}" x2="{x+CELL-1}" y2="{y+.5}" stroke="{HI[lv]}" stroke-width="1" opacity=".6"/>')
        s.append(f'  <line x1="{x+.5}" y1="{y+1}" x2="{x+.5}" y2="{y+CELL-1}" stroke="{HI[lv]}" stroke-width="1" opacity=".4"/>')
        s.append(f'  <line x1="{x+1}" y1="{y+CELL-.5}" x2="{x+CELL-1}" y2="{y+CELL-.5}" stroke="{LO[lv]}" stroke-width="1" opacity=".6"/>')
        s.append(f'  <line x1="{x+CELL-.5}" y1="{y+1}" x2="{x+CELL-.5}" y2="{y+CELL-1}" stroke="{LO[lv]}" stroke-width="1" opacity=".4"/>')
        s.append("</g>")

    # ── Side panel ─────────────────────────────────────────────────
    s.append(f'<rect x="{px-3}" y="{py-3}" width="{panel_w+6}" height="{panel_h+6}" rx="4" fill="none" stroke="{BORDER}"/>')
    s.append(f'<rect x="{px-1}" y="{py-1}" width="{panel_w+2}" height="{panel_h+2}" rx="2" fill="{BOARD}"/>')

    cx_p = px + panel_w / 2
    sy = py + 14
    s.append(f'<text x="{cx_p}" y="{sy}" text-anchor="middle" style="{sl_style}">SCORE</text>')
    s.append(f'<text x="{cx_p}" y="{sy+20}" text-anchor="middle" style="{sv_style};fill:{ACCENT}">{total:,}</text>')

    sy += 30
    s.append(f'<line x1="{px+12}" y1="{sy}" x2="{px+panel_w-12}" y2="{sy}" stroke="{BORDER}" stroke-width=".5"/>')
    sy += 14
    s.append(f'<text x="{cx_p}" y="{sy}" text-anchor="middle" style="{sl_style}">STREAK</text>')
    s.append(f'<text x="{cx_p}" y="{sy+20}" text-anchor="middle" style="{sv_style}">{mx_streak}</text>')

    sy += 30
    s.append(f'<line x1="{px+12}" y1="{sy}" x2="{px+panel_w-12}" y2="{sy}" stroke="{BORDER}" stroke-width=".5"/>')
    sy += 14
    s.append(f'<text x="{cx_p}" y="{sy}" text-anchor="middle" style="{sl_style}">ACTIVE</text>')
    s.append(f'<text x="{cx_p}" y="{sy+20}" text-anchor="middle" style="{sv_style}">{active_days}</text>')

    # NEXT piece
    today = datetime.date.today().isoformat()
    pidx = int(hashlib.md5(today.encode()).hexdigest()[:4], 16) % 7
    pieces = [
        [(0,0),(1,0),(2,0),(3,0)], [(0,0),(1,0),(0,1),(1,1)],
        [(0,0),(1,0),(2,0),(1,1)], [(1,0),(2,0),(0,1),(1,1)],
        [(0,0),(1,0),(1,1),(2,1)], [(0,0),(0,1),(1,1),(2,1)],
        [(2,0),(0,1),(1,1),(2,1)],
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
        s.append(f'<rect x="{rx}" y="{ry}" width="{ps}" height="{ps}" rx="1.5" fill="{ACCENT}" opacity=".4">')
        s.append(f'  <animate attributeName="opacity" dur="2s" repeatCount="indefinite" values=".3;.7;.3"/>')
        s.append(f'</rect>')

    s.append("</svg>")
    return "\n".join(s)


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
