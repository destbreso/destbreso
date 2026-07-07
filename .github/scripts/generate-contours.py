#!/usr/bin/env python3
"""
The terrain of a year, drawn as contour lines.

The daily contribution calendar is a height field (52 weeks x 7 days). Marching
squares, the classic algorithm for isolines, traces level sets through it, so the
result is a topographic map of the year: closed loops around the busy peaks, open
lines across the quiet flats, with a highlight that sweeps up through elevations.
Math (level sets of a scalar field) meeting the algorithm that extracts them.
Output: dist/contours.svg -> output branch.
"""

import json
import os
import sys
import urllib.request

USER = os.environ.get("GH_USER", "destbreso")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.path.join("dist", "contours.svg")

BG = "#0b0e14"; GRID = "#141b26"; ACC = "#4dd4e0"
W, H = 880, 220
PAD = 20
LEVELS = 6
UP = 4  # bilinear upsample factor

CAL_Q = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar { weeks { contributionDays { contributionCount weekday } } }
    }
  }
}"""

# marching squares: case -> list of edge pairs to connect. Edges: T,R,B,L.
CASES = {
    0: [], 15: [],
    1: [("L", "B")], 2: [("B", "R")], 3: [("L", "R")], 4: [("T", "R")],
    6: [("T", "B")], 7: [("L", "T")], 8: [("T", "L")], 9: [("T", "B")],
    11: [("T", "R")], 12: [("L", "R")], 13: [("B", "R")], 14: [("L", "B")],
    5: [("L", "T"), ("B", "R")], 10: [("T", "R"), ("L", "B")],
}


def field():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": CAL_Q, "variables": {"login": USER}}).encode(),
        headers={"Authorization": "Bearer " + TOKEN, "User-Agent": USER + "-contours"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode())
    weeks = d["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"][-52:]
    # grid[row=weekday 0..6][col=week]
    grid = [[0] * len(weeks) for _ in range(7)]
    for c, w in enumerate(weeks):
        for day in w["contributionDays"]:
            grid[day["weekday"]][c] = day["contributionCount"]
    return grid


def bilinear(grid, up):
    rows, cols = len(grid), len(grid[0])
    GH, GW = (rows - 1) * up + 1, (cols - 1) * up + 1
    out = [[0.0] * GW for _ in range(GH)]
    for j in range(GH):
        fy = j / up
        y0 = min(int(fy), rows - 1)
        y1 = min(y0 + 1, rows - 1)
        ty = fy - y0
        for i in range(GW):
            fx = i / up
            x0 = min(int(fx), cols - 1)
            x1 = min(x0 + 1, cols - 1)
            tx = fx - x0
            a = grid[y0][x0] * (1 - tx) + grid[y0][x1] * tx
            b = grid[y1][x0] * (1 - tx) + grid[y1][x1] * tx
            out[j][i] = a * (1 - ty) + b * ty
    return out


def build_svg(grid):
    g = bilinear(grid, UP)
    GH, GW = len(g), len(g[0])
    plotW, plotH = W - 2 * PAD, H - 2 * PAD
    vmax = max(max(row) for row in g) or 1

    def X(i):
        return PAD + i / (GW - 1) * plotW

    def Y(j):
        return PAD + j / (GH - 1) * plotH

    def cross(v0, v1, i0, i1, t):
        denom = (v1 - v0)
        a = 0.5 if denom == 0 else (t - v0) / denom
        a = max(0.0, min(1.0, a))
        return i0 + (i1 - i0) * a

    thresholds = [vmax * (k + 0.5) / LEVELS for k in range(LEVELS)]
    level_paths = [[] for _ in range(LEVELS)]
    for j in range(GH - 1):
        for i in range(GW - 1):
            tl, tr = g[j][i], g[j][i + 1]
            bl, br = g[j + 1][i], g[j + 1][i + 1]
            for li, t in enumerate(thresholds):
                c = (8 if tl >= t else 0) + (4 if tr >= t else 0) + (2 if br >= t else 0) + (1 if bl >= t else 0)
                for (ea, eb) in CASES.get(c, []):
                    pa = edge_point(ea, i, j, tl, tr, br, bl, t, cross)
                    pb = edge_point(eb, i, j, tl, tr, br, bl, t, cross)
                    level_paths[li].append("M%.1f %.1f L%.1f %.1f" % (X(pa[0]), Y(pa[1]), X(pb[0]), Y(pb[1])))

    p = []
    p.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
             'role="img" aria-label="A year of commits as a contour map via marching squares">' % (W, H, W, H))
    p.append('<defs><pattern id="g" width="34" height="34" patternUnits="userSpaceOnUse">'
             '<path d="M34 0H0V34" fill="none" stroke="%s" stroke-width="1"/></pattern>'
             '<filter id="glow" x="-10%%" y="-40%%" width="120%%" height="180%%">'
             '<feGaussianBlur stdDeviation="1.4" result="b"/><feMerge>'
             '<feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>' % GRID)
    p.append('<rect width="%d" height="%d" fill="%s"/>' % (W, H, BG))
    p.append('<rect width="%d" height="%d" fill="url(#g)" opacity="0.5"/>' % (W, H))
    p.append('<rect x="0.5" y="0.5" width="%d" height="%d" fill="none" stroke="#1b2330"/>' % (W - 1, H - 1))
    dur = 9
    for li in range(LEVELS):
        d = " ".join(level_paths[li])
        if not d:
            continue
        base = 0.18 + li / LEVELS * 0.22   # higher elevations a touch brighter
        begin = li / LEVELS * dur
        p.append('<g fill="none" stroke="%s" stroke-width="%.2f" stroke-linecap="round" opacity="%.2f" filter="url(#glow)">'
                 '<path d="%s"/>'
                 '<animate attributeName="opacity" values="%.2f;%.2f;1;%.2f;%.2f" keyTimes="0;0.12;0.2;0.32;1" '
                 'dur="%ds" begin="%.2fs" repeatCount="indefinite"/></g>'
                 % (ACC, 1.0 + li * 0.12, base, d, base, base, base, base, dur, begin))
    p.append('</svg>')
    return "".join(p)


def edge_point(edge, i, j, tl, tr, br, bl, t, cross):
    if edge == "T":
        return (cross(tl, tr, i, i + 1, t), j)
    if edge == "B":
        return (cross(bl, br, i, i + 1, t), j + 1)
    if edge == "L":
        return (i, cross(tl, bl, j, j + 1, t))
    return (i + 1, cross(tr, br, j, j + 1, t))  # "R"


def main():
    os.makedirs("dist", exist_ok=True)
    try:
        svg = build_svg(field())
    except Exception as ex:
        print("contours generation failed:", ex, file=sys.stderr)
        return 0
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
