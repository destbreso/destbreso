# Profile data pipeline

The daily GitHub Action (`.github/workflows/profile.yml`) generates the graphics and the
data snapshot for the profile README and the Pages site (`destbreso.github.io/destbreso`),
then pushes them to the **`output`** branch. The README and the site read from `output`
(via `raw.githubusercontent.com`), so nothing is fetched live from the GitHub API at page
load and nothing can rate-limit.

## What runs

| Script | Output (on `output`) | What it is |
| --- | --- | --- |
| `generate-signal.py` | `signal.svg` | The year as one signal: a Fourier reconstruction of the weekly commit counts (top) and the same year folded onto a Hilbert curve (bottom). Both pulses share a single SMIL timeline, so they stay in sync even inside a README (which runs no JavaScript). |
| `generate-contours.py` | `contours.svg` | The year as a landscape: the daily calendar as a height field, its level sets traced by marching squares. |
| `generate-data.py` | `data.json` | Every number on the analyst page: KPIs, the day x hour rhythm heatmap, blocks, languages, effort by project, this week vs the year baseline, momentum, and the composed insights. |

`generate-heatmap.py` is an unused experiment and is not wired into the workflow.

The site (`assets/script.js`) fetches `data.json` with `cache: no-store` and renders it,
falling back to an embedded, clearly labeled sample if the snapshot is missing.

## Environment

| Var | Default | Purpose |
| --- | --- | --- |
| `GITHUB_TOKEN` | (Action) | The repo's built-in token. Sees PUBLIC data only. |
| `PAT_TOKEN` | empty | Optional Personal Access Token. When set, PRIVATE work is included. See below. |
| `UTC_OFFSET` | `-4` | Author local time for the hour heatmap (Miami). Commit dates come back in UTC; this shifts them. |
| `GH_USER` | `destbreso` | The account to read. |

## Including private repositories (`PAT_TOKEN`)

By default the pipeline runs on the Action's `GITHUB_TOKEN`, which can only read the current
repository and public data. So without a token, everything reflects your **public** work
only: the day x hour heatmap is real but thin, the effort chart has no `private work` bar,
and the KPIs and momentum count public contributions only. (For reference, on 2026-07-07 the
public year was about 146 commits, which is why the heatmap looked sparse.)

To include your own private repositories, add a Personal Access Token as a secret:

1. **Create the token.** GitHub -> your avatar -> Settings -> Developer settings ->
   Personal access tokens.
   - Fine-grained (recommended): Resource owner = your account, Repository access =
     All repositories, Permissions = Contents: Read-only and Metadata: Read-only.
   - Or classic: the `repo` scope.
2. **Add it as a repository secret.** This repo -> Settings -> Secrets and variables ->
   Actions -> New repository secret. Name it exactly `PAT_TOKEN` and paste the token.
3. **Re-run the workflow.** Actions -> Generate Profile -> Run workflow (or wait for the
   daily cron).

With the secret set, every generator prefers the PAT, so `data.json` gets
`rhythmScope: "all repos"`, the heatmap fills across all your commits, a `private work` bar
appears in the effort chart, and the KPIs, momentum, signal, and contours all reflect your
full public plus private year.

Until the secret exists, GitHub's linter warns `Context access might be invalid: PAT_TOKEN`
on the workflow. That is expected and harmless: an unset secret resolves to an empty string,
and the code falls back to the public `GITHUB_TOKEN`.

### Scope and privacy

- **Covered:** repositories you **own** (personal, public and private), via `affiliation=owner`.
  This is the common case: your own private repos are counted in full, including commit hours.
- **Not covered by the per-repo detail:** private repos in **external organizations** (for
  example an employer). Reading those requires the organization to authorize the token (org
  PAT policy, possibly SSO), and surfacing an employer's cadence is a confidentiality matter,
  so the per-repo heatmap and project chart deliberately do not pull them in.
- **Private repository names are never emitted.** In the effort chart all private repos are
  summed into a single `private work` bar. `data.json` contains only aggregate numbers and
  public repo names.
- The PAT lives only as an encrypted Actions secret. It is never written to `data.json` or
  the `output` branch.

## Timezone

The commits REST API returns `author.date` normalized to UTC. `UTC_OFFSET` (default `-4`,
Miami) shifts each commit to local wall-clock time so the hour heatmap reads correctly.
Daylight saving is not tracked (winter is off by one hour, negligible for the multi-hour
blocks).

## Running it

The workflow runs daily (cron) and on every push to `main`. To run it by hand, use the
`workflow_dispatch` trigger: Actions -> Generate Profile -> Run workflow.
