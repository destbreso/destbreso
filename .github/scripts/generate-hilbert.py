#!/usr/bin/env python3
"""
The year, folded onto a Hilbert curve.

A Hilbert curve is a space-filling fractal built by recursion: it threads every
cell of a 2^n x 2^n grid on one continuous line while keeping neighbors in time
close in space. Here the 365 days of the year are laid along it in order, so the
single line IS the year, folded; the brightest points are the most active days,
and a pulse traces the traversal. Math (a space-filling curve) meeting the
algorithm that draws it. Output: dist/hilbert.svg -> output branch.
"""

import json
import os
import sys
import urllib.request

USER = os.environ.get("GH_USER", "destbreso")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.path.join("dist", "hilbert.svg")

BG = "#0b0e14"; GRID = "#141b26"; ACC = "#4dd4e0"
ORDER = 5              # 32 x 32 = 1024 cells
N = 1 << ORDER
W, H = 340, 300
SIDE = 240
OX = (W - SIDE) / 2
OY = (H - SIDE) / 2

CAL_Q = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar { weeks { contributionDays { contributionCount } } }
    }
  }
}"""


def daily_counts():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": CAL_Q, "variables": {"login": USER}}).encode(),
        headers={"Authorization": "Bearer " + TOKEN, "User-Agent": USER + "-hilbert"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode())
    weeks = d["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [day["contributionCount"] for w in weeks for day in w["contributionDays"]]


def d2xy(n, d):
    x = y = 0
    t = d
    s = 1
    while s < n:
        rx = 1 & (t // 2)
        ry = 1 & (t ^ rx)
        if ry == 0:
            if rx == 1:
                x = s - 1 - x
                y = s - 1 - y
            x, y = y, x
        x += s * rx
        y += s * ry
        t //= 4
        s *= 2
    return x, y


def build_svg(counts):
    cell = SIDE / (N - 1)
    pts = []
    for d in range(N * N):
        gx, gy = d2xy(N, d)
        pts.append((OX + gx * cell, OY + gy * cell))
    curve = "M" + " L".join("%.1f %.1f" % p for p in pts)

    # place each day at its proportional position along the curve; keep the busiest
    m = len(counts)
    dots = []
    if m:
        cmax = max(counts) or 1
        ranked = sorted(range(m), key=lambda i: -counts[i])[:44]
        for i in ranked:
            pos = round(i * (len(pts) - 1) / max(1, m - 1))
            x, y = pts[pos]
            r = 1.4 + (counts[i] / cmax) * 3.2
            dots.append('<circle cx="%.1f" cy="%.1f" r="%.2f" fill="%s" opacity="0.9" filter="url(#glow)"/>'
                        % (x, y, r, ACC))

    p = []
    p.append('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
             'viewBox="0 0 %d %d" width="%d" height="%d" role="img" '
             'aria-label="A year of commits folded onto a Hilbert space-filling curve">' % (W, H, W, H))
    p.append('<defs>'
             '<pattern id="g" width="30" height="30" patternUnits="userSpaceOnUse">'
             '<path d="M30 0H0V30" fill="none" stroke="%s" stroke-width="1"/></pattern>'
             '<filter id="glow" x="-60%%" y="-60%%" width="220%%" height="220%%">'
             '<feGaussianBlur stdDeviation="1.8" result="b"/><feMerge>'
             '<feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
             '</defs>' % GRID)
    p.append('<rect width="%d" height="%d" fill="%s"/>' % (W, H, BG))
    p.append('<rect width="%d" height="%d" fill="url(#g)" opacity="0.5"/>' % (W, H))
    p.append('<rect x="0.5" y="0.5" width="%d" height="%d" fill="none" stroke="#1b2330"/>' % (W - 1, H - 1))
    # faint full curve + the moving pen path
    p.append('<path id="hil" d="%s" fill="none" stroke="%s" stroke-width="1.1" '
             'stroke-linecap="round" stroke-linejoin="round" opacity="0.28"/>' % (curve, ACC))
    p.extend(dots)
    # traveling pulse along the traversal (time)
    p.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.8" stroke-linecap="round" '
             'pathLength="1000" stroke-dasharray="30 1000" opacity="0.95" filter="url(#glow)">'
             '<animate attributeName="stroke-dashoffset" values="1030;-30" dur="9s" '
             'repeatCount="indefinite" calcMode="linear"/></path>' % (curve, ACC))
    p.append('<circle r="2.6" fill="#eafcff" filter="url(#glow)">'
             '<animateMotion dur="9s" repeatCount="indefinite"><mpath xlink:href="#hil"/></animateMotion></circle>')
    p.append('</svg>')
    return "".join(p)


def main():
    os.makedirs("dist", exist_ok=True)
    try:
        svg = build_svg(daily_counts())
    except Exception as ex:
        print("hilbert generation failed:", ex, file=sys.stderr)
        return 0
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
