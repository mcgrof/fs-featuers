#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Render PNG figures for the fs-features report.

Outputs to docs/images/:
  timeline.png            -- RFC/merge/enterprise gantt per feature
  rfc_to_merge_bars.png   -- per-feature RFC-to-merge bar chart
  merge_to_enterprise.png -- per-feature merge-to-enterprise bar chart
  mm_impact_compare.png   -- RFC-to-merge by mm-impact bucket
  fixes_distribution.png  -- post-merge Fixes-tag fan-out distribution

Outputs to docs/case_studies/images/:
  lbs_biography.png       -- LBS arc, 2007 -> 2026
  lbs_per_fs.png          -- LBS adoption sequence (XFS -> btrfs -> ext4)
  lbs_xfs_v6_12.png       -- Phase 1: seven mm/iomap/xfs commits, Aug-Sep 2024
  lbs_bdev_v6_15.png      -- Phase 2: bdev + buffer-head series, Dec 2024-Mar 2025
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
CASE_STUDY_IMAGES = ROOT / "docs" / "case_studies" / "images"

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


def save(fig, name, dest: Path = IMAGES):
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / name
    fig.tight_layout()
    fig.savefig(out, dpi=140, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def _stack_event_labels(events, lane_step=0.32, min_days=500, baseline=0.0):
    """Place a list of (date, label, color) events on a horizontal
    timeline with collision-free labels stacked into discrete y-lanes
    alternating above/below the baseline. Returns a list of
    (date, label, color, sign, lane) placements ready for annotation.
    """
    from datetime import timedelta

    last_x: dict[tuple[int, int], object] = {}
    placements = []
    for i, (d, label, color) in enumerate(events):
        sign = 1 if i % 2 == 0 else -1
        lane = 1
        while True:
            prev_x = last_x.get((sign, lane))
            if prev_x is None or (d - prev_x) >= timedelta(days=min_days):
                last_x[(sign, lane)] = d
                placements.append((d, label, color, sign, lane))
                break
            lane += 1
    return placements


def _render_event_timeline(
    ax, events, baseline=0.0, lane_step=0.32, min_days=500, marker_size=240,
):
    """Render a stacked-label event timeline onto ax. Mutates ax in place
    and returns the placements list."""
    placements = _stack_event_labels(events, lane_step, min_days, baseline)
    xs = [e[0] for e in events]
    colors = [e[2] for e in events]
    ax.axhline(baseline, color=AXIS, linewidth=1.5, alpha=0.7, zorder=0)
    ax.scatter(
        xs, [baseline] * len(events), c=colors, s=marker_size, zorder=3,
        edgecolors=TEXT, linewidth=1.2,
    )
    for d, label, color, sign, lane in placements:
        y = baseline + sign * (0.18 + lane_step * (lane - 1))
        va = "bottom" if sign > 0 else "top"
        ax.annotate(
            f"{label}\n{d.isoformat()}",
            xy=(d, baseline), xytext=(d, y),
            ha="center", va=va, color=TEXT, fontsize=9, fontweight="bold",
            arrowprops=dict(arrowstyle="-", color=AXIS, lw=0.6),
        )
    max_up = max(
        (lane for (_, _, _, sign, lane) in placements if sign > 0), default=0
    )
    max_dn = max(
        (lane for (_, _, _, sign, lane) in placements if sign < 0), default=0
    )
    top = 0.18 + lane_step * max_up + 0.55
    bot = -(0.18 + lane_step * max_dn + 0.55)
    ax.set_ylim(bot, top)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.set_xlabel("")
    return placements


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
    """Full LBS arc, from Lameter 2007 to LBS-everywhere. Lives under the
    case-study tree so the case_studies/lbs.html page can embed it."""
    fig, ax = fig_setup(
        figsize=(15, 6.5),
        title="LBS biography: from Lameter 2007 to LBS-everywhere 2026",
    )

    lbs_xfs = next(
        (f for f in features if f["short_name"] == "xfs_lbs"), None
    )
    if not lbs_xfs:
        return

    events = []
    for h in lbs_xfs.get("historical_attempts", []):
        d = parse_date(h["date"])
        if not d:
            continue
        author = h["author"].split(",")[0]
        events.append((d, author, "#fb923c"))
    events.append(
        (parse_date(lbs_xfs["rfc_date"]), "Raghav: XFS LBS RFC", "#fde047")
    )
    events.append(
        (parse_date(lbs_xfs["merged_date"]), "XFS LBS merged v6.12", "#34d399")
    )
    rhel = parse_date(lbs_xfs.get("rhel_first_date"))
    if rhel:
        events.append((rhel, "RHEL 10 TP", "#22d3ee"))
    ext4 = next((f for f in features if f["short_name"] == "ext4_lbs"), None)
    btrfs = next((f for f in features if f["short_name"] == "btrfs_lbs"), None)
    if btrfs and btrfs.get("merged_date"):
        events.append(
            (parse_date(btrfs["merged_date"]), "btrfs LBS v6.18 (exp.)", "#34d399")
        )
    if ext4 and ext4.get("merged_date"):
        events.append(
            (parse_date(ext4["merged_date"]), "ext4 LBS v6.19", "#a78bfa")
        )

    events = [e for e in events if e[0]]
    events.sort(key=lambda e: e[0])

    _render_event_timeline(ax, events)

    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    legend_elements = [
        Patch(facecolor="#fb923c", label="prior stalled attempt"),
        Patch(facecolor="#fde047", label="RFC that landed"),
        Patch(facecolor="#34d399", label="merged"),
        Patch(facecolor="#a78bfa", label="ext4 follow-on"),
        Patch(facecolor="#22d3ee", label="enterprise pickup"),
    ]
    leg = ax.legend(
        handles=legend_elements, loc="upper left",
        facecolor=PANEL, edgecolor=AXIS, fontsize=8, framealpha=0.85,
    )
    for t in leg.get_texts():
        t.set_color(TEXT)

    save(fig, "lbs_biography.png", dest=CASE_STUDY_IMAGES)


def plot_lbs_xfs_v6_12():
    """Per-phase timeline: the seven mm/iomap/xfs commits that landed
    XFS LBS in v6.12 (late Aug -- early Sep 2024)."""
    from datetime import date as _date

    fig, ax = fig_setup(
        figsize=(15, 5.5),
        title="Phase 1: XFS LBS lands in v6.12 (seven commits, late Aug -- early Sep 2024)",
    )
    events = [
        (_date(2024, 8, 23), "filemap: mapping_min_order folios", "#22d3ee"),
        (_date(2024, 8, 23), "readahead: mapping_min_order in readahead", "#22d3ee"),
        (_date(2024, 9, 2),  "mm: split folio in min-order chunks", "#22d3ee"),
        (_date(2024, 9, 2),  "filemap: cap PTE range in folio_map_range", "#22d3ee"),
        (_date(2024, 9, 2),  "iomap: fix iomap_dio_zero for bs > ps", "#fb923c"),
        (_date(2024, 9, 2),  "xfs: expose block size in stat", "#34d399"),
        (_date(2024, 9, 2),  "xfs: generic xfs_sb_validate_fsb_count", "#34d399"),
        (_date(2024, 9, 3),  "xfs: enable bs > ps support", "#fde047"),
    ]

    _render_event_timeline(ax, events, min_days=3, lane_step=0.30)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))

    legend_elements = [
        Patch(facecolor="#22d3ee", label="mm / page cache"),
        Patch(facecolor="#fb923c", label="iomap"),
        Patch(facecolor="#34d399", label="XFS plumbing"),
        Patch(facecolor="#fde047", label="XFS enable LBS"),
    ]
    leg = ax.legend(
        handles=legend_elements, loc="upper left",
        facecolor=PANEL, edgecolor=AXIS, fontsize=8, framealpha=0.85,
    )
    for t in leg.get_texts():
        t.set_color(TEXT)
    save(fig, "lbs_xfs_v6_12.png", dest=CASE_STUDY_IMAGES)


def plot_lbs_bdev_v6_15():
    """Per-phase timeline: the v6.15 'Enable bs > ps for block devices'
    series that lifted LBS through the bdev cache + buffer-head path,
    setting the stage for ext4 LBS."""
    from datetime import date as _date

    fig, ax = fig_setup(
        figsize=(15, 5.5),
        title="Phase 2: bdev cache + buffer heads for LBS (v6.15, Dec 2024 -- Mar 2025)",
    )
    events = [
        (_date(2024, 12, 18), "block/bdev: helper for max block size check", "#22d3ee"),
        (_date(2025, 2, 24),  "fs/buffer: simplify block_read_full_folio", "#fb923c"),
        (_date(2025, 2, 24),  "fs/mpage: blocks_per_folio vs blocks_per_page", "#fb923c"),
        (_date(2025, 2, 24),  "fs/buffer + fs/mpage: drop large folio guard", "#fb923c"),
        (_date(2025, 2, 24),  "block/bdev: lift block size limit to 64k", "#22d3ee"),
        (_date(2025, 2, 24),  "block/bdev: enable large folios for LBS", "#22d3ee"),
        (_date(2025, 2, 24),  "bdev: bdev_io_min() for statx block size", "#22d3ee"),
        (_date(2025, 3, 7),   "FS_LBS flag gate in include/linux/fs.h", "#fde047"),
    ]

    _render_event_timeline(ax, events, min_days=14, lane_step=0.30)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

    legend_elements = [
        Patch(facecolor="#22d3ee", label="block / bdev"),
        Patch(facecolor="#fb923c", label="fs/buffer + fs/mpage"),
        Patch(facecolor="#fde047", label="VFS gating flag"),
    ]
    leg = ax.legend(
        handles=legend_elements, loc="upper left",
        facecolor=PANEL, edgecolor=AXIS, fontsize=8, framealpha=0.85,
    )
    for t in leg.get_texts():
        t.set_color(TEXT)
    save(fig, "lbs_bdev_v6_15.png", dest=CASE_STUDY_IMAGES)


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
    save(fig, "lbs_per_fs.png", dest=CASE_STUDY_IMAGES)


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
    plot_mm_impact_compare(features)
    plot_fixes_distribution(features)
    # Case-study figures (output into docs/case_studies/images/)
    plot_lbs_biography(features)
    plot_lbs_per_fs(features)
    plot_lbs_xfs_v6_12()
    plot_lbs_bdev_v6_15()
    return 0


if __name__ == "__main__":
    sys.exit(main())
