#!/usr/bin/env python3
"""
The README's hero as an animated SVG, one per theme: the name on the left and, on the right, one period of the Game of
Life circuit in circuit.json (frames.ts), a frame a generation. Cells alive through the whole period (the still lifes,
the gun's blocks) are drawn as the blueprint's lines; what moves is the plotter's cyan, with a faint trail of the two
generations before. build.sh renders these frames to the GIFs the README shows: a GIF plays in every GitHub client, and
since the period closes, its last frame leads into its first and the loop has no seam.
  python3 tools/hero/hero.py tools/hero/circuit.json out-dark.svg dark
"""
import json
import sys

W, H = 1200, 300
CELL = 4
FPS = 15
THEMES = {
    "dark": dict(bg0="#0b0e14", bg1="#0c1119", grid="#141b26", frame="#1b2330", still="#2c4a60", live="#4dd4e0",
                 name="#e8ecf1", sub="#9198a1", note="#5c6675", accent="#4dd4e0"),
    "light": dict(bg0="#f7f9fb", bg1="#eef3f7", grid="#e3e9ef", frame="#d5dde5", still="#9db4c6", live="#0f8a99",
                  name="#1f2328", sub="#59636e", note="#8c959f", accent="#0f8a99"),
}


def build(data, theme):
    C = THEMES[theme]
    x0, y0, x1, y1 = data["box"]
    frames = [set((x, y) for x, y in f) for f in data["frames"]]
    n = len(frames)
    static = set.intersection(*frames)
    cw, ch = x1 - x0 + 1, y1 - y0 + 1
    ox, oy = W - 40 - cw * CELL, (H - ch * CELL) // 2

    def cells(cs):
        return "".join("M%d %dh%dv%dh-%dz" % (ox + (x - x0) * CELL, oy + (y - y0) * CELL, CELL - 1, CELL - 1, CELL - 1) for x, y in sorted(cs))

    dur = n / FPS
    css = "@keyframes f{0%%{opacity:1}%.4f%%{opacity:0}100%%{opacity:0}}.g{opacity:0;animation:f %.3fs steps(1,end) infinite}" % (100 / n, dur)
    css += "@media (prefers-reduced-motion:reduce){.g{animation:none}.g:first-of-type{opacity:1}}"
    groups = []
    for i, f in enumerate(frames):
        trail = (frames[i - 1] | frames[i - 2]) - f - static
        groups.append('<g class="g" style="animation-delay:%.3fs"><path fill="%s" fill-opacity=".22" d="%s"/><path fill="%s" d="%s"/></g>'
                      % (i / FPS - dur, C["live"], cells(trail), C["live"], cells(f - static)))
    sans = "-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif"
    mono = "ui-monospace,SFMono-Regular,Menlo,monospace"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs><pattern id="grid" width="{CELL * 8}" height="{CELL * 8}" patternUnits="userSpaceOnUse"><path d="M{CELL * 8} 0H0V{CELL * 8}" fill="none" stroke="{C['grid']}" stroke-width="1"/></pattern>
<linearGradient id="fade" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{C['bg0']}"/><stop offset="1" stop-color="{C['bg1']}"/></linearGradient></defs>
<style>{css}</style>
<rect width="{W}" height="{H}" fill="url(#fade)"/><rect width="{W}" height="{H}" fill="url(#grid)" opacity=".6"/>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" fill="none" stroke="{C['frame']}"/>
<path fill="{C['still']}" d="{cells(static)}"/>
{"".join(groups)}
<text x="64" y="96" fill="{C['accent']}" font-family="{mono}" font-size="14" letter-spacing="3">// mathematician who builds</text>
<text x="62" y="166" fill="{C['name']}" font-family="{sans}" font-size="58" font-weight="700" letter-spacing="-1.2">David Est&#233;vez</text>
<rect x="66" y="184" width="52" height="3" fill="{C['accent']}"/>
<text x="64" y="220" fill="{C['sub']}" font-family="{sans}" font-size="21">Algorithms, craft, and systems worth building.</text>
<text x="64" y="258" fill="{C['note']}" font-family="{mono}" font-size="13.5">first principles, from proof to production</text>
</svg>'''


if __name__ == "__main__":
    data = json.load(open(sys.argv[1]))
    open(sys.argv[2], "w").write(build(data, sys.argv[3] if len(sys.argv) > 3 else "dark"))
