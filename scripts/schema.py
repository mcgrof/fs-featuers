#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Data schema for fs-features.

A Feature record captures one filesystem capability through its lifecycle:
RFC posting, merge into Linus's tree, LSFMM exposure, enterprise distro
enablement, and the Fixes-tag fan-out that accumulated after merge.

Hand-curated fields (RFC dates, LSFMM coverage, distro enablement) carry
explicit provenance via *_source fields so re-runs can be incremental and
sources can be re-checked.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Feature:
    # Identity
    name: str
    short_name: str
    fs: str  # "xfs" | "ext4" | "btrfs" | "vfs" | "mm"
    description: str = ""

    # RFC -- first time the patch series that ultimately landed was posted
    # on lore.kernel.org, marked [RFC] or similar exploratory tag. For
    # features with multiple failed prior attempts (LBS being the canonical
    # example), use first_idea_date for the earliest known proposal and
    # rfc_date for the RFC of the attempt that actually landed.
    rfc_date: Optional[str] = None  # ISO YYYY-MM-DD
    rfc_url: Optional[str] = None
    rfc_source: str = "manual"
    # earliest known proposal/RFC even if it later stalled, to track the
    # total "first idea -> merge" wall-clock distinct from the successful
    # attempt's RFC-to-merge.
    first_idea_date: Optional[str] = None
    first_idea_url: Optional[str] = None
    first_idea_note: Optional[str] = None
    # prior failed RFCs / stalled attempts, for the LBS-style biography
    historical_attempts: list[dict] = field(default_factory=list)

    # Merge -- the commit that marks the feature landing in mainline.
    # For features assembled from many commits, this is the merge commit
    # of the topic branch or the commit that flips the Kconfig/feature flag.
    merged_sha: Optional[str] = None
    merged_date: Optional[str] = None  # auto-derived if merged_sha set
    merged_version: Optional[str] = None  # auto-derived; e.g. "v6.12"
    merge_source: str = "kernel-tree"

    # LSFMM coverage
    lsfmm_years: list[int] = field(default_factory=list)
    lsfmm_urls: list[str] = field(default_factory=list)
    lsfmm_source: str = "manual"

    # SUSE Linux Enterprise enablement
    suse_first_release: Optional[str] = None  # "SLE 15 SP4"
    suse_first_date: Optional[str] = None  # ISO YYYY-MM-DD
    suse_enabled_default: Optional[bool] = None
    suse_notes: Optional[str] = None
    suse_source: str = "manual"

    # Red Hat Enterprise Linux enablement
    rhel_first_release: Optional[str] = None  # "RHEL 9.2"
    rhel_first_date: Optional[str] = None  # ISO YYYY-MM-DD
    rhel_enabled_default: Optional[bool] = None
    rhel_notes: Optional[str] = None
    rhel_source: str = "manual"

    # Core MM impact -- whether this feature required changes to mm/.
    # "none": pure fs change. "minor": fs touched mm but no mm-wide
    # implications. "major": broad MM changes (LBS-class).
    mm_impact: str = "none"
    mm_impact_notes: Optional[str] = None

    # Fixes-tag fan-out: commits that cite the merged_sha (or its topic
    # series) in a Fixes: trailer. A proxy for post-merge fragility.
    fixes_count: Optional[int] = None
    fixes_window_years: Optional[float] = None
    fixes_last_date: Optional[str] = None
    fixes_source: str = "kernel-tree"

    # Optional context
    notes: Optional[str] = None


def feature_to_dict(f: Feature) -> dict:
    return asdict(f)


def dict_to_feature(d: dict) -> Feature:
    return Feature(**d)


def load_features(path: Path) -> list[Feature]:
    if not path.exists():
        return []
    with open(path) as fp:
        data = json.load(fp)
    return [dict_to_feature(d) for d in data["features"]]


def save_features(path: Path, features: list[Feature], fs: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = {
        "filesystem": fs,
        "features": [feature_to_dict(f) for f in features],
    }
    with open(path, "w") as fp:
        json.dump(out, fp, indent=2)
        fp.write("\n")


# Enterprise release calendar -- approximate first-ship dates and kernel
# bases. Used to validate that a feature could in principle be present.
# Source: vendor release notes.
SUSE_RELEASES = [
    ("SLE 12 SP4", "2018-12-10", "4.12"),
    ("SLE 12 SP5", "2019-12-09", "4.12"),
    ("SLE 15", "2018-07-16", "4.12"),
    ("SLE 15 SP1", "2019-06-24", "4.12"),
    ("SLE 15 SP2", "2020-07-21", "5.3"),
    ("SLE 15 SP3", "2021-06-22", "5.3"),
    ("SLE 15 SP4", "2022-06-21", "5.14"),
    ("SLE 15 SP5", "2023-06-20", "5.14"),
    ("SLE 15 SP6", "2024-06-13", "6.4"),
    ("SLE 15 SP7", "2025-06-26", "6.4"),
    ("SUSE 16.0", "2026-06-01", "6.12"),
]

RHEL_RELEASES = [
    ("RHEL 7.4", "2017-07-31", "3.10"),
    ("RHEL 7.5", "2018-04-10", "3.10"),
    ("RHEL 7.6", "2018-10-30", "3.10"),
    ("RHEL 7.7", "2019-08-06", "3.10"),
    ("RHEL 7.8", "2020-03-31", "3.10"),
    ("RHEL 7.9", "2020-09-29", "3.10"),
    ("RHEL 8.0", "2019-05-07", "4.18"),
    ("RHEL 8.1", "2019-11-05", "4.18"),
    ("RHEL 8.2", "2020-04-28", "4.18"),
    ("RHEL 8.3", "2020-11-03", "4.18"),
    ("RHEL 8.4", "2021-05-18", "4.18"),
    ("RHEL 8.5", "2021-11-09", "4.18"),
    ("RHEL 8.6", "2022-05-10", "4.18"),
    ("RHEL 8.7", "2022-11-08", "4.18"),
    ("RHEL 8.8", "2023-05-16", "4.18"),
    ("RHEL 9.0", "2022-05-17", "5.14"),
    ("RHEL 9.1", "2022-11-15", "5.14"),
    ("RHEL 9.2", "2023-05-09", "5.14"),
    ("RHEL 9.3", "2023-11-07", "5.14"),
    ("RHEL 9.4", "2024-04-30", "5.14"),
    ("RHEL 9.5", "2024-11-12", "5.14"),
    ("RHEL 9.6", "2025-05-13", "5.14"),
    ("RHEL 10.0", "2025-05-20", "6.12"),
]
