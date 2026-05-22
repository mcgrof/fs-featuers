#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Enrich per-filesystem feature JSON with data derived from the kernel
tree: merged_date, merged_version, fixes_count, fixes_last_date,
fixes_window_years. Idempotent -- existing manually-set fields are
preserved when KEEP_MANUAL is set; otherwise auto-derivable fields are
overwritten with the latest kernel-tree truth.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(ROOT / "scripts"))
from kernel_git import enrich, DEFAULT_TREE  # noqa: E402


def enrich_file(path: Path, tree: Path) -> tuple[int, int]:
    """Enrich features in `path` in place. Returns (updated, total)."""
    with open(path) as fp:
        data = json.load(fp)
    features = data.get("features", [])
    updated = 0
    for feat in features:
        before = json.dumps(feat, sort_keys=True)
        enrich(tree, feat)
        if json.dumps(feat, sort_keys=True) != before:
            updated += 1
    with open(path, "w") as fp:
        json.dump(data, fp, indent=2)
        fp.write("\n")
    return updated, len(features)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tree",
        type=Path,
        default=DEFAULT_TREE,
        help=f"Kernel git tree (default: {DEFAULT_TREE})",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=list((ROOT / "data").glob("features_*.json")),
        help="Per-filesystem JSON files to enrich",
    )
    args = parser.parse_args(argv)

    if not args.tree.exists():
        print(f"error: kernel tree not found at {args.tree}", file=sys.stderr)
        return 1

    for path in args.paths:
        if not path.exists():
            print(f"skip: {path} (not found)", file=sys.stderr)
            continue
        updated, total = enrich_file(path, args.tree)
        print(f"{path.name}: {updated}/{total} features enriched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
