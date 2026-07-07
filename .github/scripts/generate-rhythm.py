#!/usr/bin/env python3
"""
Commit rhythm: render a year of commits as a signal, then reconstruct it through
its Fourier harmonics and draw it as a living waveform with a light pulse that
travels along the curve.

Why this and not a matrix rain: it says exactly one thing, and it is true. The
weekly commit counts are a real time series; its dominant harmonics are computed
by DFT; the curve is their sum. A mathematician's lens on his own data, in the
same blueprint-cyan language as the rest of the profile. Output:
dist/commit-rhythm.svg, pushed to the `output` branch by the deploy step.
"""

import math
import os
import sys
import json
import urllib.request

USER = os.environ.get("GH_USER", "destbreso")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.path.join("dist", "commit-rhythm.svg")
K = 6  # harmonics kept

# palette (matches the profile redesign)
BG = "#0b0e14"; GRID = "#141b26"; INK = "#9198a1"; FAINT = "#5c6675"; ACC = "#4dd4e0"

W, H = 880, 220
PAD_L, PAD_R, PAD_T, PAD_B = 26, 26, 30, 44
PLOT_W = W - PAD_L - PAD_R
MIDY = PAD_T + (H - PAD_T - PAD_B) / 2
BASE = H - PAD_B  # baseline for the raw bars

CAL_Q = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar { weeks { contributionDays { contributionCount } } }
    }
  }
}"""


def weekly_signal():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": CAL_Q, "variables": {"login": USER}}).encode(),
        headers={"Authorization": "Bearer " + TOKEN, "User-Agent": USER + "-rhythm"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode())
    weeks = d["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    sig = [sum(day["contributionCount"] for day in w["contributionDays"]) for w in weeks]
    return sig[-52:] if len(sig) >= 52 else sig


def dft(sig):
    n = len(sig)
    mean = sum(sig) / n
    s = [v - mean for v in sig]
    comps = []
    for k in range(1, min(K, n // 2) + 1):
        a = sum(s[i] * math.cos(2 * math.pi * k * i / n) for i in range(n)) * 2 / n
        b = sum(s[i] * math.sin(2 * math.pi * k * i / n) for i in range(n)) * 2 / n
        comps.append((k, a, b, math.hypot(a, b)))
    comps.sort(key=lambda c: -c[3])  # strongest harmonics first
    return comps, n


def recon(x, comps, n):
    return sum(a * math.cos(2 * math.pi * k * x / n) + b * math.sin(2 * math.pi * k * x / n)
               for (k, a, b, _) in comps)


def poly(points):
    return "M" + " L".join("%.1f %.1f" % p for p in points)


def build_svg(sig):
    n = len(sig)
    if n < 4:
        raise RuntimeError("not enough data")
    comps, N = dft(sig)
    SAMP = 300
    xs = [i * N / (SAMP - 1) for i in range(SAMP)]
    rvals = [recon(x, comps, N) for x in xs]
    peak = max((abs(v) for v in rvals), default=1) or 1
    amp = (H - PAD_T - PAD_B) / 2 * 0.82 / peak

    def X(x):
        return PAD_L + (x / N) * PLOT_W

    def Y(v):
        return MIDY - v * amp

    curve = poly([(X(x), Y(v)) for x, v in zip(xs, rvals)])

    # top-3 individual harmonics, faint, to show the decomposition
    harm_paths = []
    for (k, a, b, _) in comps[:3]:
        pts = [(X(x), Y(a * math.cos(2 * math.pi * k * x / N) + b * math.sin(2 * math.pi * k * x / N)))
               for x in xs]
        harm_paths.append(poly(pts))

    # raw weekly bars
    smax = max(sig) or 1
    bw = PLOT_W / n
    bars = []
    for i, v in enumerate(sig):
        bh = (v / smax) * (BASE - MIDY - 6)
        x = PAD_L + i * bw
        bars.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="1" fill="%s" opacity="0.5"/>'
                    % (x + bw * 0.18, BASE - bh, bw * 0.64, bh, "#1c2836"))

    parts = []
    parts.append('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                 'viewBox="0 0 %d %d" width="%d" height="%d" role="img" '
                 'aria-label="Commit rhythm reconstructed through its Fourier harmonics">' % (W, H, W, H))
    parts.append('<defs>'
                 '<pattern id="g" width="34" height="34" patternUnits="userSpaceOnUse">'
                 '<path d="M34 0H0V34" fill="none" stroke="%s" stroke-width="1"/></pattern>'
                 '<linearGradient id="area" x1="0" y1="0" x2="0" y2="1">'
                 '<stop offset="0" stop-color="%s" stop-opacity="0.20"/>'
                 '<stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient>'
                 '<filter id="glow" x="-20%%" y="-60%%" width="140%%" height="220%%">'
                 '<feGaussianBlur stdDeviation="2.4" result="b"/><feMerge>'
                 '<feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
                 '</defs>' % (GRID, ACC, ACC))
    parts.append('<rect width="%d" height="%d" fill="%s"/>' % (W, H, BG))
    parts.append('<rect width="%d" height="%d" fill="url(#g)" opacity="0.5"/>' % (W, H))
    parts.append('<rect x="0.5" y="0.5" width="%d" height="%d" fill="none" stroke="#1b2330"/>' % (W - 1, H - 1))
    # baseline
    parts.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#22303f" stroke-width="1" stroke-dasharray="2 4"/>'
                 % (PAD_L, MIDY, W - PAD_R, MIDY))
    parts.extend(bars)
    # faint harmonics
    for hp in harm_paths:
        parts.append('<path d="%s" fill="none" stroke="%s" stroke-width="1" opacity="0.28"/>' % (hp, ACC))
    # area under the sum
    parts.append('<path d="%s L %.1f %.1f L %.1f %.1f Z" fill="url(#area)"/>'
                 % (curve, X(N), MIDY, X(0), MIDY))
    # the reconstruction (static, soft) + id for the moving pen
    parts.append('<path id="rhythm" d="%s" fill="none" stroke="%s" stroke-width="2" '
                 'stroke-linecap="round" stroke-linejoin="round" opacity="0.55"/>' % (curve, ACC))
    # traveling light pulse (comet) along the exact curve, seamless loop
    parts.append('<path d="%s" fill="none" stroke="%s" stroke-width="2.6" stroke-linecap="round" '
                 'pathLength="1000" stroke-dasharray="46 1000" filter="url(#glow)">'
                 '<animate attributeName="stroke-dashoffset" values="1046;-46" dur="12s" '
                 'repeatCount="indefinite" calcMode="linear"/></path>' % (curve, ACC))
    # glowing head dot riding the curve, synced
    parts.append('<circle r="3.4" fill="#eafcff" filter="url(#glow)">'
                 '<animateMotion dur="12s" repeatCount="indefinite" rotate="0">'
                 '<mpath xlink:href="#rhythm"/></animateMotion></circle>')
    # No baked-in text: the waveform speaks for itself; any context lives in the
    # README prose, never stamped on the image.
    parts.append('</svg>')
    return "".join(parts)


def main():
    os.makedirs("dist", exist_ok=True)
    try:
        sig = weekly_signal()
        svg = build_svg(sig)
    except Exception as ex:
        print("rhythm generation failed:", ex, file=sys.stderr)
        return 0  # leave any prior SVG in place
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print("wrote", OUT, "weeks=", len(sig))
    return 0


if __name__ == "__main__":
    sys.exit(main())
