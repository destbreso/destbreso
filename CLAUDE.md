# destbreso

The GitHub profile repository: its README is the profile at github.com/destbreso, and the same repository is a GitHub Pages site (destbreso.github.io/destbreso), an analyst's report of how the author works, every figure generated daily from commit data.

Read first: `README.md` (the profile), `.github/scripts/README.md` (the data pipeline: tokens, what private work is counted, the timezone), then `index.html` and `assets/` (the report).

## Identity and look

- The profile's angle is the mathematician who builds: algorithms, craft, first principles. The current role is a small fact chip, never the framing. Same person as destbreso.com, another facet of him.
- Blueprint dark (`#0b0e14` with a grid), one restrained accent, plotter cyan `#4dd4e0`, and the system monospace; deliberately not destbreso.com's terminal green. Where a figure splits public from private work, private is purple (`--c3`).
- No third-party widgets in the README (stats cards, trophies, streaks, typing banners, the snake, visitor counters, rows of badges): everything shown is generated here from real data. The figures carry no text of their own.
- `01 · Building` links only to public repositories: a private one is a 404 for every visitor.

## The figures

- `year.svg` (`generate-year.py`) is the README's figure: one column a week for the last 52 weeks, public under private, this week's column still being written, walked by a small pixel robot drawn as a blueprint. A README runs no JavaScript, so it moves by CSS keyframes inside the SVG, every animation on one clock (the cycle) or a whole fraction of it, step timing on whole pixels; one SVG, never split, or two parts could not share that clock. It replaced the Fourier signal and the contour map (2026-11-05), which no visitor could read.
- The robot's pixels live once, in `assets/robot.json`, read by the generator and by the page (`assets/year.js`), where the same figure is interactive: a week is read under the pointer, a click sends the robot there, the arrow keys move it, and what moves by itself holds still a few seconds after the visitor stops, and always with reduced motion. The robot has no name and is not given one: not in the figures, captions, alt text, docs or commits of this public repository.
- The heatmap is a whole year folded into a typical week (day by hour), and says so.
- The public and private split is stacked where the form allows it (the year, the blocks, momentum, the projects); the heatmap stays a combined total. The public/private key shows only when there is private data.

## The data

- The per-repository commit aggregation (`/user/repos?affiliation=owner`, then each repository's commits by the author) is the single source of truth: GitHub's contribution calendar leaves private contributions out even with the PAT. `generate-data.py` writes `dist/series.json` (the 52 weeks from a Monday to today, weekly totals and their public share, the daily counts) and the year figure is drawn from it, which is why `profile.yml` runs the data step first. Every number on the page that has an aggregation behind it (the streak, the momentum, the trend) comes from it; the calendar is only the fallback when the aggregation finds nothing.
- A repository's commits are read up to 5,000 a year (a cap of 500 once cut the busiest repository's older months out), and the window ends today (one that ended a week back once dropped the newest days).
- The Action starts from the last published snapshot, keeping only the files still generated, so a generator that fails one day leaves the day before's file deployed instead of a broken image (the deploy replaces the whole `output` branch). When `data.json` cannot be loaded the page says so and shows nothing: it never fills in made-up numbers.
- Languages are bytes of code, markup and styles left out (a few repositories of generated HTML pages once made the stack read 81% HTML).
- Private repository names are never emitted (they are summed into one "private work" bar), and private repositories of other organizations are not read at all.
- The KPIs rebuilt from the aggregation carry no year-over-year delta (`None`): there is no prior-year pass to compare with honestly, and the page hides a missing delta. Do not compute one from the calendar.

## Outside this repository

destbreso.com links to the report in context (the projects page, the skills page, the footer and its `llms.txt`), not from its navigation. Keep the report's address stable.
