# Made by hand

Two of the README's pictures do not depend on the day's data, so the daily Action does not make them: they are rebuilt here when they change, and the results are committed in `assets/`.

## The hero (`hero/`)

`assets/hero-dark.gif` and `assets/hero-light.gif`: the name beside one period of a Game of Life circuit (a Gosper gun, a reflector, an eater) that destbreso.com's own engine compiles and runs.

1. `frames.ts` writes `circuit.json`, every generation's live cells over one period, checking that the streams run into nothing and that the period closes. It imports the site's engine, so it runs from a checkout of the site's repository: `npx tsx <this repository>/tools/hero/frames.ts <this repository>/tools/hero/circuit.json`, there. The circuit is the `SOURCE` at its top, in the site's Glider ISA; another circuit needs its period in `PERIOD`.
2. `build.sh` draws an SVG a theme from `circuit.json` (`hero.py`), renders its frames with Chromium at twice its size (`frames.mjs`) and joins them with ffmpeg on one palette, at 7 centiseconds a frame: `PLAYWRIGHT=/path/to/playwright-core/index.js CHROME=/path/to/chrome tools/hero/build.sh`. It needs Python 3, Node, playwright-core, a Chromium and ffmpeg.

## The robot (`robot/`)

`assets/robot.svg`: destbreso.com's robot in pixels, alive. `render.py` ray-marches its 3D model's parts (sizes and materials taken from the site's own 3D model of it) and shades them into a few tones each; `compose.py` draws its body once, a head for each way it turns and its eyes over the head, and writes a four-minute script of what it does as CSS steps. It needs Python 3 and numpy: `python3 tools/robot/compose.py assets/robot.svg [states.png]`, the optional sheet showing its states for checking. The script is seeded, so the same code writes the same file.
