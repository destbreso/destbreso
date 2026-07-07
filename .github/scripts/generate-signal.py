#!/usr/bin/env python3
"""
One year of commits as a single signal, drawn two ways on ONE shared timeline so
the two moving pulses stay in exact sync (same SVG, same clock, no JavaScript
needed, so it also syncs inside a GitHub README):

  top    -> the weekly commit counts reconstructed through their Fourier
            harmonics as a living waveform (the signal in time)
  bottom -> the same year folded onto a Hilbert space-filling curve, one dot per
            active day, brightest where it was busiest (the signal in space)

Both pulses share dur/begin, and they live in the same <svg> root, so there is a
single animation clock: they cannot drift. Output: dist/signal.svg -> output.
"""

import math
import os
import sys
import json
import urllib.request

USER = os.environ.get("GH_USER", "destbreso")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
PAT = os.environ.get("PAT_TOKEN", "")  # optional PAT: makes the calendar include PRIVATE contributions
OUT = os.path.join("dist", "signal.svg")

BG = "#0b0e14"; GRID = "#141b26"; ACC = "#4dd4e0"
DUR = 12   # one period, shared by BOTH pulses
K = 6      # harmonics kept

# waveform box (top)
WW, WH = 880, 240
WPAD_L, WPAD_R, WPAD_T, WPAD_B = 26, 26, 26, 40
WPLOT = WW - WPAD_L - WPAD_R
WMID = WPAD_T + (WH - WPAD_T - WPAD_B) / 2
WBASE = WH - WPAD_B

# hilbert box (bottom), centered under the waveform
ORDER = 5; N = 1 << ORDER
HB = 300; HSIDE = 250; HOX = (HB - HSIDE) / 2; HOY = (HB - HSIDE) / 2

# canvas
CW = 880
CH = WH + HB + 10
HX = (CW - HB) / 2
HY = WH + 6

CAL_Q = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar { weeks { contributionDays { contributionCount } } }
    }
  }
}"""


def weekly_daily():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": CAL_Q, "variables": {"login": USER}}).encode(),
        headers={"Authorization": "Bearer " + (PAT or TOKEN), "User-Agent": USER + "-signal"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode())
    weeks = d["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    weekly = [sum(day["contributionCount"] for day in w["contributionDays"]) for w in weeks]
    daily = [day["contributionCount"] for w in weeks for day in w["contributionDays"]]
    return (weekly[-52:] if len(weekly) >= 52 else weekly), daily


def dft(sig):
    n = len(sig)
    mean = sum(sig) / n
    s = [v - mean for v in sig]
    comps = []
    for k in range(1, min(K, n // 2) + 1):
        a = sum(s[i] * math.cos(2 * math.pi * k * i / n) for i in range(n)) * 2 / n
        b = sum(s[i] * math.sin(2 * math.pi * k * i / n) for i in range(n)) * 2 / n
        comps.append((k, a, b, math.hypot(a, b)))
    comps.sort(key=lambda c: -c[3])
    return comps, n


def recon(x, comps, n):
    return sum(a * math.cos(2 * math.pi * k * x / n) + b * math.sin(2 * math.pi * k * x / n)
               for (k, a, b, _) in comps)


def poly(points):
    return "M" + " L".join("%.1f %.1f" % p for p in points)


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


def build(weekly, daily):
    if len(weekly) < 4:
        raise RuntimeError("not enough data")
    p = []
    p.append('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
             'viewBox="0 0 %d %d" width="%d" height="%d" role="img" '
             'aria-label="A year of commits as one signal: a Fourier waveform and the same year '
             'folded onto a Hilbert curve, their pulses in sync">' % (CW, CH, CW, CH))
    p.append('<defs>'
             '<pattern id="sig_grid" width="34" height="34" patternUnits="userSpaceOnUse">'
             '<path d="M34 0H0V34" fill="none" stroke="%s" stroke-width="1"/></pattern>'
             '<linearGradient id="sig_area" x1="0" y1="0" x2="0" y2="1">'
             '<stop offset="0" stop-color="%s" stop-opacity="0.20"/>'
             '<stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient>'
             '<filter id="sig_glow" x="-20%%" y="-60%%" width="140%%" height="220%%">'
             '<feGaussianBlur stdDeviation="2.2" result="b"/><feMerge>'
             '<feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
             '</defs>' % (GRID, ACC, ACC))
    p.append('<rect width="%d" height="%d" fill="%s"/>' % (CW, CH, BG))
    p.append('<rect width="%d" height="%d" fill="url(#sig_grid)" opacity="0.5"/>' % (CW, CH))
    p.append('<rect x="0.5" y="0.5" width="%d" height="%d" fill="none" stroke="#1b2330"/>' % (CW - 1, CH - 1))

    # ---------- waveform (top) ----------
    n = len(weekly)
    comps, Nn = dft(weekly)
    SAMP = 300
    xs = [i * Nn / (SAMP - 1) for i in range(SAMP)]
    rvals = [recon(x, comps, Nn) for x in xs]
    peak = max((abs(v) for v in rvals), default=1) or 1
    amp = (WH - WPAD_T - WPAD_B) / 2 * 0.82 / peak

    def WX(x):
        return WPAD_L + (x / Nn) * WPLOT

    def WY(v):
        return WMID - v * amp

    curve = poly([(WX(x), WY(v)) for x, v in zip(xs, rvals)])
    harm = []
    for (k, a, b, _) in comps[:3]:
        harm.append(poly([(WX(x), WY(a * math.cos(2 * math.pi * k * x / Nn) + b * math.sin(2 * math.pi * k * x / Nn)))
                          for x in xs]))
    smax = max(weekly) or 1
    bw = WPLOT / n
    g = ['<g>']
    g.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#22303f" stroke-width="1" stroke-dasharray="2 4"/>'
             % (WPAD_L, WMID, WW - WPAD_R, WMID))
    for i, v in enumerate(weekly):
        bh = (v / smax) * (WBASE - WMID - 6)
        x = WPAD_L + i * bw
        g.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="1" fill="#1c2836" opacity="0.5"/>'
                 % (x + bw * 0.18, WBASE - bh, bw * 0.64, bh))
    for hp in harm:
        g.append('<path d="%s" fill="none" stroke="%s" stroke-width="1" opacity="0.28"/>' % (hp, ACC))
    g.append('<path d="%s L %.1f %.1f L %.1f %.1f Z" fill="url(#sig_area)"/>' % (curve, WX(Nn), WMID, WX(0), WMID))
    g.append('<path id="sig_wave" d="%s" fill="none" stroke="%s" stroke-width="2" '
             'stroke-linecap="round" stroke-linejoin="round" opacity="0.55"/>' % (curve, ACC))
    g.append('<path d="%s" fill="none" stroke="%s" stroke-width="2.6" stroke-linecap="round" '
             'pathLength="1000" stroke-dasharray="46 1000" filter="url(#sig_glow)">'
             '<animate attributeName="stroke-dashoffset" values="1046;-46" dur="%ds" begin="0s" '
             'repeatCount="indefinite" calcMode="linear"/></path>' % (curve, ACC, DUR))
    g.append('<circle r="3.4" fill="#eafcff" filter="url(#sig_glow)">'
             '<animateMotion dur="%ds" begin="0s" repeatCount="indefinite">'
             '<mpath xlink:href="#sig_wave"/></animateMotion></circle>' % DUR)
    g.append('</g>')
    p.extend(g)

    # ---------- hilbert (bottom), same clock ----------
    cell = HSIDE / (N - 1)
    pts = []
    for dd in range(N * N):
        gx, gy = d2xy(N, dd)
        pts.append((HOX + gx * cell, HOY + gy * cell))
    hcurve = "M" + " L".join("%.1f %.1f" % pt for pt in pts)
    m = len(daily)
    h = ['<g transform="translate(%.1f,%.1f)">' % (HX, HY)]
    h.append('<path id="sig_hil" d="%s" fill="none" stroke="%s" stroke-width="1.2" '
             'stroke-linecap="round" stroke-linejoin="round" opacity="0.34"/>' % (hcurve, ACC))
    if m:
        cmax = max(daily) or 1
        for i in range(m):
            c = daily[i]
            if c <= 0:
                continue
            pos = round(i * (len(pts) - 1) / max(1, m - 1))
            x, y = pts[pos]
            frac = c / cmax
            h.append('<circle cx="%.1f" cy="%.1f" r="%.2f" fill="%s" opacity="%.2f" filter="url(#sig_glow)"/>'
                     % (x, y, 1.2 + frac * 3.4, ACC, 0.4 + frac * 0.55))
    h.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.8" stroke-linecap="round" '
             'pathLength="1000" stroke-dasharray="30 1000" opacity="0.95" filter="url(#sig_glow)">'
             '<animate attributeName="stroke-dashoffset" values="1030;-30" dur="%ds" begin="0s" '
             'repeatCount="indefinite" calcMode="linear"/></path>' % (hcurve, ACC, DUR))
    h.append('<circle r="2.6" fill="#eafcff" filter="url(#sig_glow)">'
             '<animateMotion dur="%ds" begin="0s" repeatCount="indefinite">'
             '<mpath xlink:href="#sig_hil"/></animateMotion></circle>' % DUR)
    h.append('</g>')
    p.extend(h)

    p.append('</svg>')
    return "".join(p)


def main():
    os.makedirs("dist", exist_ok=True)
    try:
        weekly, daily = weekly_daily()
        svg = build(weekly, daily)
    except Exception as ex:
        print("signal generation failed:", ex, file=sys.stderr)
        return 0
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print("wrote", OUT, "weeks=", len(weekly))
    return 0


if __name__ == "__main__":
    sys.exit(main())
