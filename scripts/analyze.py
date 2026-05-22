#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Compute derived metrics from the per-filesystem feature JSON files and
emit:

  data/features_all.csv     -- flat per-feature table with derived metrics
  data/analysis.json        -- aggregate statistics
  reports/analysis.md       -- narrative summary

Derived per-feature:
  rfc_to_merge_years          (merged_date - rfc_date)
  first_idea_to_merge_years   (merged_date - first_idea_date, if present)
  merge_to_suse_years         (suse_first_date - merged_date)
  merge_to_rhel_years         (rhel_first_date - merged_date)
  merge_to_enterprise_years   (min of suse/rhel)
  rfc_to_enterprise_years     (merge_to_enterprise + rfc_to_merge)

Aggregates:
  per-fs RFC-to-merge mean/median/p90
  global RFC-to-merge mean/median/p90
  same with LBS removed
  per-mm-impact bucket: rfc_to_merge mean/median
  LBS speedup ratio versus comparable mm-major features
  ext4/btrfs LBS lag versus XFS LBS merge
  Fixes-count distribution per fs

Re-runnable: outputs are deterministic given the input data.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REPORTS = ROOT / "reports"


def parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        y, m, d = s.split("-")
        return date(int(y), int(m), int(d))
    except (ValueError, AttributeError):
        return None


def years_between(d1: str | None, d2: str | None) -> float | None:
    a, b = parse_date(d1), parse_date(d2)
    if not a or not b:
        return None
    return round((b - a).days / 365.25, 2)


def compute_derived(feat: dict) -> dict:
    out = dict(feat)
    rfc = feat.get("rfc_date")
    first_idea = feat.get("first_idea_date")
    merged = feat.get("merged_date")
    suse = feat.get("suse_first_date")
    rhel = feat.get("rhel_first_date")

    out["rfc_to_merge_years"] = years_between(rfc, merged)
    out["first_idea_to_merge_years"] = years_between(first_idea, merged)
    out["merge_to_suse_years"] = years_between(merged, suse)
    out["merge_to_rhel_years"] = years_between(merged, rhel)

    # earliest of SUSE/RHEL first-enabled date
    earliest = None
    for x in (suse, rhel):
        d = parse_date(x)
        if d and (earliest is None or d < earliest):
            earliest = d
    if earliest and merged:
        out["merge_to_enterprise_years"] = years_between(
            merged, earliest.isoformat()
        )
        out["rfc_to_enterprise_years"] = years_between(
            rfc or first_idea, earliest.isoformat()
        )
    else:
        out["merge_to_enterprise_years"] = None
        out["rfc_to_enterprise_years"] = None
    return out


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * pct / 100
    f, c = int(k), min(int(k) + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def summarize(values: list[float], label: str) -> dict:
    cleaned = [v for v in values if v is not None]
    if not cleaned:
        return {
            "label": label,
            "n": 0,
            "mean": None,
            "median": None,
            "p90": None,
            "min": None,
            "max": None,
        }
    return {
        "label": label,
        "n": len(cleaned),
        "mean": round(statistics.mean(cleaned), 2),
        "median": round(statistics.median(cleaned), 2),
        "p90": (
            round(percentile(cleaned, 90), 2) if len(cleaned) > 1 else cleaned[0]
        ),
        "min": round(min(cleaned), 2),
        "max": round(max(cleaned), 2),
    }


def load_all() -> list[dict]:
    features: list[dict] = []
    for path in sorted(DATA.glob("features_*.json")):
        with open(path) as fp:
            data = json.load(fp)
        for feat in data.get("features", []):
            features.append(compute_derived(feat))
    return features


def emit_csv(features: list[dict], out: Path) -> None:
    columns = [
        "fs",
        "short_name",
        "name",
        "rfc_date",
        "first_idea_date",
        "merged_date",
        "merged_version",
        "merged_sha",
        "rfc_to_merge_years",
        "first_idea_to_merge_years",
        "lsfmm_years",
        "suse_first_release",
        "suse_first_date",
        "suse_enabled_default",
        "rhel_first_release",
        "rhel_first_date",
        "rhel_enabled_default",
        "merge_to_suse_years",
        "merge_to_rhel_years",
        "merge_to_enterprise_years",
        "rfc_to_enterprise_years",
        "mm_impact",
        "fixes_count",
        "fixes_last_date",
        "fixes_window_years",
        "rfc_url",
        "notes",
    ]
    with open(out, "w", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerow(columns)
        for feat in features:
            row = []
            for col in columns:
                v = feat.get(col)
                if isinstance(v, list):
                    v = ";".join(str(x) for x in v)
                row.append("" if v is None else v)
            writer.writerow(row)


def analyze(features: list[dict]) -> dict:
    by_fs: dict[str, list[dict]] = {}
    for f in features:
        by_fs.setdefault(f["fs"], []).append(f)

    rfc_to_merge = [f.get("rfc_to_merge_years") for f in features]
    rfc_to_merge_no_lbs = [
        f.get("rfc_to_merge_years")
        for f in features
        if "_lbs" not in f.get("short_name", "")
    ]
    first_idea_to_merge = [
        f.get("first_idea_to_merge_years") for f in features
        if f.get("first_idea_date")
    ]

    by_mm_impact = {"none": [], "minor": [], "major": []}
    for f in features:
        by_mm_impact.setdefault(f.get("mm_impact", "none"), []).append(
            f.get("rfc_to_merge_years")
        )

    lbs_records = {
        f["fs"]: f
        for f in features
        if f.get("short_name", "").endswith("_lbs")
    }

    # LBS-specific: ext4/btrfs lag versus XFS LBS merge date
    xfs_lbs = lbs_records.get("xfs")
    xfs_lbs_merge = xfs_lbs.get("merged_date") if xfs_lbs else None
    lbs_lag = {}
    for fs in ("ext4", "btrfs"):
        feat = lbs_records.get(fs)
        if feat and xfs_lbs_merge:
            lbs_lag[fs] = {
                "merged_date": feat.get("merged_date"),
                "lag_years_after_xfs_lbs": years_between(
                    xfs_lbs_merge, feat.get("merged_date")
                ),
            }

    return {
        "totals": {
            "features": len(features),
            "by_fs": {fs: len(v) for fs, v in by_fs.items()},
            "by_mm_impact": {
                k: sum(1 for f in features if f.get("mm_impact") == k)
                for k in ("none", "minor", "major")
            },
        },
        "rfc_to_merge_all": summarize(rfc_to_merge, "RFC -> merge (all)"),
        "rfc_to_merge_no_lbs": summarize(
            rfc_to_merge_no_lbs, "RFC -> merge (LBS excluded)"
        ),
        "first_idea_to_merge": summarize(
            first_idea_to_merge,
            "First-idea -> merge (LBS biography only)",
        ),
        "rfc_to_merge_per_fs": {
            fs: summarize(
                [f.get("rfc_to_merge_years") for f in feats],
                f"{fs} RFC -> merge",
            )
            for fs, feats in by_fs.items()
        },
        "rfc_to_merge_by_mm_impact": {
            k: summarize(v, f"mm_impact={k} RFC -> merge")
            for k, v in by_mm_impact.items()
        },
        "merge_to_enterprise_all": summarize(
            [f.get("merge_to_enterprise_years") for f in features],
            "Merge -> enterprise (all)",
        ),
        "rfc_to_enterprise_all": summarize(
            [f.get("rfc_to_enterprise_years") for f in features],
            "RFC -> enterprise (all)",
        ),
        "lbs": {
            "by_fs": {
                fs: {
                    "rfc_date": feat.get("rfc_date"),
                    "first_idea_date": feat.get("first_idea_date"),
                    "merged_date": feat.get("merged_date"),
                    "merged_version": feat.get("merged_version"),
                    "rfc_to_merge_years": feat.get("rfc_to_merge_years"),
                    "first_idea_to_merge_years": feat.get(
                        "first_idea_to_merge_years"
                    ),
                    "fixes_count": feat.get("fixes_count"),
                }
                for fs, feat in lbs_records.items()
            },
            "ext_btrfs_lag_vs_xfs": lbs_lag,
        },
    }


def emit_markdown(report: dict, features: list[dict], out: Path) -> None:
    def fmt_summary(s: dict) -> str:
        if s["n"] == 0:
            return f"{s['label']}: no data"
        return (
            f"{s['label']} (n={s['n']}): "
            f"mean {s['mean']}y, median {s['median']}y, "
            f"p90 {s['p90']}y, min {s['min']}y, max {s['max']}y"
        )

    lines = []
    lines.append("# Filesystem feature stabilization analysis")
    lines.append("")
    lines.append(
        f"Total features tracked: {report['totals']['features']}. "
        + "Per filesystem: "
        + ", ".join(
            f"{k} {v}" for k, v in report["totals"]["by_fs"].items()
        )
        + "."
    )
    lines.append("")
    lines.append("## RFC to merge")
    lines.append("")
    lines.append(fmt_summary(report["rfc_to_merge_all"]))
    lines.append(fmt_summary(report["rfc_to_merge_no_lbs"]))
    lines.append("")
    lines.append("Per filesystem:")
    for fs, s in report["rfc_to_merge_per_fs"].items():
        lines.append(f"- {fmt_summary(s)}")
    lines.append("")
    lines.append("By mm-impact bucket:")
    for k, s in report["rfc_to_merge_by_mm_impact"].items():
        lines.append(f"- {fmt_summary(s)}")
    lines.append("")
    lines.append("## Merge to enterprise (first SUSE or RHEL enablement)")
    lines.append("")
    lines.append(fmt_summary(report["merge_to_enterprise_all"]))
    lines.append(fmt_summary(report["rfc_to_enterprise_all"]))
    lines.append("")
    lines.append("## LBS biography")
    lines.append("")
    for fs, info in report["lbs"]["by_fs"].items():
        rtm = info.get("rfc_to_merge_years")
        fitm = info.get("first_idea_to_merge_years")
        lines.append(
            f"- {fs} LBS: RFC {info.get('rfc_date')}, merged "
            f"{info.get('merged_date')} ({info.get('merged_version')}), "
            f"RFC-to-merge {rtm}y, first-idea-to-merge "
            f"{fitm}y, fixes-tag count {info.get('fixes_count')}."
        )
    lines.append("")
    if report["lbs"]["ext_btrfs_lag_vs_xfs"]:
        lines.append("LBS adoption after XFS:")
        for fs, info in report["lbs"]["ext_btrfs_lag_vs_xfs"].items():
            lines.append(
                f"- {fs} LBS merged {info['merged_date']} "
                f"({info['lag_years_after_xfs_lbs']}y after XFS LBS)"
            )
    lines.append("")
    lines.append("## Per-feature detail")
    lines.append("")
    lines.append(
        "| fs | feature | RFC | merged | RFC->merge (y) | "
        "merge->enterprise (y) | mm-impact | fixes |"
    )
    lines.append("|---|---|---|---|---|---|---|---|")
    for f in features:
        lines.append(
            "| {fs} | {name} | {rfc} | {m} | {rtm} | {me} | {mm} | {fx} |".format(
                fs=f.get("fs"),
                name=f.get("short_name"),
                rfc=f.get("rfc_date") or "?",
                m=f.get("merged_date") or "?",
                rtm=(f.get("rfc_to_merge_years") or "?"),
                me=(f.get("merge_to_enterprise_years") or "-"),
                mm=f.get("mm_impact") or "?",
                fx=f.get("fixes_count"),
            )
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as fp:
        fp.write("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv", type=Path, default=DATA / "features_all.csv"
    )
    parser.add_argument(
        "--json", type=Path, default=DATA / "analysis.json"
    )
    parser.add_argument(
        "--md", type=Path, default=REPORTS / "analysis.md"
    )
    args = parser.parse_args(argv)

    features = load_all()
    emit_csv(features, args.csv)
    report = analyze(features)
    with open(args.json, "w") as fp:
        json.dump(report, fp, indent=2)
        fp.write("\n")
    emit_markdown(report, features, args.md)
    print(
        f"wrote {args.csv} ({len(features)} rows), {args.json}, {args.md}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
