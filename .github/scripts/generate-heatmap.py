#!/usr/bin/env python3
"""
ACTIVITY HEATMAP — Ant Pathfinding Edition
==========================================
Day-of-Week × Hour-of-Day heatmap with an animated ant that:
  1. Spawns at a random low-activity cell
  2. Navigates to a *food target* using A* pathfinding
  3. "Eats through" wall cells — thicker walls take longer to chew
  4. Leaves a glowing trail behind
  5. Celebrates reaching the target
  6. Resets and loops seamlessly

SMIL-only (GitHub-safe — no CSS, no JS).
Generates: dist/activity-heatmap.svg
Requires:  GITHUB_TOKEN env variable
"""

import heapq, json, math, os, random, time, urllib.request

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


# ── A* Pathfinding ─────────────────────────────────────────────────
def astar(matrix, start, goal, max_val):
    """A* on the 7×24 grid.  Cost to enter a cell = 1 + 4*(val/max_val).
    Empty cells cost 1 step, max-activity cells cost 5 steps (thick wall).
    Returns list of (row, col) from start to goal inclusive."""
    rows, cols = 7, 24

    def h(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    open_set = [(h(start, goal), 0, start)]
    came_from = {}
    g_score = {start: 0}

    while open_set:
        _, gc, current = heapq.heappop(open_set)
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = current[0] + dr, current[1] + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                val = matrix[nr][nc]
                cost = 1.0 + 4.0 * (val / max_val)
                ng = gc + cost
                nb = (nr, nc)
                if nb not in g_score or ng < g_score[nb]:
                    g_score[nb] = ng
                    came_from[nb] = current
                    heapq.heappush(open_set, (ng + h(nb, goal), ng, nb))
    # Fallback: direct walk (shouldn't happen on 7×24)
    path = [start]
    r, c = start
    while (r, c) != goal:
        if r < goal[0]: r += 1
        elif r > goal[0]: r -= 1
        elif c < goal[1]: c += 1
        elif c > goal[1]: c -= 1
        path.append((r, c))
    return path


# ── SVG generation ─────────────────────────────────────────────────
def generate_svg(matrix):
    pad = 16
    title_h = 18
    sub_h = 14
    gap_after_sub = 8
    label_w = 32
    hour_h = 14
    legend_h = 24
    legend_gap = 12

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

    # ── Pick ant start, target, and compute path ──────────────
    rng = random.Random(7)

    # Classify cells by weight
    empties = []
    lights = []
    heavies = []
    for r in range(7):
        for c in range(24):
            ratio = matrix[r][c] / max_val
            if ratio == 0:
                empties.append((r, c))
            elif ratio <= 0.25:
                lights.append((r, c))
            elif ratio > 0.5:
                heavies.append((r, c))

    # Start: prefer empty/light cells on the left side
    start_pool = [p for p in (empties + lights) if p[1] < 12]
    if not start_pool:
        start_pool = empties + lights
    if not start_pool:
        start_pool = [(0, 0)]
    ant_start = rng.choice(start_pool)

    # Target: prefer a heavy cell far from start
    target_pool = heavies if heavies else lights if lights else [(6, 23)]
    target_pool.sort(key=lambda p: -(abs(p[0]-ant_start[0]) + abs(p[1]-ant_start[1])))
    ant_target = target_pool[0] if target_pool else (6, 23)

    path = astar(matrix, ant_start, ant_target, max_val)

    # ── Timing ────────────────────────────────────────────────
    # Each step: base 0.12s + wall thickness bonus (up to 0.48s for max walls)
    step_times = []
    t = 0.0
    for r, c in path:
        ratio = matrix[r][c] / max_val
        dur = 0.12 + 0.48 * ratio  # eating through thick walls is slow
        step_times.append(t)
        t += dur
    walk_dur = t
    celebrate_dur = 1.8       # celebration at target
    fade_dur = 1.2            # trail fades out + reset
    total_dur = walk_dur + celebrate_dur + fade_dur

    # ── Inline styles ─────────────────────────────────────────
    title_style = f"font-family:monospace;font-size:11px;font-weight:bold;fill:{ACCENT};letter-spacing:2px"
    sub_style = f"font-family:monospace;font-size:8px;fill:{DIM}"
    day_style = f"font-family:monospace;font-size:7.5px;fill:{DIM}"
    hr_style = f"font-family:monospace;font-size:6.5px;fill:{DIM}"
    leg_style = f"font-family:monospace;font-size:7px;fill:{MUTED}"

    s = []

    # ── Root SVG ──────────────────────────────────────────────
    s.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {svg_w} {svg_h}" width="{svg_w}" height="{svg_h}">'
    )

    # ── Defs ──────────────────────────────────────────────────
    s.append("<defs>")

    # Glow filter for ant head / target
    s.append(
        '<filter id="glo" x="-60%" y="-60%" width="220%" height="220%">'
        '<feGaussianBlur stdDeviation="2" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
        '</filter>'
    )
    # Celebration burst filter
    s.append(
        '<filter id="burst" x="-100%" y="-100%" width="300%" height="300%">'
        '<feGaussianBlur stdDeviation="4" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
        '</filter>'
    )

    s.append("</defs>")

    # ── Background ────────────────────────────────────────────
    s.append(f'<rect width="{svg_w}" height="{svg_h}" rx="10" fill="{BG}"/>')

    # ── Title ─────────────────────────────────────────────────
    ty = pad + 12
    s.append(f'<text x="{pad}" y="{ty}" style="{title_style}">▸ ACTIVITY HEATMAP</text>')
    s.append(
        f'<text x="{pad}" y="{ty + sub_h}" style="{sub_style}">'
        f"Day × Hour · All-time · UTC{TZ_OFFSET:+d} · 🐜 A* pathfinding"
        f"</text>"
    )

    # ── Hour labels ───────────────────────────────────────────
    for h in range(0, 24, 2):
        x = gx + h * STEP + CELL / 2
        y = gy - 4
        s.append(
            f'<text x="{x}" y="{y}" text-anchor="middle" style="{hr_style}">'
            f"{h:02d}</text>"
        )

    # ── Day labels ────────────────────────────────────────────
    for ri in range(7):
        yc = gy + ri * STEP + CELL / 2 + 3
        s.append(
            f'<text x="{gx - 4}" y="{yc}" text-anchor="end" style="{day_style}">'
            f"{DAYS[ri]}</text>"
        )

    # ══════════════════════════════════════════════════════════
    #  HEATMAP CELLS — with ant-eating animation
    # ══════════════════════════════════════════════════════════
    path_set = set(path)
    # For cells on the path, compute when the ant arrives
    path_arrival = {}
    for idx, (r, c) in enumerate(path):
        path_arrival[(r, c)] = step_times[idx]

    for ri in range(7):
        for h in range(24):
            x = gx + h * STEP
            y = gy + ri * STEP
            val = matrix[ri][h]
            if val == 0:
                color = HEAT[0]
                ratio = 0.0
            else:
                ratio = val / max_val
                if ratio <= 0.25: color = HEAT[1]
                elif ratio <= 0.50: color = HEAT[2]
                elif ratio <= 0.75: color = HEAT[3]
                else: color = HEAT[4]

            on_path = (ri, h) in path_set
            arrival = path_arrival.get((ri, h))

            if on_path and val > 0:
                # Cell gets "eaten": flash bright then dim to empty color
                eat_start = round(arrival, 3)
                eat_flash = round(eat_start + 0.06, 3)
                eat_done = round(eat_start + 0.12 + 0.36 * ratio, 3)
                reset_start = round(walk_dur + celebrate_dur, 3)
                reset_done = round(total_dur - 0.1, 3)

                kt = _kt([0, eat_start, eat_flash, eat_done, reset_start, reset_done, total_dur], total_dur)

                # Color animation: original → white flash → eaten(dim) → hold → restore
                eaten_color = HEAT[0]
                fill_vals = f"{color};{color};#ffffff;{eaten_color};{eaten_color};{color};{color}"

                s.append(
                    f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                    f'rx="3" fill="{color}">'
                    f'<animate attributeName="fill" dur="{total_dur}s" '
                    f'repeatCount="indefinite" keyTimes="{kt}" values="{fill_vals}"/>'
                )

                # Shake when eating thick walls
                if ratio > 0.3:
                    shake_x = f"{x};{x+1};{x-1};{x+1};{x}"
                    shake_kt = _kt([0, eat_start, eat_start+0.03, eat_start+0.06, eat_start+0.09, total_dur], total_dur)
                    shake_vals = f"{x};{x+1};{x-1};{x+1};{x};{x}"
                    s.append(
                        f'<animate attributeName="x" dur="{total_dur}s" '
                        f'repeatCount="indefinite" keyTimes="{shake_kt}" values="{shake_vals}"/>'
                    )

                s.append("</rect>")

            elif on_path and val == 0:
                # Empty cell on path: subtle highlight when ant passes
                highlight_start = round(arrival, 3)
                highlight_end = round(arrival + 0.2, 3)
                reset_s = round(total_dur - 0.5, 3)

                kt = _kt([0, highlight_start, highlight_end, reset_s, total_dur], total_dur)
                op_vals = "1;1;0.6;0.6;1"

                s.append(
                    f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                    f'rx="3" fill="{color}" opacity="1">'
                    f'<animate attributeName="opacity" dur="{total_dur}s" '
                    f'repeatCount="indefinite" keyTimes="{kt}" values="{op_vals}"/>'
                    f'</rect>'
                )
            else:
                # Static cell (not on path)
                s.append(
                    f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                    f'rx="3" fill="{color}"/>'
                )

    # ══════════════════════════════════════════════════════════
    #  ANT TRAIL (glowing path left behind)
    # ══════════════════════════════════════════════════════════
    for idx in range(len(path)):
        r, c = path[idx]
        cx = gx + c * STEP + CELL / 2
        cy = gy + r * STEP + CELL / 2
        t_arrive = step_times[idx]

        # Trail dot: appears when ant arrives, fades during celebration
        t_on = round(t_arrive + 0.05, 3)
        t_glow = round(t_arrive + 0.15, 3)
        t_fade_start = round(walk_dur + celebrate_dur * 0.5, 3)
        t_fade_end = round(total_dur - 0.1, 3)

        kt = _kt([0, t_on, t_glow, t_fade_start, t_fade_end, total_dur], total_dur)
        op_vs = "0;0.6;0.35;0.35;0;0"

        s.append(
            f'<circle cx="{cx}" cy="{cy}" r="3" fill="{ACCENT}" opacity="0">'
            f'<animate attributeName="opacity" dur="{total_dur}s" '
            f'repeatCount="indefinite" keyTimes="{kt}" values="{op_vs}"/>'
            f'</circle>'
        )

    # ══════════════════════════════════════════════════════════
    #  FOOD TARGET (pulsing marker)
    # ══════════════════════════════════════════════════════════
    tr, tc = ant_target
    tx = gx + tc * STEP + CELL / 2
    ty_food = gy + tr * STEP + CELL / 2

    # Outer pulse ring
    t_eat = round(step_times[-1], 3) if step_times else 0
    t_gone = round(t_eat + 0.3, 3)

    kt_food = _kt([0, t_eat, t_gone, total_dur], total_dur)
    s.append(
        f'<circle cx="{tx}" cy="{ty_food}" r="6" fill="none" '
        f'stroke="{ACCENT}" stroke-width="1.2" opacity="0.7">'
        f'<animate attributeName="r" values="5;8;5" dur="1.2s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" dur="{total_dur}s" '
        f'repeatCount="indefinite" keyTimes="{kt_food}" values="0.7;0.7;0;0"/>'
        f'</circle>'
    )
    # Inner dot
    s.append(
        f'<circle cx="{tx}" cy="{ty_food}" r="2.5" fill="{ACCENT}" opacity="0.9">'
        f'<animate attributeName="opacity" dur="{total_dur}s" '
        f'repeatCount="indefinite" keyTimes="{kt_food}" values="0.9;0.9;0;0"/>'
        f'</circle>'
    )

    # ══════════════════════════════════════════════════════════
    #  CELEBRATION BURST (when ant reaches target)
    # ══════════════════════════════════════════════════════════
    celeb_start = round(walk_dur, 3)
    celeb_peak = round(walk_dur + 0.3, 3)
    celeb_end = round(walk_dur + celebrate_dur, 3)

    kt_celeb = _kt([0, celeb_start, celeb_peak, celeb_end, total_dur], total_dur)

    # Expanding ring burst
    for ring_i in range(3):
        delay_offset = ring_i * 0.15
        r_start = round(celeb_start + delay_offset, 3)
        r_peak = round(celeb_peak + delay_offset, 3)
        r_end = round(celeb_end, 3)
        kt_r = _kt([0, r_start, r_peak, r_end, total_dur], total_dur)
        max_r = 12 + ring_i * 8
        s.append(
            f'<circle cx="{tx}" cy="{ty_food}" r="0" fill="none" '
            f'stroke="{ACCENT}" stroke-width="1" opacity="0" filter="url(#burst)">'
            f'<animate attributeName="r" dur="{total_dur}s" '
            f'repeatCount="indefinite" keyTimes="{kt_r}" '
            f'values="0;0;{max_r};{max_r + 5};0"/>'
            f'<animate attributeName="opacity" dur="{total_dur}s" '
            f'repeatCount="indefinite" keyTimes="{kt_r}" '
            f'values="0;0;0.7;0;0"/>'
            f'</circle>'
        )

    # ══════════════════════════════════════════════════════════
    #  ANT — procedural body + animated legs + antennae
    # ══════════════════════════════════════════════════════════
    # Build the ant as a small group that moves along the path

    # X, Y value strings for the walk
    ant_x_vals = []
    ant_y_vals = []
    # Rotation (face direction of movement)
    ant_rot_vals = []

    for idx, (r, c) in enumerate(path):
        cx = gx + c * STEP + CELL / 2
        cy = gy + r * STEP + CELL / 2
        ant_x_vals.append(f"{cx:.1f}")
        ant_y_vals.append(f"{cy:.1f}")

        # Compute facing angle
        if idx < len(path) - 1:
            nr, nc = path[idx + 1]
            dx = nc - c
            dy = nr - r
            angle = math.degrees(math.atan2(dy, dx))
        elif idx > 0:
            pr, pc = path[idx - 1]
            dx = c - pc
            dy = r - pr
            angle = math.degrees(math.atan2(dy, dx))
        else:
            angle = 0
        ant_rot_vals.append(f"{angle:.0f}")

    # Add celebration hold + reset
    # Ant stays at target during celebration, then jumps to start
    sr, sc = path[0]
    start_cx = gx + sc * STEP + CELL / 2
    start_cy = gy + sr * STEP + CELL / 2

    end_cx = float(ant_x_vals[-1])
    end_cy = float(ant_y_vals[-1])
    end_rot = ant_rot_vals[-1]
    start_rot = ant_rot_vals[0]

    # Keyframes for the full cycle: walk + celebrate + reset
    all_times = list(step_times)
    all_times.append(walk_dur)                          # arrival at target
    all_times.append(walk_dur + celebrate_dur)           # end celebration
    all_times.append(total_dur)                          # loop start

    all_x = list(ant_x_vals) + [f"{end_cx:.1f}", f"{start_cx:.1f}", f"{start_cx:.1f}"]
    all_y = list(ant_y_vals) + [f"{end_cy:.1f}", f"{start_cy:.1f}", f"{start_cy:.1f}"]
    all_rot = list(ant_rot_vals) + [end_rot, start_rot, start_rot]

    # Ant opacity: walks visible, celebrate flash, reset invisible briefly
    all_op_times = [0, walk_dur, walk_dur + 0.2, walk_dur + celebrate_dur - 0.3,
                    walk_dur + celebrate_dur, total_dur]
    all_op_vals = [1.0, 1.0, 1.0, 1.0, 0.0, 1.0]

    kt_walk = _kt(all_times, total_dur)
    x_str = ";".join(all_x)
    y_str = ";".join(all_y)
    rot_str = ";".join(all_rot)

    kt_op = _kt(all_op_times, total_dur)
    op_str = ";".join(f"{v}" for v in all_op_vals)

    # Ant body group  — drawn at origin (0,0), translated by animation
    # Body: 3 segments + 6 legs + 2 antennae + head
    ant_color = "#cc6633"
    ant_dark = "#8b4513"
    ant_leg = "#995522"
    ant_size = 4.5  # half-body length

    s.append(f'<g opacity="1">')
    s.append(
        f'<animate attributeName="opacity" dur="{total_dur}s" '
        f'repeatCount="indefinite" keyTimes="{kt_op}" values="{op_str}"/>'
    )

    # We animate via a nested structure:
    # Outer <g> moves X, inner <g> moves Y, innermost <g> rotates
    s.append(f'<g>')
    s.append(
        f'<animateTransform attributeName="transform" type="translate" '
        f'dur="{total_dur}s" repeatCount="indefinite" '
        f'keyTimes="{kt_walk}" '
        f'values="{";".join(f"{x} 0" for x in all_x)}"/>'
    )

    s.append(f'<g>')
    s.append(
        f'<animateTransform attributeName="transform" type="translate" '
        f'dur="{total_dur}s" repeatCount="indefinite" '
        f'keyTimes="{kt_walk}" '
        f'values="{";".join(f"0 {y}" for y in all_y)}"/>'
    )

    # Rotation group
    s.append(f'<g>')
    s.append(
        f'<animateTransform attributeName="transform" type="rotate" '
        f'dur="{total_dur}s" repeatCount="indefinite" '
        f'keyTimes="{kt_walk}" '
        f'values="{";".join(f"{r} 0 0" for r in all_rot)}"/>'
    )

    # ── Ant body drawn at (0,0) facing right ──
    # Abdomen (rear)
    s.append(f'<ellipse cx="-{ant_size}" cy="0" rx="3" ry="2.2" fill="{ant_color}"/>')
    # Thorax (middle)
    s.append(f'<ellipse cx="0" cy="0" rx="2.5" ry="2" fill="{ant_dark}"/>')
    # Head
    s.append(
        f'<ellipse cx="{ant_size - 0.5}" cy="0" rx="2" ry="1.8" fill="{ant_color}" '
        f'filter="url(#glo)"/>'
    )
    # Eyes
    s.append(f'<circle cx="{ant_size + 0.8}" cy="-0.8" r="0.5" fill="#ffffff"/>')
    s.append(f'<circle cx="{ant_size + 0.8}" cy="0.8" r="0.5" fill="#ffffff"/>')

    # Antennae (curved lines)
    s.append(
        f'<line x1="{ant_size + 1}" y1="-1" x2="{ant_size + 4}" y2="-3.5" '
        f'stroke="{ant_leg}" stroke-width="0.5" stroke-linecap="round">'
        f'<animate attributeName="y2" values="-3.5;-4.2;-3.5" dur="0.4s" repeatCount="indefinite"/>'
        f'</line>'
    )
    s.append(
        f'<line x1="{ant_size + 1}" y1="1" x2="{ant_size + 4}" y2="3.5" '
        f'stroke="{ant_leg}" stroke-width="0.5" stroke-linecap="round">'
        f'<animate attributeName="y2" values="3.5;4.2;3.5" dur="0.4s" '
        f'begin="0.1s" repeatCount="indefinite"/>'
        f'</line>'
    )

    # Legs (3 pairs, animated walking)
    leg_positions = [-3.5, 0, 3.0]  # x positions along body
    for li, lx in enumerate(leg_positions):
        phase = li * 0.12
        # Top leg
        s.append(
            f'<line x1="{lx}" y1="-2" x2="{lx - 0.5}" y2="-5" '
            f'stroke="{ant_leg}" stroke-width="0.6" stroke-linecap="round">'
            f'<animate attributeName="x2" values="{lx - 1};{lx + 1};{lx - 1}" '
            f'dur="0.3s" begin="{phase}s" repeatCount="indefinite"/>'
            f'<animate attributeName="y2" values="-5;-4.5;-5" '
            f'dur="0.3s" begin="{phase}s" repeatCount="indefinite"/>'
            f'</line>'
        )
        # Bottom leg
        s.append(
            f'<line x1="{lx}" y1="2" x2="{lx + 0.5}" y2="5" '
            f'stroke="{ant_leg}" stroke-width="0.6" stroke-linecap="round">'
            f'<animate attributeName="x2" values="{lx + 1};{lx - 1};{lx + 1}" '
            f'dur="0.3s" begin="{phase}s" repeatCount="indefinite"/>'
            f'<animate attributeName="y2" values="5;4.5;5" '
            f'dur="0.3s" begin="{phase}s" repeatCount="indefinite"/>'
            f'</line>'
        )

    s.append("</g>")  # rotation
    s.append("</g>")  # Y translate
    s.append("</g>")  # X translate
    s.append("</g>")  # opacity

    # ── Legend ─────────────────────────────────────────────────
    ly = gy + grid_h + legend_gap + 10
    leg_cell = 10
    leg_gap_px = 3
    leg_w_px = len(HEAT) * (leg_cell + leg_gap_px)
    lx_start = gx + grid_w - leg_w_px - 40

    s.append(
        f'<text x="{lx_start - 4}" y="{ly + 3}" text-anchor="end" style="{leg_style}">'
        f"Less</text>"
    )
    for i, c in enumerate(HEAT):
        rx = lx_start + i * (leg_cell + leg_gap_px)
        s.append(
            f'<rect x="{rx}" y="{ly - 4}" width="{leg_cell}" height="{leg_cell}" '
            f'rx="2" fill="{c}" stroke="{BORDER}" stroke-width=".5"/>'
        )
    last_rx = lx_start + len(HEAT) * (leg_cell + leg_gap_px)
    s.append(f'<text x="{last_rx + 4}" y="{ly + 3}" style="{leg_style}">More</text>')

    # Ant icon + label in legend
    ant_lx = gx + 2
    s.append(
        f'<text x="{ant_lx}" y="{ly + 3}" style="{leg_style}">'
        f'🐜 A* path · walls cost more</text>'
    )

    s.append("</svg>")
    return "\n".join(s)


def _kt(times, total):
    """Convert list of absolute seconds → SMIL keyTimes string 0..1."""
    kt = [max(0.0, min(1.0, round(t / total, 6))) for t in times]
    for i in range(1, len(kt)):
        if kt[i] <= kt[i - 1]:
            kt[i] = round(kt[i - 1] + 0.00001, 6)
    kt[0] = 0.0
    kt[-1] = 1.0
    return ";".join(f"{k:.6f}" for k in kt)


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
