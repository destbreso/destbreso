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

    # ═══════════════════════════════════════════════════════════
    #  MULTI-PATH GENERATION — 10 diverse A* paths
    # ═══════════════════════════════════════════════════════════
    NUM_PATHS = 10
    MIN_MANHATTAN = 12          # targets must be at least this far
    CELEBRATE_DUR = 1.5         # burst at each target
    TELEPORT_DUR = 0.6          # invisible gap between paths

    rng = random.Random(42)

    all_cells = [(r, c) for r in range(7) for c in range(24)]
    empties = [(r, c) for r, c in all_cells if matrix[r][c] == 0]
    lights  = [(r, c) for r, c in all_cells if 0 < matrix[r][c] / max_val <= 0.25]
    mids    = [(r, c) for r, c in all_cells if 0.25 < matrix[r][c] / max_val <= 0.5]
    heavies = [(r, c) for r, c in all_cells if matrix[r][c] / max_val > 0.5]

    segments = []           # one dict per path segment
    used_pairs = set()
    global_t = 0.0

    for pi in range(NUM_PATHS):
        # ── Start: prefer empty / light cells ──
        start_pool = list(empties + lights) if (empties + lights) else list(all_cells)
        rng.shuffle(start_pool)

        # ── Target: prefer heavy / mid cells, far from start ──
        target_pool = list(heavies + mids) if (heavies + mids) else list(lights + empties)
        if not target_pool:
            target_pool = list(all_cells)

        best_start, best_target, best_dist = None, None, -1

        for s_cand in start_pool[:30]:
            for t_cand in target_pool:
                d = abs(s_cand[0] - t_cand[0]) + abs(s_cand[1] - t_cand[1])
                if d >= MIN_MANHATTAN and (s_cand, t_cand) not in used_pairs and d > best_dist:
                    best_start, best_target, best_dist = s_cand, t_cand, d

        if best_start is None:
            # Relax min-distance — just pick furthest unused pair
            for s_cand in start_pool[:15]:
                sorted_t = sorted(
                    target_pool,
                    key=lambda t: -(abs(t[0] - s_cand[0]) + abs(t[1] - s_cand[1]))
                )
                for t_cand in sorted_t[:5]:
                    if (s_cand, t_cand) not in used_pairs:
                        best_start, best_target = s_cand, t_cand
                        best_dist = abs(best_start[0] - best_target[0]) + abs(best_start[1] - best_target[1])
                        break
                if best_start:
                    break

        if best_start is None:
            best_start = start_pool[0]
            best_target = max(target_pool,
                              key=lambda t: abs(t[0] - best_start[0]) + abs(t[1] - best_start[1]))

        used_pairs.add((best_start, best_target))

        seg_path = astar(matrix, best_start, best_target, max_val)

        # ── Step timing — 20× slower than original ──
        step_times = []
        t = global_t
        for r, c in seg_path:
            ratio = matrix[r][c] / max_val
            dur = 2.4 + 9.6 * ratio       # original: 0.12 + 0.48*ratio
            step_times.append(round(t, 4))
            t += dur
        walk_end = round(t, 4)

        segments.append({
            "start":      best_start,
            "target":     best_target,
            "path":       seg_path,
            "step_times": step_times,
            "walk_start": round(global_t, 4),
            "walk_end":   walk_end,
            "celeb_start": walk_end,
            "celeb_end":  round(walk_end + CELEBRATE_DUR, 4),
        })

        global_t = round(walk_end + CELEBRATE_DUR + TELEPORT_DUR, 4)

    total_dur = round(global_t, 3)

    # ── Cell eat-timing: first arrival across ALL paths ───────
    cell_first_eat = {}      # (r,c) → earliest arrival time
    for seg in segments:
        for idx, (r, c) in enumerate(seg["path"]):
            t_arr = seg["step_times"][idx]
            if (r, c) not in cell_first_eat or t_arr < cell_first_eat[(r, c)]:
                cell_first_eat[(r, c)] = t_arr

    path_cells = set()
    for seg in segments:
        for rc in seg["path"]:
            path_cells.add(rc)

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
    s.append(
        '<filter id="glo" x="-60%" y="-60%" width="220%" height="220%">'
        '<feGaussianBlur stdDeviation="2" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
        '</filter>'
    )
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
    #  HEATMAP CELLS — eaten on FIRST visit across all paths
    # ══════════════════════════════════════════════════════════
    restore_start = round(total_dur - 3.0, 3)
    restore_end   = round(total_dur - 1.0, 3)

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
                if ratio <= 0.25:   color = HEAT[1]
                elif ratio <= 0.50: color = HEAT[2]
                elif ratio <= 0.75: color = HEAT[3]
                else:               color = HEAT[4]

            on_path = (ri, h) in path_cells
            arrival = cell_first_eat.get((ri, h))

            if on_path and val > 0 and arrival is not None:
                eat_start = round(arrival, 3)
                eat_flash = round(eat_start + 0.08, 3)
                eat_done  = round(eat_start + 0.15 + 0.5 * ratio, 3)

                kt = _kt(
                    [0, eat_start, eat_flash, eat_done,
                     restore_start, restore_end, total_dur],
                    total_dur,
                )
                eaten_color = HEAT[0]
                fill_vals = (
                    f"{color};{color};#ffffff;{eaten_color};"
                    f"{eaten_color};{color};{color}"
                )
                s.append(
                    f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                    f'rx="3" fill="{color}">'
                    f'<animate attributeName="fill" dur="{total_dur}s" '
                    f'repeatCount="indefinite" keyTimes="{kt}" values="{fill_vals}"/>'
                )
                if ratio > 0.3:
                    shake_kt = _kt(
                        [0, eat_start, eat_start + 0.04,
                         eat_start + 0.08, eat_start + 0.12, total_dur],
                        total_dur,
                    )
                    s.append(
                        f'<animate attributeName="x" dur="{total_dur}s" '
                        f'repeatCount="indefinite" keyTimes="{shake_kt}" '
                        f'values="{x};{x+1};{x-1};{x+1};{x};{x}"/>'
                    )
                s.append("</rect>")

            elif on_path and val == 0 and arrival is not None:
                hl_start = round(arrival, 3)
                hl_end   = round(arrival + 0.3, 3)
                kt = _kt(
                    [0, hl_start, hl_end, restore_start, total_dur],
                    total_dur,
                )
                s.append(
                    f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                    f'rx="3" fill="{color}" opacity="1">'
                    f'<animate attributeName="opacity" dur="{total_dur}s" '
                    f'repeatCount="indefinite" keyTimes="{kt}" '
                    f'values="1;1;0.6;0.6;1"/>'
                    f'</rect>'
                )
            else:
                s.append(
                    f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                    f'rx="3" fill="{color}"/>'
                )

    # ══════════════════════════════════════════════════════════
    #  ANT TRAILS — per-segment, appear then fade
    # ══════════════════════════════════════════════════════════
    for seg in segments:
        for idx in range(len(seg["path"])):
            r, c = seg["path"][idx]
            cx = gx + c * STEP + CELL / 2
            cy = gy + r * STEP + CELL / 2
            t_arrive = seg["step_times"][idx]

            t_on   = round(t_arrive + 0.05, 3)
            t_glow = round(t_arrive + 0.2, 3)
            t_fade_start = round(seg["celeb_end"] - 0.3, 3)
            t_fade_end   = round(seg["celeb_end"] + TELEPORT_DUR * 0.5, 3)

            # Ensure monotonic
            if t_fade_start <= t_glow:
                t_fade_start = round(t_glow + 0.1, 3)
            if t_fade_end <= t_fade_start:
                t_fade_end = round(t_fade_start + 0.1, 3)

            kt = _kt(
                [0, t_on, t_glow, t_fade_start, t_fade_end, total_dur],
                total_dur,
            )
            s.append(
                f'<circle cx="{cx}" cy="{cy}" r="3" fill="{ACCENT}" opacity="0">'
                f'<animate attributeName="opacity" dur="{total_dur}s" '
                f'repeatCount="indefinite" keyTimes="{kt}" '
                f'values="0;0.6;0.35;0.35;0;0"/>'
                f'</circle>'
            )

    # ══════════════════════════════════════════════════════════
    #  FOOD TARGETS — pulsing marker per segment
    # ══════════════════════════════════════════════════════════
    for seg in segments:
        tr, tc = seg["target"]
        tx = gx + tc * STEP + CELL / 2
        ty_food = gy + tr * STEP + CELL / 2

        t_visible = round(seg["walk_start"], 3)
        t_eat  = round(seg["step_times"][-1], 3) if seg["step_times"] else t_visible
        t_gone = round(t_eat + 0.3, 3)

        kt_food = _kt([0, t_visible, t_eat, t_gone, total_dur], total_dur)

        # Outer pulse ring
        s.append(
            f'<circle cx="{tx}" cy="{ty_food}" r="6" fill="none" '
            f'stroke="{ACCENT}" stroke-width="1.2" opacity="0">'
            f'<animate attributeName="r" values="5;8;5" dur="1.2s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" dur="{total_dur}s" '
            f'repeatCount="indefinite" keyTimes="{kt_food}" values="0;0.7;0.7;0;0"/>'
            f'</circle>'
        )
        # Inner dot
        s.append(
            f'<circle cx="{tx}" cy="{ty_food}" r="2.5" fill="{ACCENT}" opacity="0">'
            f'<animate attributeName="opacity" dur="{total_dur}s" '
            f'repeatCount="indefinite" keyTimes="{kt_food}" values="0;0.9;0.9;0;0"/>'
            f'</circle>'
        )

    # ══════════════════════════════════════════════════════════
    #  CELEBRATIONS — burst rings at each target
    # ══════════════════════════════════════════════════════════
    for seg in segments:
        tr, tc = seg["target"]
        tx = gx + tc * STEP + CELL / 2
        ty_food = gy + tr * STEP + CELL / 2
        cs = round(seg["celeb_start"], 3)
        cp = round(cs + 0.3, 3)
        ce = round(seg["celeb_end"], 3)

        for ring_i in range(3):
            delay = ring_i * 0.15
            rs = round(cs + delay, 3)
            rp = round(cp + delay, 3)
            re = ce
            kt_r = _kt([0, rs, rp, re, total_dur], total_dur)
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
    #  ANT — procedural body chained across all path segments
    # ══════════════════════════════════════════════════════════

    # ── Position keyframes (walk + hold-at-target for each seg) ──
    pos_times = []
    pos_x = []
    pos_y = []
    pos_rot = []

    for si, seg in enumerate(segments):
        seg_path = seg["path"]
        for idx, (r, c) in enumerate(seg_path):
            cx = gx + c * STEP + CELL / 2
            cy = gy + r * STEP + CELL / 2
            pos_times.append(seg["step_times"][idx])
            pos_x.append(cx)
            pos_y.append(cy)

            if idx < len(seg_path) - 1:
                nr, nc = seg_path[idx + 1]
                angle = math.degrees(math.atan2(nr - r, nc - c))
            elif idx > 0:
                pr, pc = seg_path[idx - 1]
                angle = math.degrees(math.atan2(r - pr, c - pc))
            else:
                angle = 0.0
            pos_rot.append(angle)

        # Hold at target through celebration
        tr, tc = seg["target"]
        end_cx = gx + tc * STEP + CELL / 2
        end_cy = gy + tr * STEP + CELL / 2
        pos_times.append(seg["celeb_end"])
        pos_x.append(end_cx)
        pos_y.append(end_cy)
        pos_rot.append(pos_rot[-1])

    # Close cycle — back to the very first start for seamless loop
    first_start = segments[0]["start"]
    first_cx = gx + first_start[1] * STEP + CELL / 2
    first_cy = gy + first_start[0] * STEP + CELL / 2
    pos_times.append(total_dur)
    pos_x.append(first_cx)
    pos_y.append(first_cy)
    pos_rot.append(pos_rot[0])

    # ── Opacity keyframes: visible walk+celebrate, hidden teleport ──
    op_times = []
    op_vals  = []

    for si, seg in enumerate(segments):
        ws = seg["walk_start"]
        ce = seg["celeb_end"]

        if si == 0:
            op_times.append(0.0)
            op_vals.append(1.0)
        else:
            # Reappear at new start
            op_times.append(round(ws - 0.05, 4))
            op_vals.append(0.0)
            op_times.append(round(ws, 4))
            op_vals.append(1.0)

        # Disappear at celebration end
        op_times.append(round(ce - 0.05, 4))
        op_vals.append(1.0)
        op_times.append(round(ce, 4))
        op_vals.append(0.0)

    # Stay invisible until loop restarts
    op_times.append(total_dur)
    op_vals.append(0.0)

    kt_pos = _kt(pos_times, total_dur)
    kt_op  = _kt(op_times, total_dur)
    op_str = ";".join(f"{v}" for v in op_vals)

    # ── Ant body group ────────────────────────────────────────
    ant_color = "#cc6633"
    ant_dark  = "#8b4513"
    ant_leg   = "#995522"
    ant_size  = 4.5

    s.append(f'<g opacity="1">')
    s.append(
        f'<animate attributeName="opacity" dur="{total_dur}s" '
        f'repeatCount="indefinite" keyTimes="{kt_op}" values="{op_str}"/>'
    )

    # Outer <g> → X translation
    s.append(f'<g>')
    s.append(
        f'<animateTransform attributeName="transform" type="translate" '
        f'dur="{total_dur}s" repeatCount="indefinite" '
        f'keyTimes="{kt_pos}" '
        f'values="{";".join(f"{v:.1f} 0" for v in pos_x)}"/>'
    )

    # Inner <g> → Y translation
    s.append(f'<g>')
    s.append(
        f'<animateTransform attributeName="transform" type="translate" '
        f'dur="{total_dur}s" repeatCount="indefinite" '
        f'keyTimes="{kt_pos}" '
        f'values="{";".join(f"0 {v:.1f}" for v in pos_y)}"/>'
    )

    # Innermost <g> → rotation
    s.append(f'<g>')
    s.append(
        f'<animateTransform attributeName="transform" type="rotate" '
        f'dur="{total_dur}s" repeatCount="indefinite" '
        f'keyTimes="{kt_pos}" '
        f'values="{";".join(f"{v:.0f} 0 0" for v in pos_rot)}"/>'
    )

    # ── Ant body drawn at (0,0) facing right ──
    s.append(f'<ellipse cx="-{ant_size}" cy="0" rx="3" ry="2.2" fill="{ant_color}"/>')
    s.append(f'<ellipse cx="0" cy="0" rx="2.5" ry="2" fill="{ant_dark}"/>')
    s.append(
        f'<ellipse cx="{ant_size - 0.5}" cy="0" rx="2" ry="1.8" fill="{ant_color}" '
        f'filter="url(#glo)"/>'
    )
    s.append(f'<circle cx="{ant_size + 0.8}" cy="-0.8" r="0.5" fill="#ffffff"/>')
    s.append(f'<circle cx="{ant_size + 0.8}" cy="0.8" r="0.5" fill="#ffffff"/>')

    # Antennae
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

    # Legs (3 pairs)
    leg_positions = [-3.5, 0, 3.0]
    for li, lx in enumerate(leg_positions):
        phase = li * 0.12
        s.append(
            f'<line x1="{lx}" y1="-2" x2="{lx - 0.5}" y2="-5" '
            f'stroke="{ant_leg}" stroke-width="0.6" stroke-linecap="round">'
            f'<animate attributeName="x2" values="{lx - 1};{lx + 1};{lx - 1}" '
            f'dur="0.3s" begin="{phase}s" repeatCount="indefinite"/>'
            f'<animate attributeName="y2" values="-5;-4.5;-5" '
            f'dur="0.3s" begin="{phase}s" repeatCount="indefinite"/>'
            f'</line>'
        )
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
