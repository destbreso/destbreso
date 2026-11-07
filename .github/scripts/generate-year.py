#!/usr/bin/env python3
"""
The year as threads, for the profile README: one thread a project, in the order they started, swelling in the weeks it
took more work, over the last 52 weeks with this week, still being written, lit at the right. Public projects in cyan,
named where they begin; private work in violet, named only by the public site it serves (generate-data.py decides the
names); the projects too small for a thread of their own share the last one. A dark figure and a light one, for the
README's <picture>.

Reads dist/series.json (written by generate-data.py); writes dist/year.svg and dist/year-light.svg. If the series has no
threads it writes nothing, and the deploy keeps the last good figures. assets/year.js draws the same figure on the page
with the same geometry: change one, change both.
"""

import json
import math
import os
import sys
from datetime import date, timedelta

SERIES = os.path.join("dist", "series.json")
OUT = {"dark": os.path.join("dist", "year.svg"), "light": os.path.join("dist", "year-light.svg")}

W = 1200
LEFT, RIGHT, TOP = 200, 24, 24  # room for the names on the left
ROW = 16                        # a thread's row
BOTTOM = 34                     # the months
HMAX = 6.8                      # a thread's half thickness at its busiest
K = 1.6                         # half thickness for a week of c commits: K * sqrt(c), so a quiet week still shows
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
INK = {
    "dark": dict(bg="#0b0e14", grid="#141b26", pub="#4dd4e0", priv="#a78bfa", small="#5c6675", label="#c9d1d9", plabel="#a78bfa", dim="#5c6675", now="#4dd4e0"),
    "light": dict(bg="#f7f9fb", grid="#e3e9ef", pub="#0f8a99", priv="#7c5cd6", small="#8c959f", label="#1f2328", plabel="#7c5cd6", dim="#8c959f", now="#0f8a99"),
}
MONO = "ui-monospace,SFMono-Regular,Menlo,monospace"


def smooth(pts):
    """A Catmull-Rom curve through the points, as cubic Beziers."""
    d = "M%.1f %.1f" % pts[0]
    for i in range(len(pts) - 1):
        p0, p1, p2, p3 = pts[max(0, i - 1)], pts[i], pts[i + 1], pts[min(len(pts) - 1, i + 2)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += "C%.1f %.1f %.1f %.1f %.1f %.1f" % (c1 + c2 + p2)
    return d


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def rows_of(series):
    rows = [dict(name=t.get("n"), kind="priv" if t.get("private") else "pub", w=t["w"][-52:]) for t in series["threads"]]
    small = series.get("small") or {}
    if small.get("count") and sum(small.get("w", [])):
        rows.append(dict(name="%d small one%s" % (small["count"], "" if small["count"] == 1 else "s"), kind="small", w=small["w"][-52:]))
    return [r for r in rows if sum(r["w"])]


def figure(series, theme):
    C = INK[theme]
    rows = rows_of(series)
    H = TOP + ROW * len(rows) + BOTTOM
    step = (W - LEFT - RIGHT) / 51
    start = date.fromisoformat(series["weekStart"])
    g = ['<rect width="%d" height="%d" fill="%s"/>' % (W, H, C["bg"])]
    # a faint line where each month begins, and its name under the threads
    for k in range(52):
        a, b = start + timedelta(days=7 * k), start + timedelta(days=7 * k + 6)
        if a.month != b.month or a.day == 1 or k == 0:
            m = b if a.month != b.month else a
            x = LEFT + k * step
            g.append('<path d="M%.1f %dV%d" stroke="%s"/>' % (x, TOP - 8, H - BOTTOM + 8, C["grid"]))
            g.append('<text x="%.1f" y="%d" fill="%s" font-size="12" font-family="%s">%s</text>' % (x + 4, H - 12, C["dim"], MONO, MONTHS[m.month - 1]))
    # this week, still being written
    g.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" fill="%s" fill-opacity=".08"/>' % (LEFT + 51 * step - step / 2, TOP - 8, step, H - TOP - BOTTOM + 16, C["now"]))
    for i, r in enumerate(rows):
        y = TOP + i * ROW + ROW / 2
        w = r["w"]
        first = next(k for k, c in enumerate(w) if c)
        last = max(k for k, c in enumerate(w) if c)
        col = {"pub": C["pub"], "priv": C["priv"], "small": C["small"]}[r["kind"]]
        x0, x1 = LEFT + first * step, LEFT + last * step
        g.append('<path d="M%.1f %.1fH%.1f" stroke="%s" stroke-opacity=".45"/>' % (x0, y, x1, col))
        if last > first:
            # the band tapers to the line half a week before it starts and after it ends
            top = [(x0 - step * 0.6, y)] + [(LEFT + k * step, y - (min(HMAX, K * math.sqrt(w[k])) if w[k] else 0)) for k in range(first, last + 1)]
            end = min(W - RIGHT, x1 + step * 0.6)
            top.append((end, y))
            bot = [(x, 2 * y - yy) for x, yy in top]
            g.append('<path d="%sL%sZ" fill="%s"/>' % (smooth(top), smooth(bot[::-1])[1:], col))
        else:
            g.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (x0, y, max(1.8, min(HMAX, K * math.sqrt(w[first]))), col))
        if r["name"]:
            lc = {"pub": C["label"], "priv": C["plabel"], "small": C["dim"]}[r["kind"]]
            g.append('<text x="%.1f" y="%.1f" text-anchor="end" fill="%s" font-size="13" font-family="%s">%s</text>' % (x0 - step * 0.6 - 5, y + 4.4, lc, MONO, esc(r["name"])))
    label = "The last 52 weeks as threads, one a project in the order each started, thicker in the weeks it took more work"
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="%s">%s</svg>'
            % (W, H, W, H, label, "".join(g)))


def build():
    try:
        with open(SERIES, encoding="utf-8") as f:
            series = json.load(f)
    except (OSError, ValueError) as ex:
        print("year: no series (%s); keeping the last figures" % ex, file=sys.stderr)
        return 0
    if not series.get("threads") or not series.get("weekStart"):
        print("year: the series has no threads; keeping the last figures", file=sys.stderr)
        return 0
    for theme, path in OUT.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(figure(series, theme))
        print("wrote", path)
    return 0


if __name__ == "__main__":
    sys.exit(build())
