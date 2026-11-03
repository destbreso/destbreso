# destbreso

The GitHub profile repository: its README is the profile at github.com/destbreso, and the same repository is a GitHub Pages site (destbreso.github.io/destbreso), an analyst's report of how the author works, every figure generated daily from commit data.

Read first: `README.md` (the profile), `.github/scripts/README.md` (the data pipeline: tokens, what private work is counted, the timezone), then `index.html` and `assets/` (the report).

## Identity and look

- The profile's angle is the mathematician who builds: algorithms, craft, first principles. The current role is a small fact chip, never the framing. Same person as destbreso.com, another facet of him.
- Blueprint dark (`#0b0e14` with a grid), one restrained accent, plotter cyan `#4dd4e0`, and the system monospace; deliberately not destbreso.com's terminal green. Where a figure splits public from private work, private is purple (`--c3`).
- No third-party widgets in the README (stats cards, trophies, streaks, typing banners, the snake, visitor counters, rows of badges): everything shown is generated here from real data. The figures carry no text of their own.
- `01 · Building` links only to public repositories: a private one is a 404 for every visitor.

## The figures

- `signal.svg` is one image on purpose: the Fourier waveform and the same year folded onto a Hilbert curve pulse in sync. A README runs no JavaScript, so two images can never share a clock; `generate-signal.py` draws both in one SVG with every animation on the same duration from `begin="0s"`. Never split it in two.
- The heatmap is a whole year folded into a typical week (day by hour), and says so.
- The public and private split is stacked where the form allows it (the blocks, momentum, the projects); the heatmap, the signal and the contours stay combined totals. The public/private key shows only when there is private data.

## The data

- The per-repository commit aggregation (`/user/repos?affiliation=owner`, then each repository's commits by the author) is the single source of truth: GitHub's contribution calendar leaves private contributions out even with the PAT. `generate-data.py` writes `dist/series.json` and the signal and contour generators read it, which is why `profile.yml` runs the data step first. The calendar is only the fallback when the aggregation finds nothing.
- Private repository names are never emitted (they are summed into one "private work" bar), and private repositories of other organizations are not read at all.
- The KPIs rebuilt from the aggregation carry no year-over-year delta (`None`): there is no prior-year pass to compare with honestly, and the page hides a missing delta. Do not compute one from the calendar.

## Outside this repository

destbreso.com links to the report in context (the projects page, the skills page, the footer and its `llms.txt`), not from its navigation. Keep the report's address stable.
