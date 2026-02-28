#!/usr/bin/env python3
"""
ACTIVITY HEATMAP
================
Day of Week × Hour of Day contribution heatmap SVG.
Uses the GitHub Events API for timestamp-level granularity.

Generates: dist/activity-heatmap.svg
Requires:  GITHUB_TOKEN env variable (optional, improves rate-limit)
"""

import json
import os
import urllib.request
import datetime

# ── Config ─────────────────────────────────────────────────────────
USERNAME = "destbreso"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
DIST = "dist"
TZ_OFFSET = -4  # UTC-4 (Eastern / Miami)

# ── Palette ────────────────────────────────────────────────────────
BG = "#0a0a0f"
CARD = "#111118"
BORDER = "#1e1e2a"
ACCENT = "#22d3ee"
TEXT = "#e0e0e8"
DIM = "#55556a"
MUTED = "#8888a0"

#               empty       L1         L2         L3         L4
HEAT = ["#111118", "#0b3d4a", "#0f6577", "#1590a5", "#22d3ee"]

CELL = 18
GAP = 2
STEP = CELL + GAP  # 20

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# ── Data fetching ──────────────────────────────────────────────────
def fetch_events():
    """Fetch up to 1 000 public events from GitHub REST API."""
    all_events = []
    headers = {"Accept": "application/vnd.github.v3+json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    for page in range(1, 11):
        url = (
            f"https://api.github.com/users/{USERNAME}"
            f"/events?per_page=100&page={page}"
        )
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as r:
                data = json.loads(r.read())
                if not data:
                    break
                all_events.extend(data)
        except Exception as e:
            print(f"⚠  Page {page} failed: {e}")
            break

    return all_events


def build_matrix(events):
    """Build a 7×24 matrix (Mon-Sun × 0h-23h) from PushEvent timestamps."""
    # matrix[weekday 0=Mon..6=Sun][hour 0..23]
    matrix = [[0] * 24 for _ in range(7)]

    for ev in events:
        if ev.get("type") != "PushEvent":
            continue
        ts = ev.get("created_at", "")
        if not ts:
            continue
        try:
            parts = ts.replace("Z", "").split("T")
            ymd = parts[0].split("-")
            hms = parts[1].split(":")
            dt = datetime.date(int(ymd[0]), int(ymd[1]), int(ymd[2]))
            hour = (int(hms[0]) + TZ_OFFSET) % 24
            dow = dt.weekday()  # 0=Mon .. 6=Sun

            payload = ev.get("payload", {})
            commits = payload.get("size") or len(payload.get("commits", [])) or 1
            matrix[dow][hour] += commits
        except Exception:
            continue

    return matrix


# ── SVG generation ─────────────────────────────────────────────────
def generate_svg(matrix):
    pad = 16
    title_h = 18
    sub_h = 14
    gap_after_sub = 8
    label_w = 32
    hour_h = 14
    legend_h = 24
    legend_gap = 10

    grid_w = 24 * STEP
    grid_h = 7 * STEP

    svg_w = pad + label_w + grid_w + pad
    svg_h = (
        pad + title_h + sub_h + gap_after_sub + hour_h + grid_h
        + legend_gap + legend_h + pad
    )

    gx = pad + label_w
    gy = pad + title_h + sub_h + gap_after_sub + hour_h

    flat = [v for row in matrix for v in row]
    max_val = max(flat) if flat else 1
    if max_val == 0:
        max_val = 1

    s = []
    s.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {svg_w} {svg_h}" width="{svg_w}" height="{svg_h}">'
    )

    # ── Styles ─────────────────────────────────────────────────────
    s.append("<style>")
    s.append(
        f"text {{ font-family:'Courier New','Lucida Console',monospace; }}\n"
        f".t {{ font-size:11px; font-weight:bold; fill:{ACCENT}; letter-spacing:2px; }}\n"
        f".sub {{ font-size:8px; fill:{DIM}; }}\n"
        f".day {{ font-size:7.5px; fill:{DIM}; }}\n"
        f".hr {{ font-size:6.5px; fill:{DIM}; }}\n"
        f".leg {{ font-size:7px; fill:{MUTED}; }}"
    )
    s.append("</style>")

    # ── Background ─────────────────────────────────────────────────
    s.append(f'<rect width="{svg_w}" height="{svg_h}" rx="10" fill="{BG}"/>')

    # ── Title ──────────────────────────────────────────────────────
    ty = pad + 12
    s.append(f'<text x="{pad}" y="{ty}" class="t">▸ ACTIVITY HEATMAP</text>')
    s.append(
        f'<text x="{pad}" y="{ty + sub_h}" class="sub">'
        f"Day of Week × Hour of Day · Last 90 days · UTC{TZ_OFFSET:+d}"
        f"</text>"
    )

    # ── Hour labels (every 2 hours) ────────────────────────────────
    for h in range(0, 24, 2):
        x = gx + h * STEP + CELL / 2
        y = gy - 4
        s.append(
            f'<text x="{x}" y="{y}" text-anchor="middle" class="hr">'
            f"{h:02d}</text>"
        )

    # ── Rows: Day label + cells ────────────────────────────────────
    for ri in range(7):
        yc = gy + ri * STEP + CELL / 2 + 3
        s.append(
            f'<text x="{gx - 4}" y="{yc}" text-anchor="end" class="day">'
            f"{DAYS[ri]}</text>"
        )

        for h in range(24):
            x = gx + h * STEP
            y = gy + ri * STEP
            val = matrix[ri][h]

            if val == 0:
                color = HEAT[0]
            else:
                ratio = val / max_val
                if ratio <= 0.25:
                    color = HEAT[1]
                elif ratio <= 0.50:
                    color = HEAT[2]
                elif ratio <= 0.75:
                    color = HEAT[3]
                else:
                    color = HEAT[4]

            s.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="3" fill="{color}"/>'
            )

    # ── Legend (right-aligned) ─────────────────────────────────────
    ly = gy + grid_h + legend_gap + 10
    leg_cell = 10
    leg_gap = 3
    leg_w = len(HEAT) * (leg_cell + leg_gap)

    lx_start = gx + grid_w - leg_w - 40

    s.append(f'<text x="{lx_start - 4}" y="{ly + 3}" text-anchor="end" class="leg">Less</text>')
    for i, c in enumerate(HEAT):
        rx = lx_start + i * (leg_cell + leg_gap)
        s.append(
            f'<rect x="{rx}" y="{ly - 4}" width="{leg_cell}" height="{leg_cell}" '
            f'rx="2" fill="{c}" stroke="{BORDER}" stroke-width=".5"/>'
        )
    last_rx = lx_start + len(HEAT) * (leg_cell + leg_gap)
    s.append(f'<text x="{last_rx + 4}" y="{ly + 3}" class="leg">More</text>')

    s.append("</svg>")
    return "\n".join(s)


# ── Main ───────────────────────────────────────────────────────────
def main():
    os.makedirs(DIST, exist_ok=True)
    events = fetch_events()
    matrix = build_matrix(events)
    svg = generate_svg(matrix)
    path = os.path.join(DIST, "activity-heatmap.svg")
    with open(path, "w") as f:
        f.write(svg)

    total = sum(sum(row) for row in matrix)
    push_count = sum(1 for e in events if e.get("type") == "PushEvent")
    print(f"✅ {path} — {total} commits from {push_count} push events")


if __name__ == "__main__":
    main()
