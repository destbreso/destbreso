#!/usr/bin/env bash
# The README's hero GIFs, dark and light, from circuit.json: an SVG a theme (hero.py), its frames rendered by Chromium
# (frames.mjs), joined by ffmpeg with one palette for all of them, so no colour shifts between frames. 7 centiseconds a
# frame, the same for each, so the loop keeps an even pace across its seam.
#   PLAYWRIGHT=/path/to/playwright-core/index.js CHROME=/path/to/chrome tools/hero/build.sh
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
root="$here/../.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
n="$(python3 -c "import json,sys; print(len(json.load(open(sys.argv[1]))['frames']))" "$here/circuit.json")"
for theme in dark light; do
  python3 "$here/hero.py" "$here/circuit.json" "$tmp/$theme.svg" "$theme"
  node "$here/frames.mjs" "$tmp/$theme.svg" "$tmp/$theme" "$n"
  ffmpeg -loglevel error -y -framerate 100/7 -i "$tmp/$theme/f%03d.png" -vf "palettegen=max_colors=96:stats_mode=full:reserve_transparent=0" "$tmp/$theme-palette.png"
  ffmpeg -loglevel error -y -framerate 100/7 -i "$tmp/$theme/f%03d.png" -i "$tmp/$theme-palette.png" -lavfi "paletteuse=dither=none:diff_mode=rectangle" -loop 0 "$root/assets/hero-$theme.gif"
done
ls -la "$root/assets/hero-dark.gif" "$root/assets/hero-light.gif"
