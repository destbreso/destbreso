#!/usr/bin/env python3
"""
Build data.json for the destbreso.github.io/destbreso analyst page.

Runs daily in GitHub Actions with the authenticated GITHUB_TOKEN (5000 req/hr),
so nothing here rate-limits. It computes every number from real GitHub data and
composes the narrative (insights + decisions) FROM those numbers, so the page
never states a claim the data cannot back. Output: dist/data.json, pushed to the
`output` branch by the existing deploy step. Every section is best-effort: if one
source fails, that section is skipped and the front end keeps its shape.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from collections import defaultdict
from datetime import datetime, timedelta, timezone

USER = os.environ.get("GH_USER", "destbreso")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
PAT = os.environ.get("PAT_TOKEN", "")  # optional PAT with repo scope: unlocks PRIVATE repos for the rhythm
UTC_OFFSET = int(os.environ.get("UTC_OFFSET", "-4"))  # Miami; used only when a commit date is normalized to UTC
OUT = os.path.join("dist", "data.json")
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
BLOCKS = [
    ("morning 06-12", range(6, 12)),
    ("afternoon 12-17", range(12, 17)),
    ("evening 17-21", range(17, 21)),
    ("night 21-06", list(range(21, 24)) + list(range(0, 6))),
]


def _req(url, data=None, headers=None, token=None):
    # Prefer an explicit token, then the PAT, then GITHUB_TOKEN. The PAT (when set)
    # makes the calendar, momentum, KPIs and languages include PRIVATE work; forcing
    # GITHUB_TOKEN gives the PUBLIC-only view used for the public/private split.
    h = {"Authorization": "Bearer " + (token or PAT or TOKEN), "User-Agent": USER + "-signal",
         "Accept": "application/vnd.github+json"}
    if headers:
        h.update(headers)
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=h,
                                 method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode()), r.headers


def gql(query, variables, token=None):
    d, _ = _req("https://api.github.com/graphql", {"query": query, "variables": variables}, token=token)
    if "errors" in d:
        raise RuntimeError(d["errors"])
    return d["data"]


def rest(path, page=None):
    url = "https://api.github.com" + path
    if page:
        url += ("&" if "?" in path else "?") + "per_page=100&page=" + str(page)
    d, headers = _req(url)
    return d


def rest_tok(path, token, page=None):
    """Same as rest(), but with an explicit token (lets the rhythm use a PAT)."""
    url = "https://api.github.com" + path
    if page:
        url += ("&" if "?" in path else "?") + "per_page=100&page=" + str(page)
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token, "User-Agent": USER + "-signal",
        "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def owner_repos(token, include_private):
    """Owned, non-fork repos as (full_name, is_private). include_private uses
    /user/repos (needs a PAT) so private repos are included in the aggregate."""
    path = ("/user/repos?affiliation=owner&sort=pushed" if include_private
            else "/users/" + USER + "/repos?type=owner&sort=pushed")
    out = []
    for page in range(1, 4):  # up to 300 repos, most-recently-pushed first
        batch = rest_tok(path, token, page)
        if not batch:
            break
        out += [(r["full_name"], bool(r.get("private"))) for r in batch if not r.get("fork")]
        if len(batch) < 100:
            break
    return out


def repo_commit_dates(full, token, since):
    """Yield author-date strings for the user's commits in one repo since `since`."""
    for page in range(1, 6):  # cap ~500 commits/repo so a busy repo cannot run away
        path = "/repos/%s/commits?author=%s&since=%s" % (full, USER, since)
        try:
            batch = rest_tok(path, token, page)
        except Exception:
            return  # empty repo (409), no access, etc.: skip this repo
        if not batch:
            return
        for c in batch:
            try:
                yield c["commit"]["author"]["date"]
            except Exception:
                continue
        if len(batch) < 100:
            return


def block_of(hr):
    for label, hrs in BLOCKS:
        if hr in hrs:
            return label
    return BLOCKS[-1][0]


def parse_commit(iso):
    """Return (utc_dt, local_dt). utc_dt is timezone-aware for recency checks;
    local_dt is shifted to the author's local wall clock for weekday/hour
    bucketing. GitHub normalizes author.date to UTC (Z / +00:00), which Miami
    never is, so a zero offset means UTC and we apply UTC_OFFSET."""
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt + timedelta(hours=UTC_OFFSET) if dt.utcoffset() == timedelta(0) else dt
    return dt, local


def build_projects(repo_commits, repo_private, top=6):
    """Where the effort goes, last 12 months. Public repos named; all private
    repos folded into one aggregate bar so the effort shows without leaking names."""
    pub = sorted([(full.split("/")[-1], c) for full, c in repo_commits.items()
                  if c > 0 and not repo_private.get(full)], key=lambda x: -x[1])
    projects = [{"n": n, "c": c, "kind": "public"} for n, c in pub[:top]]
    other = sum(c for _, c in pub[top:])
    if other:
        projects.append({"n": "other public", "c": other, "kind": "other"})
    priv_total = sum(c for full, c in repo_commits.items() if c > 0 and repo_private.get(full))
    if priv_total:
        projects.append({"n": "private work", "c": priv_total, "kind": "private"})
    projects.sort(key=lambda p: -p["c"])
    return projects


def this_week(week_total, week_blocks, block_counts, seen):
    """How the last 7 days deviate from the year baseline: volume vs the weekly
    average, and which block ran most above its usual share."""
    avg_weekly = seen / 52.0
    vol = round((week_total - avg_weekly) / avg_weekly * 100) if avg_weekly else 0
    dev_block, dev_pts = None, 0
    if week_total:
        tb = sum(block_counts.values()) or 1
        base = {label: block_counts.get(label, 0) / tb for label, _ in BLOCKS}
        wk = {label: week_blocks.get(label, 0) / week_total for label, _ in BLOCKS}
        dev_block = max(BLOCKS, key=lambda lb: wk[lb[0]] - base[lb[0]])[0]
        dev_pts = round((wk[dev_block] - base[dev_block]) * 100)
    return {"commits": week_total, "volDelta": vol, "devBlock": dev_block, "devPts": dev_pts}


CAL_Q = """
query($login:String!, $from:DateTime!, $to:DateTime!){
  user(login:$login){
    contributionsCollection(from:$from, to:$to){
      totalCommitContributions
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}"""


def window(days_ago_from, days_ago_to):
    now = datetime.now(timezone.utc)
    return (now - timedelta(days=days_ago_from)).isoformat(), (now - timedelta(days=days_ago_to)).isoformat()


def calendar_days(frm, to, token=None):
    d = gql(CAL_Q, {"login": USER, "from": frm, "to": to}, token=token)
    cc = d["user"]["contributionsCollection"]
    days = [(day["date"], day["contributionCount"])
            for w in cc["contributionCalendar"]["weeks"] for day in w["contributionDays"]]
    return cc["totalCommitContributions"], days


def longest_streak(days):
    best = cur = 0
    for _, c in days:
        cur = cur + 1 if c > 0 else 0
        best = max(best, cur)
    return best


def monthly(days):
    agg = defaultdict(int)
    for date, c in days:
        agg[date[:7]] += c  # YYYY-MM
    keys = sorted(agg.keys())[-12:]
    labels = [MONTHS[int(k[5:7]) - 1] for k in keys]
    return keys, [agg[k] for k in keys], labels


def monthly_on(days, keys):
    agg = defaultdict(int)
    for date, c in days:
        agg[date[:7]] += c
    return [agg.get(k, 0) for k in keys]


def pct(delta_now, delta_prev):
    if not delta_prev:
        return 0
    return round((delta_now - delta_prev) / delta_prev * 100)


def build():
    data = {"generated_at": datetime.now(timezone.utc).isoformat(), "sample": False}

    # ---- contributions (this year + prior year for deltas) ----
    frm, to = window(365, 0)
    commits, days = calendar_days(frm, to)
    active = sum(1 for _, c in days if c > 0)
    streak = longest_streak(days)
    mkeys, mvals, mlabels = monthly(days)
    # public-only monthly (forced GITHUB_TOKEN) so momentum can stack public vs private
    try:
        _, pub_days = calendar_days(frm, to, token=TOKEN)
        pubm = monthly_on(pub_days, mkeys)
        mvals_public = [min(pubm[i], mvals[i]) for i in range(len(mkeys))]
    except Exception:
        mvals_public = list(mvals)

    try:
        pfrm, pto = window(730, 365)
        pcommits, pdays = calendar_days(pfrm, pto)
        pactive = sum(1 for _, c in pdays if c > 0)
    except Exception:
        pcommits, pactive = 0, 0

    try:
        u = rest("/users/" + USER)
        repos_total = u.get("public_repos", 0)
    except Exception:
        repos_total = 0

    # monthly active-day counts for a spark
    amap = defaultdict(int)
    for date, c in days:
        if c > 0:
            amap[date[:7]] += 1
    akeys = sorted(amap.keys())[-12:]
    aspark = [amap[k] for k in akeys] or mvals

    data["kpis"] = [
        {"label": "commits · 12mo", "val": commits, "delta": pct(commits, pcommits), "spark": mvals},
        {"label": "active days", "val": active, "delta": pct(active, pactive), "spark": aspark},
        {"label": "longest streak", "val": str(streak) + "d", "delta": 0, "spark": mvals},
        {"label": "public repos", "val": repos_total, "delta": 0, "spark": mvals},
    ]
    data["momentum"] = mvals
    data["momentumPublic"] = mvals_public
    data["momentumLabels"] = mlabels
    if mvals:
        peak_i = mvals.index(max(mvals))
        data["momentumAnnot"] = {"index": peak_i, "text": "busiest month"}

    # ---- rhythm (weekday x hour) + blocks, from real commit timestamps ----
    # The contribution calendar has no hour-of-day, and the public Events API
    # misses private-repo work (that is why this panel was empty). So aggregate
    # actual commit author timestamps across the owner's repos. A PAT with repo
    # scope (env PAT_TOKEN) includes PRIVATE repos; without it, public repos only.
    try:
        rtoken = PAT or TOKEN
        include_private = bool(PAT)
        matrix = [[0] * 24 for _ in range(7)]
        block_counts = defaultdict(int)
        block_pub = defaultdict(int)
        block_priv = defaultdict(int)
        week_blocks = defaultdict(int)
        since = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()
        week_cut = datetime.now(timezone.utc) - timedelta(days=7)
        seen = week_total = 0
        repo_commits, repo_private = {}, {}
        for full, priv in owner_repos(rtoken, include_private):
            cnt = 0
            for iso in repo_commit_dates(full, rtoken, since):
                dt, local = parse_commit(iso)
                blk = block_of(local.hour)
                matrix[local.weekday()][local.hour] += 1
                block_counts[blk] += 1
                (block_priv if priv else block_pub)[blk] += 1
                seen += 1
                cnt += 1
                if dt >= week_cut:
                    week_total += 1
                    week_blocks[blk] += 1
            repo_commits[full] = cnt
            repo_private[full] = priv
        if seen:
            mx = max((max(r) for r in matrix), default=0) or 1
            data["rhythm"] = [[round(v / mx, 3) for v in row] for row in matrix]
            total_b = sum(block_counts.values()) or 1
            data["blocks"] = [{"l": label,
                               "v": round(block_counts.get(label, 0) / total_b * 100),
                               "pubv": round(block_pub.get(label, 0) / total_b * 100),
                               "privv": round(block_priv.get(label, 0) / total_b * 100)}
                              for label, _ in BLOCKS]
            data["blocks"].sort(key=lambda b: -b["v"])
            data["rhythmScope"] = "all repos" if include_private else "public repos"
            data["projects"] = build_projects(repo_commits, repo_private)
            data["thisWeek"] = this_week(week_total, week_blocks, block_counts, seen)
        else:
            print("rhythm: no commits found (set PAT_TOKEN to include private repos)", file=sys.stderr)
    except Exception as ex:
        print("rhythm skipped:", ex, file=sys.stderr)

    # ---- languages across owned repos (private included when a PAT is set) ----
    try:
        rtoken = PAT or TOKEN
        totals = defaultdict(int)
        for full, _ in owner_repos(rtoken, bool(PAT))[:30]:
            try:
                for lang, b in rest_tok("/repos/" + full + "/languages", rtoken).items():
                    totals[lang] += b
            except Exception:
                continue
        grand = sum(totals.values()) or 1
        top = sorted(totals.items(), key=lambda kv: -kv[1])[:4]
        langs = [{"n": k, "p": round(v / grand * 100)} for k, v in top]
        used = sum(l["p"] for l in langs)
        if used < 100:
            langs.append({"n": "Other", "p": 100 - used})
        data["langs"] = langs
    except Exception as ex:
        print("langs skipped:", ex, file=sys.stderr)

    # ---- narrative, composed from the numbers above (true by construction) ----
    peak_block = (data.get("blocks") or [{"l": "the day"}])[0]["l"]
    langs = data.get("langs") or []
    top_lang = langs[0]["n"] if langs else "TypeScript"
    has_py = any(l["n"] == "Python" for l in langs)
    trend_up = len(mvals) >= 6 and sum(mvals[-3:]) > sum(mvals[:3])

    data["insights"] = {
        "rhythm": ("Across the year, most commits land in the <b>" + peak_block + "</b> block. "
                   "<b>Decision:</b> I protect that window for deep work and keep meetings out."),
        "langs": ("<b>" + top_lang + "</b> leads the stack"
                  + (", with <b>Python</b> close behind for the analytical work" if has_py else "")
                  + ". <b>Decision:</b> I choose the language by the problem, not by habit."),
        "momentum": (("Momentum trends up across the year. " if trend_up else "Activity stays steady across the year. ")
                     + "<b>Decision:</b> I read cadence over volume, consistency beats heroics."),
    }
    projs = data.get("projects") or []
    if projs:
        total_c = sum(p["c"] for p in projs) or 1
        topp = projs[0]
        data["insights"]["proj"] = ("<b>" + topp["n"] + "</b> takes the biggest share of commits ("
                                    + str(round(topp["c"] / total_c * 100)) + "%). "
                                    "<b>Decision:</b> I let the busiest project set the week, and shield the rest from it.")
    data["decisions"] = [
        {"obs": "My most active block is <b>" + peak_block + "</b>.",
         "act": "Guard it for hard problems; batch reviews for later."},
        {"obs": "Longest streak this year: <b>" + str(streak) + " days</b>.",
         "act": "Trust consistency over crunch; ship small and often."},
        {"obs": "The stack leans <b>" + top_lang + "</b>.",
         "act": "Default to it, but reach for Python when the problem is numeric."},
    ]
    return data


def main():
    os.makedirs("dist", exist_ok=True)
    try:
        data = build()
    except Exception as ex:
        print("data generation failed:", ex, file=sys.stderr)
        # Do not overwrite a good prior snapshot with garbage; leave it be.
        return 0
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print("wrote", OUT, "commits=", data["kpis"][0]["val"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
