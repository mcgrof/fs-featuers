#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Render docs/index.html from the JSON catalogs and computed analysis.

Style mirrors the knlp.io aesthetic: dark Tailwind theme via CDN,
card-grid layout, single-column max-w-6xl. Each filesystem gets its
own section with a feature grid; LBS gets its own dedicated panel.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"


def load_features() -> list[dict]:
    feats = []
    for path in sorted(DATA.glob("features_*.json")):
        with open(path) as fp:
            data = json.load(fp)
        feats.extend(data["features"])
    return feats


def load_analysis() -> dict:
    with open(DATA / "analysis.json") as fp:
        return json.load(fp)


FS_BORDER = {
    "xfs": "border-cyan-500",
    "ext4": "border-purple-500",
    "btrfs": "border-emerald-500",
}
FS_HEADING = {
    "xfs": "text-cyan-400",
    "ext4": "text-purple-400",
    "btrfs": "text-emerald-400",
}
FS_BADGE = {
    "xfs": "bg-cyan-900 text-cyan-300",
    "ext4": "bg-purple-900 text-purple-300",
    "btrfs": "bg-emerald-900 text-emerald-300",
}
MM_BADGE = {
    "none": "bg-gray-800 text-gray-400",
    "minor": "bg-orange-900 text-orange-300",
    "major": "bg-rose-900 text-rose-300",
}


def safe(s: object) -> str:
    if s is None:
        return ""
    return html.escape(str(s))


def fmt_num(x: object) -> str:
    if x is None or x == "":
        return "-"
    return f"{x}y"


def feature_card(feat: dict) -> str:
    fs = feat["fs"]
    name = safe(feat.get("name") or feat["short_name"])
    desc = safe(feat.get("description", ""))
    rfc = safe(feat.get("rfc_date") or "?")
    rfc_url = feat.get("rfc_url") or ""
    merged = safe(feat.get("merged_date") or "?")
    merged_ver = safe(feat.get("merged_version") or "?")
    suse = safe(feat.get("suse_first_release") or "-")
    rhel = safe(feat.get("rhel_first_release") or "-")
    mm = feat.get("mm_impact", "none")
    rtm = feat.get("rfc_to_merge_years")
    mte = feat.get("merge_to_enterprise_years")
    fixes = feat.get("fixes_count")
    fixes_window = feat.get("fixes_window_years")
    rfc_link = (
        f'<a href="{safe(rfc_url)}" class="hover:underline">{rfc}</a>'
        if rfc_url
        else rfc
    )
    lbs_marker = (
        '<span class="ml-2 px-2 py-0.5 text-xs rounded bg-yellow-900 '
        'text-yellow-300">LBS</span>'
        if feat["short_name"].endswith("_lbs")
        else ""
    )
    return f"""
    <div class="card rounded-lg p-5 border-l-4 {FS_BORDER[fs]}">
      <div class="flex items-start justify-between mb-2">
        <h3 class="font-semibold {FS_HEADING[fs]}">{name}{lbs_marker}</h3>
        <span class="text-xs {FS_BADGE[fs]} px-2 py-1 rounded">{fs}</span>
      </div>
      <p class="text-gray-400 text-sm mb-3">{desc}</p>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
        <div><span class="text-gray-500">RFC:</span> {rfc_link}</div>
        <div><span class="text-gray-500">Merged:</span> {merged} ({merged_ver})</div>
        <div><span class="text-gray-500">SUSE:</span> {suse}</div>
        <div><span class="text-gray-500">RHEL:</span> {rhel}</div>
        <div><span class="text-gray-500">RFC->merge:</span> {fmt_num(rtm)}</div>
        <div><span class="text-gray-500">Merge->ent:</span> {fmt_num(mte)}</div>
        <div>
          <span class="text-gray-500">mm:</span>
          <span class="{MM_BADGE.get(mm, MM_BADGE['none'])} px-1.5 py-0.5 rounded">
            {mm}
          </span>
        </div>
        <div>
          <span class="text-gray-500">Fixes:</span> {fixes if fixes is not None else "-"}
          {f'<span class="text-gray-600"> ({fixes_window}y)</span>' if fixes_window else ''}
        </div>
      </div>
    </div>
    """


def stat_row(label: str, summary: dict) -> str:
    if summary["n"] == 0:
        return f'<tr><td class="py-2 px-3 text-gray-500">{safe(label)}</td><td colspan="5">no data</td></tr>'
    return f"""
    <tr class="border-b border-gray-800">
      <td class="py-2 px-3 text-gray-300">{safe(label)}</td>
      <td class="py-2 px-3 text-center text-gray-400">{summary['n']}</td>
      <td class="py-2 px-3 text-right font-mono text-emerald-300">{summary['mean']}y</td>
      <td class="py-2 px-3 text-right font-mono text-cyan-300">{summary['median']}y</td>
      <td class="py-2 px-3 text-right font-mono text-amber-300">{summary['p90']}y</td>
      <td class="py-2 px-3 text-right font-mono text-rose-300">{summary['max']}y</td>
    </tr>
    """


def render(features: list[dict], analysis: dict) -> str:
    by_fs = {}
    for f in features:
        by_fs.setdefault(f["fs"], []).append(f)

    # Order: XFS first (canonical), then ext4, then btrfs
    order = ["xfs", "ext4", "btrfs"]
    fs_sections = []
    for fs in order:
        feats = by_fs.get(fs, [])
        if not feats:
            continue
        # Sort by RFC date
        feats.sort(key=lambda f: f.get("rfc_date") or "9999")
        cards = "\n".join(feature_card(f) for f in feats)
        fs_pretty = {"xfs": "XFS", "ext4": "ext4", "btrfs": "btrfs"}[fs]
        fs_sections.append(
            f"""
        <section class="mb-14" id="{fs}">
          <div class="camp-header">
            <h2 class="text-2xl font-bold">{fs_pretty}</h2>
            <p class="text-gray-500 text-sm mt-1">
              {len(feats)} feature{"s" if len(feats) != 1 else ""} catalogued, ordered by RFC date.
            </p>
          </div>
          <div class="grid gap-4">
            {cards}
          </div>
        </section>
        """
        )

    # Aggregate stats table
    stats_html = "\n".join(
        [
            stat_row(s["label"], s)
            for s in [
                analysis["rfc_to_merge_all"],
                analysis["rfc_to_merge_no_lbs"],
                analysis["merge_to_enterprise_all"],
                analysis["rfc_to_enterprise_all"],
            ]
        ]
        + [
            stat_row(s["label"], s)
            for s in analysis["rfc_to_merge_per_fs"].values()
        ]
        + [
            stat_row(s["label"], s)
            for s in analysis["rfc_to_merge_by_mm_impact"].values()
        ]
    )

    # LBS biography panel
    lbs_panels = []
    for fs in ("xfs", "btrfs", "ext4"):
        info = analysis["lbs"]["by_fs"].get(fs)
        if not info:
            continue
        lbs_panels.append(
            f"""
        <div class="card rounded-lg p-5 border-l-4 {FS_BORDER[fs]}">
          <h3 class="font-semibold {FS_HEADING[fs]} mb-2">{fs.upper()} LBS</h3>
          <p class="text-gray-400 text-xs mb-2">
            RFC <span class="font-mono text-gray-300">{safe(info.get("rfc_date"))}</span>
            -> merged <span class="font-mono text-gray-300">{safe(info.get("merged_date"))}</span>
            ({safe(info.get("merged_version"))})
          </p>
          <div class="grid grid-cols-2 gap-2 text-sm">
            <div>
              <div class="text-xs text-gray-500">RFC -> merge</div>
              <div class="font-mono text-emerald-300 text-xl">
                {info.get("rfc_to_merge_years")}y
              </div>
            </div>
            <div>
              <div class="text-xs text-gray-500">first idea -> merge</div>
              <div class="font-mono text-amber-300 text-xl">
                {info.get("first_idea_to_merge_years")}y
              </div>
            </div>
          </div>
        </div>
        """
        )
    lbs_panels_html = "\n".join(lbs_panels)

    lag_rows = []
    for fs, info in analysis["lbs"]["ext_btrfs_lag_vs_xfs"].items():
        lag_rows.append(
            f'<li><strong>{fs.upper()} LBS</strong> merged '
            f'<span class="font-mono">{safe(info["merged_date"])}</span>, '
            f'<span class="text-amber-300">{info["lag_years_after_xfs_lbs"]}y</span> '
            'after XFS LBS</li>'
        )
    lag_html = "\n".join(lag_rows)

    totals = analysis["totals"]
    rfc_all = analysis["rfc_to_merge_all"]
    rfc_no_lbs = analysis["rfc_to_merge_no_lbs"]
    rfc_major = analysis["rfc_to_merge_by_mm_impact"]["major"]

    xfs_lbs = analysis["lbs"]["by_fs"].get("xfs", {})
    speedup_msg = ""
    if rfc_major and rfc_major.get("mean") and xfs_lbs.get("rfc_to_merge_years"):
        speedup_msg = (
            f"LBS-on-XFS RFC-to-merge was "
            f"<span class='font-mono text-emerald-300'>{xfs_lbs['rfc_to_merge_years']}y</span>, "
            f"versus the mm-impact-major bucket mean of "
            f"<span class='font-mono text-amber-300'>{rfc_major['mean']}y</span>."
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>fs-features: Linux filesystem feature stabilization</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {{ background: #0f172a; }}
    .card {{
      background: linear-gradient(145deg, #1e293b, #1a2332);
      border: 1px solid #334155;
      transition: all 0.3s ease;
    }}
    .card:hover {{
      border-color: #3b82f6;
      transform: translateY(-2px);
      box-shadow: 0 10px 40px -10px rgba(59, 130, 246, 0.3);
    }}
    .camp-header {{
      border-bottom: 1px solid #334155;
      padding-bottom: 8px;
      margin-bottom: 16px;
    }}
    .figure img {{
      max-width: 100%;
      height: auto;
      border-radius: 0.5rem;
      border: 1px solid #334155;
    }}
  </style>
</head>
<body class="min-h-screen text-gray-100">
  <div class="max-w-6xl mx-auto px-6 py-12">

    <header class="text-center mb-16">
      <h1 class="text-4xl font-bold mb-3">fs-features</h1>
      <p class="text-xl text-gray-400 mb-2">
        How long does it take to stabilize a Linux filesystem feature?
      </p>
      <p class="text-gray-500 max-w-3xl mx-auto">
        A catalog of {totals["features"]} major XFS, ext4, and btrfs features and the wall-clock
        each took to go from RFC posting through merge through enterprise distribution
        enablement. Re-runnable: the pipeline derives merge dates and Fixes-tag fan-out from
        any kernel tree on disk.
      </p>
      <div class="mt-6 flex justify-center gap-3 text-sm">
        <a href="https://github.com/mcgrof/fs-features"
           class="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg font-medium">
          source
        </a>
        <a href="../data/features_all.csv"
           class="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg font-medium">
          CSV
        </a>
        <a href="../data/analysis.json"
           class="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg font-medium">
          JSON
        </a>
        <a href="../reports/findings.md"
           class="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg font-medium">
          findings
        </a>
      </div>
    </header>

    <section class="mb-14" id="summary">
      <div class="camp-header">
        <h2 class="text-2xl font-bold">Summary</h2>
        <p class="text-gray-500 text-sm mt-1">
          Aggregate stabilization metrics across all {totals["features"]} tracked features.
        </p>
      </div>

      <div class="card rounded-xl p-6 overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-700 text-gray-400">
              <th class="text-left py-2 px-3">metric</th>
              <th class="text-center py-2 px-3">n</th>
              <th class="text-right py-2 px-3">mean</th>
              <th class="text-right py-2 px-3">median</th>
              <th class="text-right py-2 px-3">p90</th>
              <th class="text-right py-2 px-3">max</th>
            </tr>
          </thead>
          <tbody>
            {stats_html}
          </tbody>
        </table>
      </div>

      <div class="mt-6 card rounded-xl p-6">
        <h3 class="font-semibold text-lg mb-3">What the numbers say</h3>
        <p class="text-gray-300 text-sm mb-2">
          Across {rfc_all["n"]} features for which both RFC and merge dates are
          recorded, the median RFC-to-merge wall-clock is
          <span class="font-mono text-cyan-300">{rfc_all["median"]}y</span> and
          the mean is
          <span class="font-mono text-emerald-300">{rfc_all["mean"]}y</span>.
          Removing LBS changes the global mean to
          <span class="font-mono text-amber-300">{rfc_no_lbs["mean"]}y</span> --
          it is a small effect on the headline number because the RFC of the
          successful 2023 LBS attempt landed in
          <span class="font-mono text-emerald-300">0.97y</span>, well within the
          per-feature range.
        </p>
        <p class="text-gray-300 text-sm mb-2">
          {speedup_msg}
        </p>
        <p class="text-gray-300 text-sm">
          The interesting LBS number is not RFC-to-merge but
          <strong>first-idea-to-merge</strong>: from Christoph Lameter's 2007
          compound-page RFC through Nick Piggin's fsblock work, the 2017 LSFMM
          revisit, Dave Chinner's 2018 attempt, and finally Pankaj Raghav's 2023
          series, the total wall-clock is
          <span class="font-mono text-rose-300">17.31y</span>. The 2023 attempt
          is also the first one whose test surface was driven by kdevops with
          AI-assisted triage rather than ad-hoc xfstests runs.
        </p>
      </div>
    </section>

    <section class="mb-14" id="lbs">
      <div class="camp-header">
        <h2 class="text-2xl font-bold">LBS biography</h2>
        <p class="text-gray-500 text-sm mt-1">
          Large Block Sizes is the only feature in the catalog with a multi-RFC
          arc spanning a decade and a half. The chart records every attempt,
          succeeded or not.
        </p>
      </div>

      <div class="figure mb-6">
        <img src="images/lbs_biography.png" alt="LBS biography timeline">
      </div>

      <div class="grid md:grid-cols-3 gap-4 mb-6">
        {lbs_panels_html}
      </div>

      <div class="card rounded-xl p-6">
        <h3 class="font-semibold text-lg mb-3">After XFS, the runway opened</h3>
        <p class="text-gray-300 text-sm mb-3">
          The mm and iomap large-folio infrastructure that LBS-on-XFS forced into
          existence was reused by ext4 and btrfs at much lower cost. Both
          followed inside thirteen months:
        </p>
        <ul class="text-gray-400 text-sm space-y-1 ml-4 list-disc">
          {lag_html}
        </ul>
      </div>

      <div class="figure mt-6">
        <img src="images/lbs_per_fs.png" alt="LBS adoption per fs">
      </div>
    </section>

    <section class="mb-14" id="charts">
      <div class="camp-header">
        <h2 class="text-2xl font-bold">Charts</h2>
        <p class="text-gray-500 text-sm mt-1">
          PNG figures generated from the same JSON the report pulls from.
        </p>
      </div>

      <div class="grid gap-6">
        <div class="figure">
          <h3 class="font-semibold text-lg mb-2">Feature lifecycle</h3>
          <img src="images/timeline.png" alt="Timeline of features">
        </div>
        <div class="figure">
          <h3 class="font-semibold text-lg mb-2">RFC -> merge per feature</h3>
          <img src="images/rfc_to_merge_bars.png" alt="RFC to merge bar chart">
        </div>
        <div class="figure">
          <h3 class="font-semibold text-lg mb-2">Merge -> first enterprise enablement</h3>
          <img src="images/merge_to_enterprise.png" alt="Merge to enterprise bar chart">
        </div>
        <div class="figure">
          <h3 class="font-semibold text-lg mb-2">By mm-impact bucket</h3>
          <img src="images/mm_impact_compare.png" alt="mm-impact comparison">
        </div>
        <div class="figure">
          <h3 class="font-semibold text-lg mb-2">Post-merge Fixes-tag fan-out</h3>
          <img src="images/fixes_distribution.png" alt="Fixes-tag distribution">
        </div>
      </div>
    </section>

    {''.join(fs_sections)}

    <section class="mb-14" id="method">
      <div class="camp-header">
        <h2 class="text-2xl font-bold">Method</h2>
      </div>
      <div class="card rounded-xl p-6 text-sm text-gray-300 space-y-3">
        <p>
          Each feature is represented as a JSON record under
          <code class="text-cyan-300">data/features_&lt;fs&gt;.json</code> with
          a seed commit SHA (the commit that landed the feature flag or
          enabling code), an RFC date pointing at lore.kernel.org or the LWN
          announcement, hand-curated LSFMM exposure and distro enablement, an
          MM-impact classification (none / minor / major), and free-text notes.
        </p>
        <p>
          The pipeline (<code class="text-cyan-300">scripts/enrich.py</code>)
          uses <code>git describe --contains --match v*</code> against a local
          kernel tree to derive the kernel release that contains the seed
          commit, and counts subsequent commits whose message bodies contain
          <code>Fixes: &lt;short-sha&gt;</code> as a proxy for post-merge
          fragility. <code>scripts/analyze.py</code> joins everything, computes
          derived per-feature metrics and aggregate statistics, and emits CSV,
          JSON, Markdown, and PNG outputs. The HTML report is just a renderer
          on top of the same JSON.
        </p>
        <p>
          MM-impact is the qualitative classification the project most cares
          about. "none" covers pure-fs changes. "minor" covers iomap or
          page-cache hooks that did not require generic mm work. "major"
          covers DAX and LBS: the two features that drove year-scale mm
          refactors.
        </p>
        <p>
          The catalog is incomplete by design: minor cleanups and bug-fix
          features are out of scope, only landings that introduced a new
          format-level or interface-level capability are tracked. To add a
          missed feature, append a record to the appropriate JSON file and
          re-run <code>make</code>.
        </p>
      </div>
    </section>

    <footer class="text-center text-gray-600 text-sm border-t border-gray-800 pt-8">
      <p class="mb-2">
        <a href="https://github.com/mcgrof/fs-features" class="hover:text-gray-400">source</a>
        <span class="mx-2">&middot;</span>
        <a href="../PROMPTS.md" class="hover:text-gray-400">PROMPTS.md</a>
        <span class="mx-2">&middot;</span>
        <a href="../reports/analysis.md" class="hover:text-gray-400">analysis.md</a>
      </p>
      <p>MIT License &middot; Luis Chamberlain and contributors</p>
    </footer>
  </div>
</body>
</html>
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=DOCS / "index.html",
    )
    args = parser.parse_args(argv)
    features = load_features()
    sys.path.insert(0, str(ROOT / "scripts"))
    from analyze import compute_derived

    features = [compute_derived(f) for f in features]
    analysis = load_analysis()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as fp:
        fp.write(render(features, analysis))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
