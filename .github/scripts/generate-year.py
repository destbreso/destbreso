#!/usr/bin/env python3
"""
The year in pixels, for the profile README: one column a week for the last 52 weeks, public
work in cyan under private work in violet, and a small blueprint robot that walks the year
from the oldest week to this one. It climbs onto each week's column, stops to look up at the
busiest week, and at this week turns to the visitor, pleased when the week is above the
year's average. No text: the README's caption says what it is.

A README runs no JavaScript, so everything moves by CSS keyframes inside the SVG, all of them
on one clock (CYCLE seconds, or a fraction of it), so they never drift apart. Pixel art:
whole units, crisp edges, step timing. Reads dist/series.json (written by generate-data.py);
writes dist/year.svg. If the series is missing it writes nothing, and the deploy keeps the
last good figure.
"""

import json
import math
import os
import sys

SERIES = os.path.join("dist", "series.json")
OUT = os.path.join("dist", "year.svg")

PITCH = 4          # a week's column and its gap, in pixels
BAR = 3            # a column's width
HMAX = 34          # the busiest week's height
LEFT, TOP = 6, 26  # room for the robot on the tallest column
W = LEFT * 2 + 52 * PITCH - 1
GROUND = TOP + HMAX  # the row the columns stand on
H = GROUND + 6
CYCLE = 30.0       # seconds, set from the walk's length in build(): a multiple of 3, so the 1 s and 1.5 s pulses divide it
STEP = 0.4         # seconds from one week to the next
SUB = 4            # moves a step (one pixel each, as the pitch is four)

# the robot's pixels, shared with the page (assets/year.js): one source for both
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "robot.json"), encoding="utf-8") as _f:
    ROBOT = json.load(_f)
HEAD = ROBOT["head"]
RW, RH = ROBOT["w"], ROBOT["h"]
EYE_NAMES = ("right", "front", "up", "closed", "happy")


def runs(rows, ch):
    """One path for every pixel of an ink: each horizontal run as a rectangle."""
    d = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            if row[x] == ch:
                n = 1
                while x + n < len(row) and row[x + n] == ch:
                    n += 1
                d.append("M%d %dh%dv1h-%dz" % (x, y, n, n))
                x += n
            else:
                x += 1
    return "".join(d)


def pct(t):
    return "%.3f%%" % (max(0.0, min(CYCLE, t)) / CYCLE * 100)


def keyframes(name, frames, prop):
    """frames: [(time in seconds, value)] held until the next (step-end)."""
    body = "".join("%s{%s:%s}" % (pct(t), prop, v) for t, v in frames)
    return "@keyframes %s{%s}" % (name, body)


def build(series):
    global CYCLE
    weekly = series["weekly"][-52:]
    pub = (series.get("weeklyPublic") or [None] * 52)[-52:]
    split = all(p is not None for p in pub)
    days_now = series.get("daysThisWeek", 7)
    peak = max(weekly) or 1
    per = peak / HMAX
    heights = [0 if c == 0 else max(1, round(c / per)) for c in weekly]
    pub_h = [0 if not split or c == 0 else min(h, round(p / per)) for c, p, h in zip(weekly, pub, heights)]
    busiest = max(range(52), key=lambda i: weekly[i])
    full = weekly[:-1]
    average = sum(full) / max(1, len(full))
    # this week so far, against an average week cut to as many days
    pleased = weekly[-1] >= average * days_now / 7

    col_x = lambda i: LEFT + i * PITCH
    # the robot walks the rooftops: on the highest of the three columns under its body, so it never sinks into one
    def ground(i):
        return max(heights[max(0, i - 1): i + 2])
    def at(i):
        return col_x(i) + 1 - RW // 2 + 1, GROUND - ground(i) - RH

    # ── the timeline (seconds) ──
    t = 0.8                      # it appears
    moves = []                   # (time, x, y)
    legs = []                    # (time, "a" | "b")
    eyes = [(0.0, "right")]
    x0, y0 = at(0)
    moves.append((0.0, x0, y0))
    legs.append((0.0, "a"))
    stop_busy = stop_busy_end = None
    for i in range(51):
        if i == busiest and i > 0:
            stop_busy = t
            eyes += [(t + 0.2, "up"), (t + 1.3, "closed"), (t + 1.45, "up"), (t + 2.3, "right")]
            t += 2.5
            stop_busy_end = t
        (xa, ya), (xb, yb) = at(i), at(i + 1)
        arc = 2 + max(0, ya - yb) // 3
        for s in range(1, SUB + 1):
            f = s / SUB
            x = round(xa + (xb - xa) * f)
            y = round(ya + (yb - ya) * f - arc * math.sin(math.pi * f))
            moves.append((t + STEP * f, x, y))
            legs.append((t + STEP * (s - 0.5) / SUB, "b" if s % 2 else "a"))
        t += STEP
    if busiest == 51:
        stop_busy = t
    legs.append((t, "a"))
    # at this week: turns to the visitor, pleased or calm, blinks, then fades and the year starts again
    end = t
    eyes += [(end + 0.3, "front"), (end + 1.1, "happy" if pleased else "closed"), (end + 2.2 if not pleased else end + 3.0, "front")]
    if not pleased:
        eyes += [(end + 2.35, "closed"), (end + 2.5, "front")]
    fade_at = end + 4.2
    # the next year begins soon after: the clock is as long as the walk and its rests, a multiple of 3 s
    CYCLE = 3.0 * math.ceil((fade_at + 0.9) / 3.0)
    # a blink now and then on the way
    for bt in (3.0, 9.5, 16.0):
        if bt < end and not (stop_busy and stop_busy <= bt <= (stop_busy_end or 0)):
            eyes += [(bt, "closed"), (bt + 0.14, "right")]
    eyes.sort()

    css = []
    css.append("svg{--bg:#0b0e14;--grid:#141c28;--ground:#263243;--pub:#4dd4e0;--priv:#a78bfa;--line:#4dd4e0;--face:#0b0e14;--eye:#c9f7fb;--spark:#fde68a;--cap:rgba(255,255,255,.28)}")
    css.append("@media (prefers-color-scheme:light){svg{--bg:#f6f8fa;--grid:#e6ebf1;--ground:#c3cedb;--pub:#1597a6;--priv:#7c5cd6;--line:#1597a6;--face:#f6f8fa;--eye:#0e6f7b;--spark:#d97706;--cap:rgba(255,255,255,.45)}}")
    css.append(".bg{fill:var(--bg)}.gr{stroke:var(--grid)}.gd{fill:var(--ground)}.pb{fill:var(--pub)}.pv{fill:var(--priv)}"
               ".o{fill:var(--line)}.f{fill:var(--face)}.e{fill:var(--eye)}.sp{fill:var(--spark)}.cap{fill:var(--cap)}")
    anim = "%.1fs step-end infinite" % CYCLE
    css.append(keyframes("walk", [(tt, "translate(%dpx,%dpx)" % (x, y)) for tt, x, y in moves], "transform"))
    css.append(keyframes("show", [(0, "0"), (0.8, "1"), (fade_at, "0")], "opacity"))
    css.append(".robot{animation:walk %s,show %s}" % (anim, anim))
    for leg in ("a", "b"):
        css.append(keyframes("leg" + leg, [(tt, "1" if v == leg else "0") for tt, v in legs], "opacity"))
        css.append(".leg%s{animation:leg%s %s}" % (leg, leg, anim))
    for name in EYE_NAMES:
        frames = [(tt, "1" if v == name else "0") for tt, v in eyes]
        if frames[0][0] > 0:
            frames.insert(0, (0, "1" if name == "right" else "0"))
        css.append(keyframes("eye" + name, frames, "opacity"))
        css.append(".eye%s{animation:eye%s %s}" % (name, name, anim))
    # the antenna's light and this week's cursor, on whole fractions of the clock
    css.append("@keyframes pulse{0%{opacity:1}50%{opacity:.35}}.ant{animation:pulse 1.5s steps(1) infinite}")
    css.append("@keyframes cur{0%{opacity:1}50%{opacity:0}}.cur{animation:cur 1s step-end infinite}")
    if stop_busy is not None:
        css.append(keyframes("spark", [(0, "0"), (stop_busy + 0.3, "1"), (stop_busy + 0.6, "0.4"), (stop_busy + 0.9, "1"), (stop_busy + 1.2, "0.4"), (stop_busy + 1.5, "1"), ((stop_busy_end or stop_busy + 2.4) + 0.4, "0")], "opacity"))
        css.append(".spark{animation:spark %s}" % anim)

    out = []
    out.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" shape-rendering="crispEdges">' % (W, H, W * 4, H * 4))
    out.append("<title>A year of commits, a column a week, walked by a small robot</title>")
    out.append("<style>%s</style>" % "".join(css))
    out.append('<rect class="bg" width="%d" height="%d"/>' % (W, H))
    # the blueprint's grid, every eight pixels
    grid = "".join("M%d 0v%d" % (x, H) for x in range(0, W, 8)) + "".join("M0 %dh%d" % (y, W) for y in range(0, H, 8))
    out.append('<path class="gr" stroke-width=".25" fill="none" d="%s"/>' % grid)
    # the ground, and a tick where each month begins (from the series' first Monday)
    out.append('<rect class="gd" x="%d" y="%d" width="%d" height="1"/>' % (LEFT - 2, GROUND, 52 * PITCH + 3))
    ticks = []
    try:
        from datetime import date, timedelta
        start = date.fromisoformat(series["weekStart"])
        for i in range(52):
            a, b = start + timedelta(weeks=i), start + timedelta(weeks=i, days=6)
            if a.month != b.month or a.day == 1:
                ticks.append("M%d %dh1v2h-1z" % (col_x(i) + 1, GROUND + 2))
    except Exception:
        pass
    out.append('<path class="gd" d="%s"/>' % "".join(ticks))
    # the columns: public at the foot, private stacked on it
    pd, vd = [], []
    for i, (h, ph) in enumerate(zip(heights, pub_h)):
        if not h:
            continue
        x = col_x(i)
        if split:
            if ph:
                pd.append("M%d %dh%dv%dh-%dz" % (x, GROUND - ph, BAR, ph, BAR))
            if h - ph:
                vd.append("M%d %dh%dv%dh-%dz" % (x, GROUND - h, BAR, h - ph, BAR))
        else:
            pd.append("M%d %dh%dv%dh-%dz" % (x, GROUND - h, BAR, h, BAR))
    out.append('<path class="pb" d="%s"/>' % "".join(pd))
    out.append('<path class="pv" d="%s"/>' % "".join(vd))
    # a row of light on each column's top, as pixel art lights its blocks
    caps = "".join("M%d %dh%dv1h-%dz" % (col_x(i), GROUND - h, BAR, BAR) for i, h in enumerate(heights) if h)
    out.append('<path class="cap" d="%s"/>' % caps)
    # this week is still being written: its top pixel blinks
    out.append('<rect class="cur o" x="%d" y="%d" width="%d" height="1"/>' % (col_x(51), GROUND - heights[51] - 2, BAR))
    # a spark over the busiest week while the robot looks at it
    if stop_busy is not None:
        sx, sy = col_x(busiest) + 1, GROUND - heights[busiest] - RH - 9
        out.append('<path class="spark sp" d="M%d %dh1v1h1v1h-1v1h-1v-1h-1v-1h1z"/>' % (sx, sy))
    # the robot
    out.append('<g class="robot">')
    out.append('<path class="f" d="%s"/>' % runs(HEAD, "F"))
    out.append('<path class="o" d="%s"/>' % runs(HEAD, "O"))
    out.append('<path class="ant e" d="%s"/>' % runs(HEAD, "A"))
    for name in EYE_NAMES:
        out.append('<path class="eye%s e" d="%s"/>' % (name, runs(ROBOT["eyes"][name], "E")))
    for leg in ("a", "b"):
        out.append('<path class="leg%s o" d="%s"/>' % (leg, runs([""] * 11 + ROBOT["legs"][leg], "O")))
    out.append("</g></svg>")
    return "".join(out)


def main():
    try:
        with open(SERIES, encoding="utf-8") as f:
            series = json.load(f)
        if len(series.get("weekly", [])) < 52:
            raise ValueError("fewer than 52 weeks")
        svg = build(series)
    except Exception as ex:
        print("year.svg not written:", ex, file=sys.stderr)
        return 0
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print("wrote", OUT, len(svg.encode()), "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
