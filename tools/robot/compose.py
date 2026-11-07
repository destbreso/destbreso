"""
The robot as one animated SVG (assets/robot.svg): its body drawn once, a head for each way it turns, its eyes laid over
the head, and a long script of what it does, four minutes drawn from a seeded deck of behaviours (none twice in a row,
every one at least once), every change on one clock by CSS steps, since a README runs no JavaScript. Its antenna's light
and its belly's light each keep a clock of their own. Optionally a contact sheet of its states, for checking.
  python3 tools/robot/compose.py assets/robot.svg [sheet.png]
"""
import json, math, random, sys
import numpy as np
from render import Pose, render, colorize, outline, sheet, GREEN

BODY_YAW = math.radians(-22)
POSES = {
    "front": dict(head_yaw=14),
    "front_mid": dict(head_yaw=1),
    "left": dict(head_yaw=-12),
    "up_mid": dict(head_yaw=12, head_pitch=-5),
    "up": dict(head_yaw=10, head_pitch=-10),
    "tilt_r_mid": dict(head_yaw=15, head_roll=4.5),
    "tilt_r": dict(head_yaw=16, head_roll=9),
    "tilt_l_mid": dict(head_yaw=14, head_roll=-3),
    "tilt_l": dict(head_yaw=13, head_roll=-6),
    "nod": dict(head_yaw=12, head_pitch=5),
    "down": dict(head_yaw=10, head_pitch=9),
}

def pose(name):
    a = POSES[name]
    return Pose(body_yaw=BODY_YAW, head_yaw=math.radians(a.get("head_yaw", 0)), head_pitch=math.radians(a.get("head_pitch", 0)),
                head_roll=math.radians(a.get("head_roll", 0)))

EYES = {}

def E(**kw):
    """An eye state by what it is; the same state is drawn once however often it is used."""
    kw.setdefault("look", (0.2, 0))
    kw["look"] = tuple(round(v * 4) / 4 for v in kw["look"])  # a quarter of their room: as far as a pixel goes
    key = json.dumps(kw, sort_keys=True)
    EYES[key] = kw
    return key

OPEN = E()

class Script:
    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.t = 0.0
        self.pose, self.eye = "front", OPEN
        self.ev = [(0.0, "front", OPEN)]
        self.moves = [(0.0, 0, 0)]
        self.dx = 0

    def put(self, pose=None, eye=None, dt=0.0):
        self.pose = pose or self.pose
        self.eye = eye or self.eye
        self.ev.append((self.t, self.pose, self.eye))
        self.t += dt

    def wait(self, d):
        self.t += d

    def shift(self, dx, dy=0):
        self.moves.append((self.t, dx, dy))

    def blink(self, double=False):
        st = dict(EYES[self.eye])
        back = self.eye
        if st.get("kind", "open") not in ("open", "wink"):
            return
        for _ in range(2 if double else 1):
            self.put(eye=E(**{**st, "shut": 0.6}), dt=0.06)
            self.put(eye=E(**{**st, "shut": 1.0}), dt=0.09)
            self.put(eye=E(**{**st, "shut": 0.6}), dt=0.06)
            self.put(eye=back, dt=0.32 if double else 0.0)

    def hold(self, d, blinks=True):
        """Stay a while, blinking now and then as it does."""
        end = self.t + d
        while True:
            gap = self.rng.uniform(2.0, 5.2)
            if not blinks or self.t + gap + 0.25 > end:
                self.wait(max(0.0, end - self.t))
                return
            self.wait(gap)
            self.blink(double=self.rng.random() < 0.2)

    def home(self, via="front_mid"):
        if self.pose != "front":
            self.put(via, E(look=(0.0, 0)), 0.1)
        self.put("front", OPEN)

# ---------- what it does ----------

def glance(s):
    lx, ly = s.rng.choice([(-0.85, 0), (0.95, 0), (-0.6, 0.75), (0.7, 0.75), (0.75, -0.7), (-0.7, -0.6)])
    s.put(eye=E(look=(lx * 0.45, ly * 0.45)), dt=0.08)
    s.put(eye=E(look=(lx, ly)))
    s.hold(s.rng.uniform(0.9, 2.0), blinks=s.rng.random() < 0.5)
    s.put(eye=E(look=(lx * 0.45, ly * 0.45)), dt=0.08)
    s.put(eye=OPEN)

def read(s):
    s.put("front_mid", E(look=(-0.6, 0.2)), 0.1)
    s.put("left", E(look=(-0.9, 0.35)), 0.5)
    for line in range(s.rng.randint(4, 6)):
        y = 0.35 - line * 0.16
        s.put(eye=E(look=(-0.35, y)), dt=s.rng.uniform(0.35, 0.6))
        s.put(eye=E(look=(-0.95, y - 0.16)), dt=0.25)
        if line == 2:
            s.blink()
    s.put(eye=E(look=(-0.8, -0.3)), dt=0.6)
    s.home()

def look_up(s):
    s.put("up_mid", E(look=(0.1, 0.5)), 0.1)
    s.put("up", E(look=(0.1, 0.9)))
    s.hold(s.rng.uniform(1.2, 2.2))
    for lx in s.rng.sample([-0.6, 0.0, 0.7], 2):
        s.put(eye=E(look=(lx, 0.85)), dt=s.rng.uniform(0.5, 1.0))
    s.put("up_mid", E(look=(0.1, 0.4)), 0.1)
    s.home()

def fly(s):
    s.put("up_mid", E(look=(0.3, 0.6)), 0.1)
    s.put("up", E(look=(0.5, 0.9)), 0.3)
    x, y = 0.5, 0.9
    for _ in range(s.rng.randint(8, 12)):
        x = max(-0.95, min(0.95, x + s.rng.uniform(-0.6, 0.6)))
        y = max(0.2, min(1.0, y + s.rng.uniform(-0.3, 0.3)))
        s.put(eye=E(look=(x, y)), dt=s.rng.uniform(0.22, 0.42))
    s.put("up_mid", E(look=(x * 0.5, 0.3)), 0.1)
    s.put("front", E(look=(0.95, 0.1)), 0.9)
    s.put(eye=OPEN)

def hop(s, at, n=2):
    for k in range(n):
        s.moves.append((at + k * 0.36, s.dx, -2))
        s.moves.append((at + k * 0.36 + 0.16, s.dx, 0))

def happy(s):
    s.put("tilt_r_mid", E(kind="happy"), 0.1)
    s.put("tilt_r", E(kind="happy"))
    hop(s, s.t + 0.05, 2)
    s.wait(s.rng.uniform(1.6, 2.4))
    s.put("tilt_r_mid", E(kind="happy"), 0.1)
    s.home()

def hearts(s):
    s.put(eye=E(look=(0.2, 0), shut=0.6), dt=0.06)
    s.put(eye=E(kind="heart"))
    hop(s, s.t + 0.2, 1)
    s.wait(s.rng.uniform(1.6, 2.2))
    s.put(eye=E(look=(0.2, 0), shut=0.6), dt=0.06)
    s.put(eye=OPEN)

def curious(s):
    w = E(look=(0.15, 0.1), wide=1.08, tall=1.12)
    s.put("tilt_l_mid", w, 0.1)
    s.put("tilt_l", w)
    s.hold(s.rng.uniform(1.6, 2.6))
    s.put("tilt_l_mid", w, 0.1)
    s.home(via="front")

def feet(s):
    s.put("front_mid", E(look=(0.1, -0.5)), 0.1)
    s.put("down", E(look=(0.15, -0.85)))
    s.hold(s.rng.uniform(1.0, 1.6), blinks=False)
    s.put(eye=E(look=(-0.6, -0.85)), dt=0.6)
    s.put(eye=E(look=(0.7, -0.85)), dt=0.6)
    s.home()

def logo(s):
    """Its face becomes the site's mark, the cursor blinking as a prompt's does."""
    s.put(eye=E(look=(0.2, 0), shut=0.6), dt=0.06)
    s.put(eye=E(look=(0.2, 0), shut=1.0), dt=0.12)
    for k in range(s.rng.randint(7, 11)):
        s.put(eye=E(kind="logo", cursor=k % 2 == 0), dt=0.53)
    s.put(eye=E(look=(0.2, 0), shut=1.0), dt=0.12)
    s.put(eye=E(look=(0.2, 0), shut=0.6), dt=0.06)
    s.put(eye=OPEN)

def doze(s):
    for shut, d in ((0.3, 0.9), (0.55, 1.1), (0.78, 1.3)):
        s.put(eye=E(look=(0.1, -0.2), shut=shut), dt=d)
    s.put("nod", E(look=(0.1, -0.3), shut=0.9), 1.4)
    s.put("front", E(look=(0.1, 0.1), wide=1.08, tall=1.12), 0.7)
    s.blink()
    s.put(eye=OPEN)

def content(s):
    s.put(eye=E(look=(0.2, 0), shut=0.6), dt=0.06)
    s.put(eye=E(kind="content"), dt=s.rng.uniform(2.0, 3.2))
    s.put(eye=E(look=(0.2, 0), shut=0.6), dt=0.06)
    s.put(eye=OPEN)

def wink(s):
    s.put(eye=E(look=(0.3, 0.05), kind="wink"), dt=0.55)
    s.put(eye=E(look=(0.3, 0.05)), dt=0.4)
    s.put(eye=OPEN)

def scoot(s):
    """Drives a little way along on its wheels, looks about, and comes back."""
    d = s.rng.choice([-1, 1])
    n = s.rng.randint(4, 7)
    s.put(eye=E(look=(0.9 * d, -0.1)), dt=0.25)
    for _ in range(n):
        s.dx += d
        s.shift(s.dx)
        s.wait(0.14)
    s.hold(0.5, blinks=False)
    s.put(eye=E(look=(-0.8 * d, 0)), dt=0.9)
    s.blink()
    s.put(eye=E(look=(-0.9 * d, -0.1)), dt=0.25)
    for _ in range(n):
        s.dx -= d
        s.shift(s.dx)
        s.wait(0.14)
    s.put(eye=OPEN)

def think(s):
    s.put(eye=E(look=(0.35, 0.35)), dt=0.08)
    s.put(eye=E(look=(0.75, 0.75)))
    s.hold(s.rng.uniform(1.4, 2.2), blinks=False)
    s.put(eye=E(look=(0.4, 0.3)), dt=0.25)
    happy(s)

def scan(s):
    for lx in (-0.85, -0.45, 0.0, 0.45, 0.85, 0.45, 0.0):
        s.put(eye=E(kind="squint", look=(lx, 0)), dt=0.18)
    s.put(eye=OPEN)

LOG = []
DECK = {glance: 3, read: 1.6, look_up: 1.2, fly: 1.0, happy: 1.3, hearts: 0.7, curious: 1.1, feet: 0.9, logo: 1.6,
        doze: 0.5, content: 0.9, wink: 0.6, scoot: 0.9, think: 0.8, scan: 0.9}

def script(seed=11, length=240.0):
    s = Script(seed)
    # its first seconds are what most visitors see: it notices them, is pleased, and shows where it lives
    s.hold(1.6, blinks=False)
    s.blink()
    s.wait(0.8)
    s.put(eye=E(look=(0.3, 0.05), wide=1.08, tall=1.12), dt=0.9)
    happy(s)
    s.hold(2.2)
    logo(s)
    used = set()
    last = None
    while s.t < length - 14:
        s.hold(s.rng.uniform(2.0, 6.0))
        pool = [b for b in DECK if b is not last]
        unused = [b for b in pool if b not in used]
        if unused and s.rng.random() < 0.6:
            pick = s.rng.choice(unused)
        else:
            pick = s.rng.choices(pool, weights=[DECK[b] for b in pool])[0]
        LOG.append((round(s.t, 1), pick.__name__))
        pick(s)
        used.add(pick)
        last = pick
    s.hold(max(2.0, length - s.t))
    return s

# ---------- drawing ----------

def layer(img):
    out = {}
    h, w = img.shape
    for y in range(h):
        x = 0
        while x < w:
            c = img[y, x]
            if not c:
                x += 1
                continue
            n = 1
            while x + n < w and img[y, x + n] == c:
                n += 1
            out.setdefault(c, []).append((x, y, n))
            x += n
    return out

def rects(rs):
    """Runs stacked straight above each other become one rectangle."""
    left = {(x, y, n) for x, y, n in rs}
    out = []
    for x, y, n in sorted(rs, key=lambda r: (r[1], r[0])):
        if (x, y, n) not in left:
            continue
        h = 1
        while (x, y + h, n) in left:
            left.discard((x, y + h, n))
            h += 1
        left.discard((x, y, n))
        out.append((x, y, n, h))
    return out

def paths(img, dx, dy):
    return "".join('<path fill="%s" d="%s"/>' % (c, "".join("M%d %dh%dv%dh-%dz" % (x - dx, y - dy, n, h, n) for x, y, n, h in rects(rs)))
                   for c, rs in sorted(layer(img).items()))

def merge(sp):
    sp = sorted(sp)
    m = [list(sp[0])]
    for a, b in sp[1:]:
        if abs(a - m[-1][1]) < 1e-9:
            m[-1][1] = b
        else:
            m.append([a, b])
    return m

def keyframes(name, spans, cycle, rest):
    pts = {0.0: 1 if rest else 0}
    for a, b in spans:
        pts[round(a, 3)] = 1
        pts[round(b, 3)] = 0
    ks = sorted(pts.items())
    body = "".join("%s%%{opacity:%d}" % (fmt(100 * t / cycle), v) for t, v in ks if t < cycle)
    return "@keyframes %s{%s100%%{opacity:%d}}" % (name, body, 1 if rest else 0)

def fmt(v):
    return ("%.3f" % v).rstrip("0").rstrip(".")

def main(out_svg, out_png=None):
    s = script()
    cycle = round(s.t, 2)
    R = render(pose("front"), {"kind": "none"}, only="body")
    body = outline(R, colorize(R))
    led = np.where(R["led"], body, "")
    body = np.where(R["led"], "", body)
    heads, eyes = {}, {}
    used = sorted(set((p, e) for _, p, e in s.ev))
    for p in sorted(set(p for p, _ in used)):
        R = render(pose(p), {"kind": "none"}, only="head")
        img = outline(R, colorize(R))
        light = (R["mat"] == GREEN)
        heads[p] = (np.where(light, "", img), np.where(light, img, ""))
    for p, e in used:
        R = render(pose(p), EYES[e], only="head")
        img = outline(R, colorize(R))
        base = np.where(heads[p][0] != "", heads[p][0], heads[p][1])
        eyes[(p, e)] = np.where(img != base, img, "")
    allm = body != ""
    for a, b in heads.values():
        allm |= (a != "") | (b != "")
    ys, xs = np.nonzero(allm)
    x0, x1, y0, y1 = xs.min() - 9, xs.max() + 10, ys.min() - 4, ys.max() + 4
    vw, vh = x1 - x0, y1 - y0
    ends = [t for t, _, _ in s.ev[1:]] + [cycle]
    head_spans, eye_spans = {}, {}
    for (t, p, e), t2 in zip(s.ev, ends):
        if t2 > t:
            head_spans.setdefault(p, []).append((t, t2))
            eye_spans.setdefault((p, e), []).append((t, t2))
    css = ["svg{shape-rendering:crispEdges}", ".k{animation:%gs steps(1,end) infinite;opacity:0}.k.r{opacity:1}" % cycle]
    inner = []
    sh = []
    cx, cy = (xs.min() + xs.max()) / 2 - x0, ys.max() - y0
    for yy in range(-2, 3):
        half = int(round(math.sqrt(max(0, 1 - (yy / 2.6) ** 2)) * 27))
        sh.append("M%d %dh%dv1h-%dz" % (int(cx - half), int(cy + yy), 2 * half, 2 * half))
    inner.append('<path fill="#000" fill-opacity=".28" d="%s"/>' % "".join(sh))
    inner.append(paths(body, x0, y0))
    inner.append('<g class="led">%s</g>' % paths(led, x0, y0))
    for i, p in enumerate(sorted(heads)):
        if p not in head_spans:
            continue
        name = "h%d" % i
        rest = p == "front"
        css.append(keyframes(name, merge(head_spans[p]), cycle, rest) + ".%s{animation-name:%s}" % (name, name))
        inner.append('<g class="k %s%s">%s<g class="ant">%s</g></g>' % (name, " r" if rest else "", paths(heads[p][0], x0, y0), paths(heads[p][1], x0, y0)))
    for i, key in enumerate(sorted(eyes)):
        if key not in eye_spans:
            continue
        name = "e%d" % i
        rest = key == ("front", OPEN)
        css.append(keyframes(name, merge(eye_spans[key]), cycle, rest) + ".%s{animation-name:%s}" % (name, name))
        inner.append('<g class="k %s%s">%s</g>' % (name, " r" if rest else "", paths(eyes[key], x0, y0)))
    mv = sorted(s.moves)
    kf = "".join("%s%%{transform:translate(%dpx,%dpx)}" % (fmt(100 * t / cycle), dx, dy) for t, dx, dy in mv if t < cycle)
    css.append("@keyframes go{%s100%%{transform:translate(0,0)}}.bot{animation:go %gs steps(1,end) infinite}" % (kf, cycle))
    # its antenna's light breathes and its belly's light blinks, each on a clock of its own
    css.append("@keyframes ant{0%,100%{opacity:1}50%{opacity:.55}}.ant{animation:ant 3.1s ease-in-out infinite}")
    css.append("@keyframes led{0%{opacity:1}88%{opacity:.25}94%{opacity:1}}.led{animation:led 5.3s steps(1,end) infinite}")
    css.append("@media (prefers-reduced-motion:reduce){.k,.bot,.ant,.led{animation:none}}")
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" '
           'aria-label="A small white robot with a black glass face and green eyes"><style>%s</style><g class="bot">%s</g></svg>'
           % (vw, vh, vw * 3, vh * 3, "".join(css), "".join(inner)))
    open(out_svg, "w").write(svg)
    kinds = {}
    for t, p, e in s.ev:
        kinds[EYES[e].get("kind", "open")] = kinds.get(EYES[e].get("kind", "open"), 0) + 1
    print(" ".join("%s:%s" % (t, n) for t, n in LOG))
    print("svg bytes", len(svg), "box", vw, vh, "cycle", cycle, "events", len(s.ev), "heads", len(heads), "eyes", len(eyes))
    shots = []
    for key in [("front", OPEN), ("left", None), ("up", None), ("tilt_r", None), ("tilt_l", None), ("down", None),
                ("front", E(kind="logo", cursor=True)), ("front", E(kind="logo", cursor=False)), ("front", E(kind="heart")),
                ("front", E(kind="content")), ("front", E(look=(0.3, 0.05), kind="wink")), ("front", E(kind="squint", look=(0.0, 0)))]:
        p, e = key
        if e is None:
            e = next(ee for pp, ee in eyes if pp == p)
        im = body.copy()
        im = np.where(heads[p][0] != "", heads[p][0], im)
        im = np.where(heads[p][1] != "", heads[p][1], im)
        if (p, e) in eyes:
            im = np.where(eyes[(p, e)] != "", eyes[(p, e)], im)
        im = np.where(led != "", led, im)
        shots.append(im[y0:y1, x0 + 6:x1 - 6])
    if out_png:
        sheet(shots, out_png, scale=3)

if __name__ == "__main__":
    main(*sys.argv[1:3])
