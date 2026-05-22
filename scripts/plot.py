#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Render PNG figures for the fs-features report.

Outputs to docs/images/:
  timeline.png            -- RFC/merge/enterprise gantt per feature
  rfc_to_merge_bars.png   -- per-feature RFC-to-merge bar chart
  merge_to_enterprise.png -- per-feature merge-to-enterprise bar chart
  lbs_biography.png       -- LBS timeline with prior failed attempts
  lbs_per_fs.png          -- LBS adoption sequence (XFS -> btrfs -> ext4)
  mm_impact_compare.png   -- RFC-to-merge by mm-impact bucket
  fixes_distribution.png  -- post-merge Fixes-tag fan-out distribution
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
IMAGES = ROOT / "docs" / "images"

# Dark theme matching the knlp.io aesthetic
BG = "#0f172a"
PANEL = "#1e293b"
AXIS = "#334155"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"

FS_COLORS = {
    "xfs": "#22d3ee",  # cyan-400
    "ext4": "#a78bfa",  # purple-400
    "btrfs": "#34d399",  # emerald-400
}
MM_COLORS = {
    "none": "#94a3b8",
    "minor": "#fb923c",
    "major": "#f87171",
}


def style_axes(ax):
    ax.set_facecolor(PANEL)
    for spine in ax.spines.values():
        spine.set_color(AXIS)
    ax.tick_params(colors=MUTED, which="both")
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color(TEXT)
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)
    ax.title.set_color(TEXT)
    ax.grid(True, color=AXIS, alpha=0.3, linestyle="--", linewidth=0.5)


def parse_date(s):
    if not s:
        return None
    try:
        y, m, d = s.split("-")
        return date(int(y), int(m), int(d))
    except (ValueError, AttributeError):
        return None


def load_features() -> list[dict]:
    feats = []
    for path in sorted(DATA.glob("features_*.json")):
        with open(path) as fp:
            data = json.load(fp)
        feats.extend(data["features"])
    return feats


def fig_setup(figsize=(12, 7), title=None):
    fig, ax = plt.subplots(figsize=figsize, facecolor=BG)
    style_axes(ax)
    if title:
        ax.set_title(title, fontsize=14, fontweight="bold", pad=16, color=TEXT)
    return fig, ax


def save(fig, name):
    IMAGES.mkdir(parents=True, exist_ok=True)
    out = IMAGES / name
    fig.tight_layout()
    fig.savefig(out, dpi=140, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def plot_timeline(features):
    fig, ax = fig_setup(
        figsize=(14, max(8, len(features) * 0.25)),
        title="Feature lifecycle: RFC -> merge -> enterprise",
    )

    rows = []
    for f in features:
        rfc = parse_date(f.get("rfc_date"))
        merged = parse_date(f.get("merged_date"))
        suse = parse_date(f.get("suse_first_date"))
        rhel = parse_date(f.get("rhel_first_date"))
        enterprise = None
        for d in (suse, rhel):
            if d and (enterprise is None or d < enterprise):
                enterprise = d
        rows.append((f, rfc, merged, enterprise))

    # Sort by RFC date so the chart reads as a chronological story
    rows.sort(key=lambda r: r[1] or date(2999, 1, 1))
    labels = []
    for i, (f, rfc, merged, enterprise) in enumerate(rows):
        y = i
        fs_color = FS_COLORS.get(f["fs"], MUTED)
        labels.append(f"[{f['fs']}] {f['short_name']}")
        if rfc and merged:
            ax.plot(
                [rfc, merged], [y, y], color=fs_color, linewidth=2.5, alpha=0.9
            )
        if merged and enterprise:
            ax.plot(
                [merged, enterprise],
                [y, y],
                color=fs_color,
                linewidth=1,
                alpha=0.5,
                linestyle="--",
            )
        # Markers
        if rfc:
            ax.plot(rfc, y, "o", color=fs_color, markersize=4)
        if merged:
            ax.plot(
                merged, y, "s", color=fs_color, markersize=5, alpha=0.95
            )
        if enterprise:
            ax.plot(
                enterprise, y, "^", color=fs_color, markersize=5, alpha=0.95
            )
        # Highlight LBS
        if f["short_name"].endswith("_lbs"):
            ax.axhspan(y - 0.4, y + 0.4, color="#fde68a", alpha=0.08, zorder=0)

    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlabel("year")

    legend_elements = [
        Patch(facecolor=FS_COLORS["xfs"], label="XFS"),
        Patch(facecolor=FS_COLORS["ext4"], label="ext4"),
        Patch(facecolor=FS_COLORS["btrfs"], label="btrfs"),
    ]
    leg = ax.legend(
        handles=legend_elements,
        loc="upper left",
        facecolor=PANEL,
        edgecolor=AXIS,
        labelcolor=TEXT,
    )
    for text in leg.get_texts():
        text.set_color(TEXT)

    save(fig, "timeline.png")


def plot_rfc_to_merge_bars(features):
    rows = [
        (f, f.get("rfc_to_merge_years"))
        for f in features
        if f.get("rfc_to_merge_years") is not None
    ]
    rows.sort(key=lambda r: r[1])
    fig, ax = fig_setup(
        figsize=(12, max(8, len(rows) * 0.25)),
        title="RFC -> merge wall-clock per feature",
    )

    labels, values, colors = [], [], []
    for f, v in rows:
        labels.append(f"[{f['fs']}] {f['short_name']}")
        values.append(v)
        # color LBS distinctly
        if f["short_name"].endswith("_lbs"):
            colors.append("#fde047")  # yellow-300
        else:
            colors.append(FS_COLORS.get(f["fs"], MUTED))

    bars = ax.barh(labels, values, color=colors, edgecolor=AXIS, linewidth=0.5)
    ax.invert_yaxis()
    ax.set_xlabel("years")
    ax.tick_params(axis="y", labelsize=8)

    # Reference lines
    import statistics

    mean_v = statistics.mean(values)
    median_v = statistics.median(values)
    ax.axvline(
        mean_v,
        color="#f59e0b",
        linestyle="--",
        linewidth=1,
        label=f"mean {mean_v:.2f}y",
    )
    ax.axvline(
        median_v,
        color="#10b981",
        linestyle=":",
        linewidth=1,
        label=f"median {median_v:.2f}y",
    )
    leg = ax.legend(
        loc="lower right",
        facecolor=PANEL,
        edgecolor=AXIS,
    )
    for t in leg.get_texts():
        t.set_color(TEXT)

    # annotate LBS
    for f, v in rows:
        if f["short_name"].endswith("_lbs"):
            ax.annotate(
                "LBS",
                xy=(v, labels.index(f"[{f['fs']}] {f['short_name']}")),
                xytext=(v + 0.05, labels.index(f"[{f['fs']}] {f['short_name']}")),
                color="#fde047",
                fontweight="bold",
                fontsize=9,
                va="center",
            )
    save(fig, "rfc_to_merge_bars.png")


def plot_merge_to_enterprise(features):
    rows = [
        (f, f.get("merge_to_enterprise_years"))
        for f in features
        if f.get("merge_to_enterprise_years") is not None
    ]
    rows.sort(key=lambda r: r[1])
    if not rows:
        return
    fig, ax = fig_setup(
        figsize=(12, max(6, len(rows) * 0.3)),
        title="Merge -> first enterprise enablement (SUSE or RHEL)",
    )

    labels, values, colors = [], [], []
    for f, v in rows:
        labels.append(f"[{f['fs']}] {f['short_name']}")
        values.append(v)
        if f["short_name"].endswith("_lbs"):
            colors.append("#fde047")
        else:
            colors.append(MM_COLORS.get(f.get("mm_impact"), MUTED))

    ax.barh(labels, values, color=colors, edgecolor=AXIS, linewidth=0.5)
    ax.invert_yaxis()
    ax.set_xlabel("years")
    ax.tick_params(axis="y", labelsize=8)

    import statistics

    mean_v = statistics.mean(values)
    ax.axvline(
        mean_v,
        color="#f59e0b",
        linestyle="--",
        linewidth=1,
        label=f"mean {mean_v:.2f}y",
    )
    legend_elements = [
        Patch(facecolor=MM_COLORS["none"], label="mm-impact none"),
        Patch(facecolor=MM_COLORS["minor"], label="mm-impact minor"),
        Patch(facecolor=MM_COLORS["major"], label="mm-impact major"),
        Patch(facecolor="#fde047", label="LBS"),
    ]
    leg = ax.legend(
        handles=legend_elements,
        loc="lower right",
        facecolor=PANEL,
        edgecolor=AXIS,
    )
    for t in leg.get_texts():
        t.set_color(TEXT)

    save(fig, "merge_to_enterprise.png")


def plot_lbs_biography(features):
    """Timeline showing LBS's 17-year arc of attempts."""
    fig, ax = fig_setup(
        figsize=(14, 5),
        title="LBS biography: 17 years of attempts, finally merged in 2024",
    )

    lbs_xfs = next(
        (f for f in features if f["short_name"] == "xfs_lbs"), None
    )
    if not lbs_xfs:
        return

    events = []
    # historical_attempts already contains the first idea + every prior
    # stalled RFC, so it is the canonical source for the pre-success arc.
    for h in lbs_xfs.get("historical_attempts", []):
        d = parse_date(h["date"])
        if not d:
            continue
        author = h["author"].split(",")[0]
        # Compact two-line label for readability on a tight timeline
        events.append(
            (
                d,
                f"{author}\n{h.get('note', '')[:38]}".rstrip(),
                "#fb923c",
                h.get("note", "")[:60],
            )
        )
    events.append(
        (
            parse_date(lbs_xfs["rfc_date"]),
            "Pankaj Raghav et al:\nXFS LBS RFC",
            "#fde047",
            "the attempt that landed",
        )
    )
    events.append(
        (
            parse_date(lbs_xfs["merged_date"]),
            "XFS LBS merged\n(v6.12)",
            "#34d399",
            "0.97 years from RFC",
        )
    )
    suse = parse_date(lbs_xfs.get("suse_first_date"))
    rhel = parse_date(lbs_xfs.get("rhel_first_date"))
    if rhel:
        events.append(
            (rhel, "RHEL 10\n(tech preview)", "#22d3ee", "0.71y from merge")
        )

    events = [e for e in events if e[0]]
    events.sort(key=lambda e: e[0])
    xs = [e[0] for e in events]
    ys = [0.5] * len(events)
    colors = [e[2] for e in events]

    # baseline
    ax.axhline(0.5, color=AXIS, linewidth=1, alpha=0.6, zorder=0)
    ax.scatter(xs, ys, c=colors, s=200, zorder=2, edgecolors=TEXT, linewidth=1)
    # alternating labels above/below, with extra offset when adjacent events
    # are within 1 year of each other to avoid label collisions
    last_year = None
    sign = 1
    for i, (d, label, color, sub) in enumerate(events):
        year = d.year + d.month / 12
        if last_year is not None and abs(year - last_year) < 1.5:
            sign = -sign  # flip to opposite side
            offset = 0.45 * sign
        else:
            offset = 0.22 * (1 if i % 2 == 0 else -1)
            sign = 1 if offset > 0 else -1
        last_year = year
        va = "bottom" if offset > 0 else "top"
        ax.annotate(
            f"{label}\n{d.isoformat()}",
            xy=(d, 0.5),
            xytext=(d, 0.5 + offset),
            ha="center",
            va=va,
            color=TEXT,
            fontsize=9,
            fontweight="bold",
            arrowprops=dict(arrowstyle="-", color=AXIS, lw=0.6),
        )

    ax.set_ylim(-0.2, 1.2)
    ax.set_yticks([])
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.spines["left"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.set_xlabel("")

    save(fig, "lbs_biography.png")


def plot_lbs_per_fs(features):
    lbs = {
        f["fs"]: f for f in features if f["short_name"].endswith("_lbs")
    }
    if not lbs:
        return
    fig, ax = fig_setup(
        figsize=(11, 5),
        title="LBS adoption: XFS opened the runway, ext4 and btrfs followed",
    )

    rows = []
    for fs in ("xfs", "btrfs", "ext4"):
        f = lbs.get(fs)
        if not f:
            continue
        rfc = parse_date(f.get("rfc_date"))
        merged = parse_date(f.get("merged_date"))
        rows.append((fs, rfc, merged, f))

    for i, (fs, rfc, merged, f) in enumerate(rows):
        y = i
        c = FS_COLORS.get(fs, MUTED)
        ax.plot([rfc, merged], [y, y], color=c, linewidth=4, solid_capstyle="round")
        ax.plot(rfc, y, "o", color=c, markersize=10)
        ax.plot(merged, y, "s", color=c, markersize=11)
        rtm = f.get("rfc_to_merge_years")
        ax.annotate(
            f"{fs.upper()} LBS, RFC->merge {rtm}y",
            xy=(merged, y),
            xytext=(10, 0),
            textcoords="offset points",
            color=TEXT,
            fontsize=10,
            fontweight="bold",
            va="center",
        )
        ax.annotate(
            f"RFC {rfc.isoformat() if rfc else '?'}",
            xy=(rfc, y),
            xytext=(-10, 0),
            textcoords="offset points",
            color=MUTED,
            fontsize=9,
            ha="right",
            va="center",
        )

    ax.set_yticks([])
    ax.set_xlabel("year")
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.invert_yaxis()
    save(fig, "lbs_per_fs.png")


def plot_mm_impact_compare(features):
    fig, ax = fig_setup(
        figsize=(11, 6),
        title="RFC -> merge by mm-impact bucket",
    )

    buckets = {"none": [], "minor": [], "major": []}
    for f in features:
        v = f.get("rfc_to_merge_years")
        if v is None:
            continue
        buckets.setdefault(f.get("mm_impact", "none"), []).append((v, f))

    labels = []
    data = []
    for bucket in ("none", "minor", "major"):
        rows = buckets[bucket]
        labels.append(f"{bucket}\n(n={len(rows)})")
        data.append([v for v, _ in rows])

    bp = ax.boxplot(
        data,
        patch_artist=True,
        widths=0.5,
        tick_labels=labels,
        medianprops=dict(color=TEXT, linewidth=2),
        whiskerprops=dict(color=MUTED),
        capprops=dict(color=MUTED),
        flierprops=dict(
            marker="o", markerfacecolor="#f87171", markeredgecolor="none"
        ),
    )
    for patch, bucket in zip(bp["boxes"], ("none", "minor", "major")):
        patch.set_facecolor(MM_COLORS[bucket])
        patch.set_alpha(0.6)

    # Overlay individual points; LBS in gold
    for x, bucket in enumerate(("none", "minor", "major"), start=1):
        for v, f in buckets[bucket]:
            color = "#fde047" if f["short_name"].endswith("_lbs") else TEXT
            ax.scatter(
                x,
                v,
                color=color,
                s=30,
                alpha=0.8,
                edgecolors=BG,
                linewidth=0.4,
                zorder=3,
            )

    ax.set_ylabel("years from RFC to merge")
    save(fig, "mm_impact_compare.png")


def plot_fixes_distribution(features):
    counts = [
        (f, f.get("fixes_count") or 0)
        for f in features
        if f.get("fixes_count") is not None
    ]
    counts.sort(key=lambda x: x[1], reverse=True)
    counts = counts[:30]
    fig, ax = fig_setup(
        figsize=(12, max(6, len(counts) * 0.25)),
        title="Post-merge Fixes-tag fan-out per feature (top 30)",
    )
    labels = [f"[{f['fs']}] {f['short_name']}" for f, _ in counts]
    values = [v for _, v in counts]
    colors = [FS_COLORS.get(f["fs"], MUTED) for f, _ in counts]
    ax.barh(labels, values, color=colors, edgecolor=AXIS, linewidth=0.5)
    ax.invert_yaxis()
    ax.set_xlabel("Fixes: <merged_sha> count")
    ax.tick_params(axis="y", labelsize=8)
    save(fig, "fixes_distribution.png")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    features = load_features()
    # Compute derived metrics inline (analyze.py does the canonical compute,
    # but for plot purposes we recompute the per-feature derived fields)
    sys.path.insert(0, str(ROOT / "scripts"))
    from analyze import compute_derived

    features = [compute_derived(f) for f in features]
    plot_timeline(features)
    plot_rfc_to_merge_bars(features)
    plot_merge_to_enterprise(features)
    plot_lbs_biography(features)
    plot_lbs_per_fs(features)
    plot_mm_impact_compare(features)
    plot_fixes_distribution(features)
    return 0


if __name__ == "__main__":
    sys.exit(main())
