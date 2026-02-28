#!/usr/bin/env python3
"""
ACTIVITY HEATMAP
================
Day of Week × Hour of Day contribution heatmap SVG.
Uses the GitHub Stats Punch Card API across ALL owned repos
for full historical data (not just last 90 days).

Generates: dist/activity-heatmap.svg
Requires:  GITHUB_TOKEN env variable
"""

import json
import os
import time
import urllib.request

# ── Config ─────────────────────────────────────────────────────────
USERNAME = "destbreso"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
DIST = "dist"
TZ_OFFSET = -4  # UTC-4 (Eastern / Miami)

# ── Palette ────────────────────────────────────────────────────────
BG     = "#0a0a0f"
BORDER = "#1e1e2a"
ACCENT = "#22d3ee"
DIM    = "#55556a"
MUTED  = "#8888a0"

#            empty       L1         L2         L3         L4
HEAT = ["#111118", "#0b3d4a", "#0f6577", "#1590a5", "#22d3ee"]

CELL = 18
GAP  = 2
STEP = CELL + GAP  # 20

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# ── Data fetching ──────────────────────────────────────────────────
def api_get(url):
    headers = {"Accept": "application/vnd.github.v3+json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read()), r.status


def fetch_repos():
    repos = []
    for page in range(1, 5):
        url = (
            f"https://api.github.com/users/{USERNAME}/repos"
            f"?per_page=100&page={page}&type=owner&sort=pushed"
        )
        try:
            data, _ = api_get(url)
            if not data:
                break
            repos.extend(data)
        except Exception as e:
            print(f"⚠ Repos page {page}: {e}")
            break
    # exclude forks
    return [r for r in repos if not r.get("fork", False)]


def fetch_punch_card(owner, repo):
    """
    GET /repos/{owner}/{repo}/stats/punch_card
    Returns [[day, hour, commits], …]  (168 entries: 7 × 24)
    day: 0 = Sunday … 6 = Saturday
    May return 202 Accepted when computing for the first time → retry.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/stats/punch_card"
    for attempt in range(6):
        try:
            data, status = api_get(url)
            if status == 202:
                # stats being computed — exponential backoff
                wait = 2 * (attempt + 1)
                print(f"  ⏳ {repo}: 202 (computing), retry in {wait}s...")
                time.sleep(wait)
                continue
            if isinstance(data, list) and len(data) > 0:
                return data
            # empty list or unexpected — treat as no data
            return []
        except Exception as e:
            print(f"  ⚠ Punch card {repo} (try {attempt+1}): {e}")
            time.sleep(2)
    print(f"  ✗ {repo}: gave up after retries")
    return []


def build_matrix(repos):
    """Aggregate punch-card data into a 7×24 matrix (Mon–Sun × 0–23h)."""
    matrix = [[0] * 24 for _ in range(7)]

    for repo in repos:
        name = repo["name"]
        owner = repo["owner"]["login"]
        pc = fetch_punch_card(owner, name)

        for entry in pc:
            if not isinstance(entry, list) or len(entry) < 3:
                continue
            day_sun, hour_utc, commits = entry
            # day_sun: 0=Sun … 6=Sat  →  day_mon: 0=Mon … 6=Sun
            day_mon = (day_sun - 1) % 7
            # Timezone shift — also correct the day when crossing midnight
            hour_shifted = hour_utc + TZ_OFFSET
            if hour_shifted < 0:
                hour_shifted += 24
                day_mon = (day_mon - 1) % 7
            elif hour_shifted >= 24:
                hour_shifted -= 24
                day_mon = (day_mon + 1) % 7
            matrix[day_mon][hour_shifted] += commits

        # polite pause between repos
        time.sleep(0.15)

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
        pad + title_h + sub_h + gap_after_sub + hour_h
        + grid_h + legend_gap + legend_h + pad
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

    # ── Defs ───────────────────────────────────────────────────
    s.append("<defs>")

    # Scan-line gradient: transparent → accent glow → transparent
    s.append(
        '<linearGradient id="scan" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0%"   stop-color="#22d3ee" stop-opacity="0"/>'
        '<stop offset="40%"  stop-color="#22d3ee" stop-opacity="0.12"/>'
        '<stop offset="50%"  stop-color="#22d3ee" stop-opacity="0.25"/>'
        '<stop offset="60%"  stop-color="#22d3ee" stop-opacity="0.12"/>'
        '<stop offset="100%" stop-color="#22d3ee" stop-opacity="0"/>'
        '</linearGradient>'
    )

    # Soft glow filter for the scan bar
    s.append(
        '<filter id="scanGlow" x="-20%" y="-20%" width="140%" height="140%">'
        '<feGaussianBlur stdDeviation="3" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
        '</filter>'
    )

    s.append("</defs>")

    # Inline style constants (GitHub strips <style> blocks from SVGs)
    title_style = f"font-family:monospace;font-size:11px;font-weight:bold;fill:{ACCENT};letter-spacing:2px"
    sub_style = f"font-family:monospace;font-size:8px;fill:{DIM}"
    day_style = f"font-family:monospace;font-size:7.5px;fill:{DIM}"
    hr_style = f"font-family:monospace;font-size:6.5px;fill:{DIM}"
    leg_style = f"font-family:monospace;font-size:7px;fill:{MUTED}"

    # Background
    s.append(f'<rect width="{svg_w}" height="{svg_h}" rx="10" fill="{BG}"/>')

    # Title + subtitle
    ty = pad + 12
    s.append(f'<text x="{pad}" y="{ty}" style="{title_style}">▸ ACTIVITY HEATMAP</text>')
    s.append(
        f'<text x="{pad}" y="{ty + sub_h}" style="{sub_style}">'
        f"Day of Week × Hour of Day · All-time · UTC{TZ_OFFSET:+d}"
        f"</text>"
    )

    # Hour labels (every 2 hours)
    for h in range(0, 24, 2):
        x = gx + h * STEP + CELL / 2
        y = gy - 4
        s.append(
            f'<text x="{x}" y="{y}" text-anchor="middle" style="{hr_style}">'
            f"{h:02d}</text>"
        )

    # ── Rows — cells with cascade reveal + continuous wave breathing ──
    anim_total_dur = 2.8          # seconds to reveal entire grid
    cell_count = 7 * 24
    per_cell = anim_total_dur / cell_count

    # Wave parameters (continuous after reveal)
    wave_dur = 5.0                # seconds per full wave cycle
    max_diag = 23 + 6             # max diagonal index (h + ri)
    phase_spread = wave_dur * 0.85  # spread phases across this many seconds

    for ri in range(7):
        yc = gy + ri * STEP + CELL / 2 + 3
        s.append(
            f'<text x="{gx - 4}" y="{yc}" text-anchor="end" style="{day_style}">'
            f"{DAYS[ri]}</text>"
        )

        for h in range(24):
            x = gx + h * STEP
            y = gy + ri * STEP
            val = matrix[ri][h]

            if val == 0:
                color = HEAT[0]
                ratio = 0.0
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

            # Staggered reveal: column-first scan (top→bottom, left→right)
            cell_idx = h * 7 + ri
            delay = round(cell_idx * per_cell, 3)

            s.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="3" fill="{color}" opacity="0">'
            )

            # ── Phase 1: cascade reveal (plays once) ──
            # Fade-in from 0 → 1
            s.append(
                f'<animate attributeName="opacity" from="0" to="1" '
                f'dur="0.35s" begin="{delay:.3f}s" fill="freeze"/>'
            )
            # Grow from center
            half = CELL / 2
            s.append(
                f'<animate attributeName="x" values="{x + half};{x - 1};{x}" '
                f'dur="0.4s" begin="{delay:.3f}s" fill="freeze"/>'
            )
            s.append(
                f'<animate attributeName="y" values="{y + half};{y - 1};{y}" '
                f'dur="0.4s" begin="{delay:.3f}s" fill="freeze"/>'
            )
            s.append(
                f'<animate attributeName="width" values="0;{CELL + 2};{CELL}" '
                f'dur="0.4s" begin="{delay:.3f}s" fill="freeze"/>'
            )
            s.append(
                f'<animate attributeName="height" values="0;{CELL + 2};{CELL}" '
                f'dur="0.4s" begin="{delay:.3f}s" fill="freeze"/>'
            )

            # ── Phase 2: continuous wave breathing (after reveal) ──
            # All active cells participate; intensity depends on activity level
            if val > 0:
                # Diagonal phase offset creates a sweeping wave
                diag = h + ri
                phase = round(diag / max_diag * phase_spread, 3)
                wave_begin = round(anim_total_dur + 0.5 + phase, 3)

                # Higher activity → deeper breathing (more dramatic pulse)
                if ratio > 0.75:
                    lo, hi = 0.50, 1.0
                elif ratio > 0.50:
                    lo, hi = 0.58, 1.0
                elif ratio > 0.25:
                    lo, hi = 0.68, 0.95
                else:
                    lo, hi = 0.78, 0.92

                s.append(
                    f'<animate attributeName="opacity" '
                    f'values="{hi};{lo};{hi}" dur="{wave_dur}s" '
                    f'begin="{wave_begin}s" repeatCount="indefinite"/>'
                )

                # High-activity cells also get a subtle size pulse
                if ratio > 0.6:
                    shrink = round(CELL * 0.92)
                    grow = CELL
                    ox = x + (CELL - shrink) // 2
                    size_begin = round(wave_begin + wave_dur * 0.1, 3)
                    s.append(
                        f'<animate attributeName="width" '
                        f'values="{grow};{shrink};{grow}" dur="{wave_dur}s" '
                        f'begin="{size_begin}s" repeatCount="indefinite"/>'
                    )
                    s.append(
                        f'<animate attributeName="height" '
                        f'values="{grow};{shrink};{grow}" dur="{wave_dur}s" '
                        f'begin="{size_begin}s" repeatCount="indefinite"/>'
                    )
                    s.append(
                        f'<animate attributeName="x" '
                        f'values="{x};{ox};{x}" dur="{wave_dur}s" '
                        f'begin="{size_begin}s" repeatCount="indefinite"/>'
                    )
                    s.append(
                        f'<animate attributeName="y" '
                        f'values="{y};{y + (CELL - shrink) // 2};{y}" '
                        f'dur="{wave_dur}s" '
                        f'begin="{size_begin}s" repeatCount="indefinite"/>'
                    )

            s.append("</rect>")

    # ── Scanning light bar (sweeps left → right continuously) ──
    scan_w = 60  # width of the luminous bar
    scan_begin = round(anim_total_dur + 0.3, 2)
    scan_dur = 6.0

    # Clip to grid area
    s.append(
        f'<clipPath id="gridClip">'
        f'<rect x="{gx}" y="{gy}" width="{grid_w}" height="{grid_h}"/>'
        f'</clipPath>'
    )
    s.append(f'<g clip-path="url(#gridClip)">')
    s.append(
        f'<rect x="{gx - scan_w}" y="{gy}" '
        f'width="{scan_w}" height="{grid_h}" '
        f'fill="url(#scan)" filter="url(#scanGlow)" opacity="0.8">'
        f'<animateTransform attributeName="transform" type="translate" '
        f'from="0 0" to="{grid_w + scan_w * 2} 0" '
        f'dur="{scan_dur}s" begin="{scan_begin}s" repeatCount="indefinite"/>'
        f'</rect>'
    )
    s.append("</g>")

    # Legend (right-aligned)
    ly = gy + grid_h + legend_gap + 10
    leg_cell = 10
    leg_gap = 3
    leg_w = len(HEAT) * (leg_cell + leg_gap)
    lx_start = gx + grid_w - leg_w - 40

    s.append(
        f'<text x="{lx_start - 4}" y="{ly + 3}" text-anchor="end" style="{leg_style}">'
        f"Less</text>"
    )
    for i, c in enumerate(HEAT):
        rx = lx_start + i * (leg_cell + leg_gap)
        s.append(
            f'<rect x="{rx}" y="{ly - 4}" width="{leg_cell}" height="{leg_cell}" '
            f'rx="2" fill="{c}" stroke="{BORDER}" stroke-width=".5"/>'
        )
    last_rx = lx_start + len(HEAT) * (leg_cell + leg_gap)
    s.append(f'<text x="{last_rx + 4}" y="{ly + 3}" style="{leg_style}">More</text>')

    s.append("</svg>")
    return "\n".join(s)


# ── Main ───────────────────────────────────────────────────────────
def main():
    os.makedirs(DIST, exist_ok=True)
    repos = fetch_repos()
    print(f"📦 Found {len(repos)} owned repos (non-fork)")
    matrix = build_matrix(repos)
    svg = generate_svg(matrix)
    path = os.path.join(DIST, "activity-heatmap.svg")
    with open(path, "w") as f:
        f.write(svg)
    total = sum(sum(row) for row in matrix)
    print(f"✅ {path} — {total} total commits aggregated from {len(repos)} repos")


if __name__ == "__main__":
    main()
