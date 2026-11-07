"""
The robot of destbreso.com in pixels, rendered from its 3D model's own measurements and materials (the site's
model of it): an orthographic ray march of signed distance fields, lit from the upper left with cast
shadows, quantized to a few tones a material, outlined where a part ends. Its face's eyes follow the site's flat face
drawing (sizes as fractions of the screen). Units are millimetres, y up, its front toward +z. Needs numpy.
"""
import json, math, struct, sys, zlib
import numpy as np

# ---------- signed distances ----------

def rbox(p, c, b, r):
    q = np.abs(p - c) - (np.array(b) / 2 - r)
    return np.linalg.norm(np.maximum(q, 0), axis=-1) + np.minimum(q.max(axis=-1), 0) - r

def cyl_y(p, c, r, h):
    d = p - c
    a = np.sqrt(d[..., 0] ** 2 + d[..., 2] ** 2) - r
    b = np.abs(d[..., 1]) - h / 2
    return np.minimum(np.maximum(a, b), 0) + np.sqrt(np.maximum(a, 0) ** 2 + np.maximum(b, 0) ** 2)

def cyl_x(p, c, r, h):
    d = p - c
    a = np.sqrt(d[..., 1] ** 2 + d[..., 2] ** 2) - r
    b = np.abs(d[..., 0]) - h / 2
    return np.minimum(np.maximum(a, b), 0) + np.sqrt(np.maximum(a, 0) ** 2 + np.maximum(b, 0) ** 2)

def sphere(p, c, r):
    return np.linalg.norm(p - c, axis=-1) - r

def rrect2(x, y, w, h, r):
    qx = np.abs(x) - (w / 2 - r)
    qy = np.abs(y) - (h / 2 - r)
    return np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0) - r

def plate_z(p, c, w, h, r, depth):
    d = p - c
    a = rrect2(d[..., 0], d[..., 1], w, h, r)
    b = np.abs(d[..., 2]) - depth / 2
    return np.minimum(np.maximum(a, b), 0) + np.sqrt(np.maximum(a, 0) ** 2 + np.maximum(b, 0) ** 2)

def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

SHELL, GRAPHITE, RUBBER, GLASS, GREEN = 1, 2, 3, 4, 5
NECK = np.array([0.0, 68.0, 0.0])

class Pose:
    def __init__(self, body_yaw=0.0, head_yaw=0.0, head_pitch=0.0, head_roll=0.0, lift=0.0):
        self.body = rot_y(body_yaw)
        self.head = rot_y(head_yaw) @ rot_x(head_pitch) @ rot_z(head_roll)
        self.lift = lift

def to_body(p, pose):
    q = p.copy()
    q[..., 1] -= pose.lift
    return q @ pose.body  # inverse rotation (orthonormal): row vectors times R

def to_head(pb, pose):
    return (pb - NECK) @ pose.head  # head-local, origin at the neck's top

HEAD_PARTS = (11, 12, 13, 14)

def scene(p, pose, only=None):
    """Distance and material at world points p (N, 3); `only` keeps the body's parts or the head's."""
    b = to_body(p, pose)
    h = to_head(b, pose)
    parts = []
    for side in (-1, 1):
        parts.append((rbox(b, np.array([side * 17, 6.5, 3]), (26, 13, 38), 6.2), RUBBER))
        parts.append((cyl_x(b, np.array([side * 30.5, 6.5, 3]), 5.5, 2.0), GRAPHITE))
        parts.append((cyl_y(b, np.array([side * 17, 19, 0]), 6.25, 14), GRAPHITE))
        parts.append((sphere(b, np.array([side * 17, 27, 0]), 7.2), SHELL))
    parts.append((rbox(b, np.array([0, 44, 0]), (46, 32, 34), 13.5), SHELL))
    parts.append((plate_z(b, np.array([0, 43, 17.2]), 28, 19, 4, 2.4), GRAPHITE))
    parts.append((cyl_y(b, np.array([0, 64, 0]), 7.6, 10), GRAPHITE))
    parts.append((rbox(h, np.array([0, 31, 0]), (76, 62, 58), 19), SHELL))
    parts.append((plate_z(h, np.array([0, 32, 28.4]), 64.5, 54.5, 13.5, 3.6), GLASS))
    parts.append((cyl_y(h, np.array([22, 68, -10]), 1.15, 16), GRAPHITE))
    parts.append((sphere(h, np.array([22, 77.5, -10]), 2.8), GREEN))
    if only is not None:
        keep = [i for i in range(len(parts)) if (i in HEAD_PARTS) == (only == "head")]
        parts = [parts[i] if i in keep else (np.full(len(p), 1e9), parts[i][1]) for i in range(len(parts))]
    d = np.stack([x for x, _ in parts], axis=-1)
    k = d.argmin(axis=-1)
    mats = np.array([m for _, m in parts])
    return d.min(axis=-1), mats[k], k

# ---------- the face ----------

def eye_masks(x, y, eyes):
    """In the screen's own plane (mm, y up, origin at its middle): what the eyes light. Returns (core, eye, glow1,
    glow2) booleans. `eyes` is a dict: look (x, y in -1..1), shut (0..1), kind (open, happy, content, squint)."""
    W, H = 57.5, 42.5
    lx, ly = eyes.get("look", (0, 0))
    shut = eyes.get("shut", 0.0)
    kind = eyes.get("kind", "open")
    dist = np.full(x.shape, 1e9)
    if kind == "none":
        return dist
    if kind == "logo":
        # the site's mark, as its favicon draws it (512 units: a chevron and the cursor), scaled onto the screen
        k = 0.118
        def seg(ax, ay, bx, by, r):
            ax, ay, bx, by = (ax - 276) * k, (256 - ay) * k, (bx - 276) * k, (256 - by) * k
            px, py = x - ax, y - ay
            vx, vy = bx - ax, by - ay
            hh = np.clip((px * vx + py * vy) / (vx * vx + vy * vy), 0, 1)
            return np.hypot(px - vx * hh, py - vy * hh) - r
        r = 21 * k
        dist = np.minimum(seg(186, 166, 266, 256, r), seg(266, 256, 186, 346, r))
        if eyes.get("cursor", True):
            dist = np.minimum(dist, seg(291, 326, 367, 326, r))
        return dist
    if kind == "heart":
        for side in (-1, 1):
            cx = side * W * 0.2
            sc = 7.6
            px, py = (x - cx) / sc, (y + 0.5) / sc
            # the classic implicit heart; near its edge q's cube root is about twice the distance, in its units
            q = (px ** 2 + py ** 2 - 1) ** 3 - px ** 2 * py ** 3
            dist = np.minimum(dist, np.sign(q) * np.abs(q) ** (1 / 3) / 2 * sc)
        return dist
    for side in (-1, 1):
        cx = side * W * 0.2 + lx * W * 0.1
        cy = ly * H * 0.12
        ew = W * 0.2 * eyes.get("wide", 1.0)
        if kind in ("happy", "content"):
            r = ew * 0.48
            oy = -4.0 if kind == "happy" else 4.0
            dx, dy = x - cx, y - (cy + oy)
            ang = np.arctan2(dy, dx)
            ring = np.abs(np.sqrt(dx ** 2 + dy ** 2) - r) - 1.9
            keep = (dy > 0) if kind == "happy" else (dy < 0)
            cap = np.minimum(np.hypot(x - (cx - r), y - (cy + oy)), np.hypot(x - (cx + r), y - (cy + oy))) - 1.9
            dd = np.where(keep, ring, cap)
            dist = np.minimum(dist, dd)
            continue
        eh = H * 0.42 * eyes.get("tall", 1.0)
        if kind == "squint":
            eh = H * 0.16
        sh_ = shut if not (kind == "wink" and side == 1) else 1.0
        eh = max(H * 0.05, eh * (1 - sh_))
        rr = min(ew, eh) * 0.3
        dist = np.minimum(dist, rrect2(x - cx, y - cy, ew, eh, rr))
    return dist

PX = 1.7  # millimetres a pixel

def render(pose, eyes, only=None, w=72, h=100, yaw_cam=0.0, pitch_cam=math.radians(9), cx=0.0, cy=72.0):
    js, is_ = np.meshgrid(np.arange(w), np.arange(h))
    u = (js + 0.5 - w / 2) * PX + cx
    v = (h / 2 - (is_ + 0.5)) * PX + cy
    cam = rot_y(yaw_cam) @ rot_x(-pitch_cam)
    right, up, fwd = cam[:, 0], cam[:, 1], cam[:, 2]
    o = u[..., None] * right + v[..., None] * up + 400 * fwd
    o = o.reshape(-1, 3)
    d = -fwd
    t = np.zeros(len(o))
    hit = np.zeros(len(o), bool)
    alive = np.ones(len(o), bool)
    for _ in range(160):
        p = o[alive] + t[alive, None] * d
        dist, _, _ = scene(p, pose, only)
        t[alive] += dist
        idx = np.nonzero(alive)[0]
        done = dist < 0.02
        hit[idx[done]] = True
        far = t[idx] > 800
        alive[idx[done | far]] = False
        if not alive.any():
            break
    p = o + t[:, None] * d
    dist, mat, part = scene(p, pose, only)
    e = 0.05
    n = np.stack([scene(p + np.array(a) * e, pose, only)[0] - scene(p - np.array(a) * e, pose, only)[0] for a in ([1, 0, 0], [0, 1, 0], [0, 0, 1])], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
    L = np.array([-0.55, 0.75, 0.62]); L /= np.linalg.norm(L)
    lam = np.clip(n @ L, 0, 1)
    so = p + n * 0.6
    st = np.zeros(len(so)); sh = np.zeros(len(so), bool); live = hit.copy()
    for _ in range(80):
        q = so[live] + st[live, None] * L
        dd, _, _ = scene(q, pose, None)
        st[live] += np.maximum(dd, 0.3)
        idx = np.nonzero(live)[0]
        blocked = dd < 0.05
        sh[idx[blocked]] = True
        live[idx[blocked | (st[idx] > 200)]] = False
        if not live.any():
            break
    lam = np.where(sh, lam * 0.25, lam)
    view = -d
    hv = (L + view); hv /= np.linalg.norm(hv)
    spec = np.clip(n @ hv, 0, 1) ** 40
    mat = np.where(hit, mat, 0)
    depth = np.where(hit, t, 1e9)
    # the face: what lies on the screen, in head-local coordinates
    b = to_body(p, pose)
    hl = to_head(b, pose)
    sx, sy = hl[:, 0], hl[:, 1] - 32
    on_glass = (mat == GLASS) & (hl[:, 2] > 29.0)
    eyed = eye_masks(sx, sy, eyes)
    cam_lens = on_glass & (np.hypot(sx - 0, sy - 24.5) < 2.4)
    lamp = on_glass & (np.hypot(sx - 12, sy - 24.5) < 1.5)
    bl = b - np.array([0, 43, 18.4])
    on_belly = (mat == GRAPHITE) & (part == 9) & (bl[:, 2] > -0.5)
    dots = np.zeros(len(p), bool)
    for k in range(12):
        dx = -7.5 + (k % 4) * 5.0
        dy = 4.0 - (k // 4) * 4.5
        dots |= np.hypot(bl[:, 0] - dx, bl[:, 1] - dy) < 1.05
    led = on_belly & (np.hypot(bl[:, 0] - 9.5, bl[:, 1] + 7.5) < 1.4)
    proj = (mat == SHELL) & (part == 11) & (hl[:, 2] > 26) & (np.hypot(hl[:, 0], hl[:, 1] - 7.5) < 2.6)
    shape = (h, w)
    return dict(mat=mat.reshape(shape), lam=lam.reshape(shape), spec=spec.reshape(shape), depth=depth.reshape(shape),
                part=part.reshape(shape), ndv=(n @ view).reshape(shape), eyed=np.where(on_glass, eyed, 1e9).reshape(shape),
                on_glass=on_glass.reshape(shape), cam=cam_lens.reshape(shape), lamp=lamp.reshape(shape),
                dots=(on_belly & dots).reshape(shape), led=led.reshape(shape), proj=proj.reshape(shape), ny=n[:, 1].reshape(shape), sx=sx.reshape(shape), sy=sy.reshape(shape))

# ---------- palette and tones ----------

PAL = {
    "shell": ["#fffdf8", "#f3efe7", "#e4dfd4", "#cec7b9", "#aea696", "#878071"],
    "shell_out": "#5f594f",
    "graphite": ["#5a5f68", "#43474e", "#33363c", "#26282d", "#1b1c20"],
    "graphite_out": "#101114",
    "rubber": ["#3a3c40", "#26272a", "#1a1b1d", "#111214"],
    "rubber_out": "#08090a",
    "glass": ["#2c3337", "#161a1d", "#0b0d0f", "#050607"],
    "glass_rim": "#3a4246",
    "eye_core": "#d4fbcf", "eye": "#a0e299", "glow1": "#3e7a45", "glow2": "#1a3320",
    "green_hi": "#e3ffdf",
    "lens": "#020304", "lens_ring": "#4a5259", "lens_hi": "#8da2b3",
    "lamp": "#2a2a26",
    "led": "#a0e299",
    "dot": "#0a0b0c",
}

def tone(levels, lam, bias=0.0):
    k = np.clip(((1 - lam) + bias) * (len(levels) - 0.01), 0, len(levels) - 1).astype(int)
    return k

def colorize(R):
    h, w = R["mat"].shape
    out = np.full((h, w), "", dtype=object)
    mat, lam, spec = R["mat"], R["lam"], R["spec"]
    amb = 0.32
    li = np.clip(amb + (1 - amb) * lam, 0, 1)
    # shell: four tones by light, the brightest only where the highlight is
    sh = PAL["shell"]
    k = np.clip(((1 - li) * 5.2).astype(int) + 1, 1, 5)
    k = np.where(spec > 0.55, 0, k)
    for i in range(h):
        for j in range(w):
            m = mat[i, j]
            if m == SHELL:
                out[i, j] = sh[k[i, j]]
            elif m == GRAPHITE and R["part"][i, j] == 13:
                out[i, j] = "#7c828b" if li[i, j] > 0.5 else "#5d636b"
            elif m == GRAPHITE:
                g = PAL["graphite"]
                out[i, j] = g[0] if spec[i, j] > 0.6 else g[min(4, int((1 - li[i, j]) * 4.6) + 1)]
            elif m == RUBBER:
                r = PAL["rubber"]
                out[i, j] = r[min(3, int((1 - li[i, j]) * 3.6))]
            elif m == GLASS:
                gl = PAL["glass"]
                rim = R["ndv"][i, j] < 0.55
                if rim:
                    out[i, j] = PAL["glass_rim"]
                else:
                    out[i, j] = gl[2] if R["ny"][i, j] > 0.2 else gl[3]
                    gx, gy = R["sx"][i, j], R["sy"][i, j]
                    band = gx * 0.7 + gy
                    if 5.5 < band < 12.5 and gx < -11 and gy > 6:
                        out[i, j] = gl[1]
                    if 7.5 < band < 9.8 and gx < -15 and gy > 9:
                        out[i, j] = gl[0]
            elif m == GREEN:
                out[i, j] = PAL["green_hi"] if spec[i, j] > 0.4 else PAL["eye"]
    # the face's lights, over the glass
    ed = R["eyed"]
    for i in range(h):
        for j in range(w):
            if not R["on_glass"][i, j]:
                continue
            dd = ed[i, j]
            if dd < -1.6 * PX * 0.9:
                out[i, j] = PAL["eye_core"]
            elif dd < 0:
                out[i, j] = PAL["eye"]
            elif dd < PX * 0.9:
                out[i, j] = PAL["glow1"]
            elif dd < PX * 1.9:
                out[i, j] = PAL["glow2"]
            if R["cam"][i, j]:
                out[i, j] = PAL["lens"]
    out = np.where(R["dots"], PAL["dot"], out)
    out = np.where(R["led"], PAL["led"], out)
    out = np.where(R["proj"], PAL["lens"], out)
    return out

def outline(R, img):
    """A darker edge where the robot meets nothing, or where a nearer part covers a farther one."""
    h, w = img.shape
    mat, depth, part = R["mat"], R["depth"], R["part"]
    res = img.copy()
    darker = {SHELL: PAL["shell_out"], GRAPHITE: PAL["graphite_out"], RUBBER: PAL["rubber_out"], GLASS: "#000000", GREEN: "#3e7a45"}
    for i in range(h):
        for j in range(w):
            m = mat[i, j]
            if not m or part[i, j] in (13, 14):
                continue
            edge = False
            for di, dj in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                a, b = i + di, j + dj
                if not (0 <= a < h and 0 <= b < w) or not mat[a, b]:
                    edge = True
                    break
                if part[a, b] != part[i, j] and depth[a, b] < depth[i, j] - 3.0:
                    edge = True
                    break
            if edge:
                res[i, j] = darker[m]
    return res

# ---------- output ----------

def hexrgb(c):
    return tuple(int(c[k:k + 2], 16) for k in (1, 3, 5))

def png(img, path, scale=6, bg="#0d1117"):
    h, w = img.shape
    rows = []
    for i in range(h):
        row = bytearray()
        for j in range(w):
            c = img[i, j] or bg
            row += bytes(hexrgb(c)) * scale
        for _ in range(scale):
            rows.append(b"\x00" + bytes(row))
    raw = b"".join(rows)
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w * scale, h * scale, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    open(path, "wb").write(data)

def sheet(imgs, path, scale=5, bg="#0d1117", gap=4):
    h = max(i.shape[0] for i in imgs)
    w = sum(i.shape[1] for i in imgs) + gap * (len(imgs) - 1)
    canvas = np.full((h, w), "", dtype=object)
    x = 0
    for im in imgs:
        canvas[: im.shape[0], x: x + im.shape[1]] = im
        x += im.shape[1] + gap
    png(canvas, path, scale, bg)

def frame(pose, eyes, **kw):
    R = render(pose, eyes, **kw)
    return outline(R, colorize(R))

if __name__ == "__main__":  # a quick look at a few poses
    out = sys.argv[1]
    by = math.radians(-22)
    f = [
        frame(Pose(body_yaw=by, head_yaw=math.radians(14)), {"look": (0.2, 0)}),
        frame(Pose(body_yaw=by, head_yaw=math.radians(14)), {"look": (0.2, 0), "shut": 0.85}),
        frame(Pose(body_yaw=by, head_yaw=math.radians(-12)), {"look": (-0.8, 0)}),
        frame(Pose(body_yaw=by, head_yaw=math.radians(10), head_pitch=math.radians(-10)), {"look": (0.1, 0.9)}),
        frame(Pose(body_yaw=by, head_yaw=math.radians(16), head_roll=math.radians(9)), {"kind": "happy"}),
    ]
    sheet(f, out)
