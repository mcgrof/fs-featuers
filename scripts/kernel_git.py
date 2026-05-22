#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Kernel-tree introspection. Given a Feature record with merged_sha set,
derives merged_date, merged_version (via the first release tag containing
the commit), and the count of subsequent commits that name the SHA in a
Fixes: trailer.

The kernel tree path defaults to ~/linux but is configurable through the
KERNEL_TREE environment variable or the --tree CLI flag.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_TREE = Path(os.environ.get("KERNEL_TREE", str(Path.home() / "linux")))


def git(tree: Path, *args: str, allow_fail: bool = False) -> str:
    cmd = ["git", "-C", str(tree)] + list(args)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=not allow_fail,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {exc.stderr.strip()}"
        ) from exc
    if allow_fail and result.returncode != 0:
        return ""
    return result.stdout.strip()


def commit_date(tree: Path, sha: str) -> str | None:
    """Return committer date (ISO YYYY-MM-DD) for sha, or None."""
    out = git(tree, "log", "-1", "--format=%cI", sha, allow_fail=True)
    if not out:
        return None
    # Trim to date only.
    return out.split("T", 1)[0]


def commit_version(tree: Path, sha: str) -> str | None:
    """Return the first release tag (vX.Y) that contains sha.

    Uses `git describe --contains --match v* sha` which returns the tag
    name in form 'vX.Y[-rcN]~..'. We slice off everything from '~'.
    Returns None if the commit is not in any release tag yet.
    """
    out = git(tree, "describe", "--contains", "--match", "v*", sha, allow_fail=True)
    if not out:
        return None
    name = out.split("~", 1)[0]
    name = name.split("^", 1)[0]
    return name


def fixes_referencing(
    tree: Path, sha: str, since: str | None = None
) -> tuple[int, str | None]:
    """Count later commits whose body contains `Fixes: <abbrev>` matching sha.

    Match is anchored on the abbreviated sha that `git show` produces with
    default settings. We use the first 12 hex chars (kernel convention is
    12-char abbreviated Fixes). Returns (count, latest_date_iso).

    If `since` is provided (ISO date), restricts to commits after that.
    """
    if not sha or len(sha) < 12:
        return (0, None)
    short = sha[:12]
    args = [
        "log",
        "--all",
        f"--grep=Fixes:[ \\t]\\+{short}",
        "-E",
        "--format=%cI %H",
    ]
    if since:
        args.append(f"--since={since}")
    out = git(tree, *args, allow_fail=True)
    if not out:
        return (0, None)
    dates = []
    for line in out.splitlines():
        date_part = line.split(" ", 1)[0].split("T", 1)[0]
        dates.append(date_part)
    if not dates:
        return (0, None)
    dates.sort()
    return (len(dates), dates[-1])


def fixes_referencing_many(
    tree: Path, shas: list[str]
) -> tuple[int, str | None]:
    """Aggregate fixes count across a list of seed shas (for features that
    landed across multiple commits). De-duplicates by hits' own SHA."""
    seen: dict[str, str] = {}
    for seed in shas:
        if not seed or len(seed) < 12:
            continue
        short = seed[:12]
        out = git(
            tree,
            "log",
            "--all",
            f"--grep=Fixes:[ \\t]\\+{short}",
            "-E",
            "--format=%H %cI",
            allow_fail=True,
        )
        for line in out.splitlines():
            parts = line.strip().split(" ", 1)
            if len(parts) != 2:
                continue
            commit_sha, iso = parts
            seen[commit_sha] = iso.split("T", 1)[0]
    if not seen:
        return (0, None)
    dates = sorted(seen.values())
    return (len(seen), dates[-1])


def enrich(tree: Path, feature: dict) -> dict:
    """Fill in merged_date, merged_version, fixes_count, fixes_last_date
    when merged_sha (or merged_shas list) is present and the kernel tree
    has the commit."""
    if not tree.exists():
        return feature

    sha = feature.get("merged_sha")
    extra = feature.get("merged_shas") or []
    seeds = [sha] + extra if sha else list(extra)

    if sha:
        if not feature.get("merged_date"):
            d = commit_date(tree, sha)
            if d:
                feature["merged_date"] = d
        if not feature.get("merged_version"):
            v = commit_version(tree, sha)
            if v:
                feature["merged_version"] = v

    if seeds:
        n, last = fixes_referencing_many(tree, seeds)
        feature["fixes_count"] = n
        feature["fixes_last_date"] = last
        merged_date = feature.get("merged_date")
        if last and merged_date:
            from datetime import date

            def parse(s: str) -> date:
                y, m, d = s.split("-")
                return date(int(y), int(m), int(d))

            try:
                delta = (parse(last) - parse(merged_date)).days
                feature["fixes_window_years"] = round(delta / 365.25, 2)
            except ValueError:
                pass
    return feature


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tree",
        type=Path,
        default=DEFAULT_TREE,
        help=f"Kernel git tree (default: {DEFAULT_TREE})",
    )
    parser.add_argument(
        "sha",
        nargs="?",
        help="Commit SHA to introspect. If omitted, prints the resolved tree.",
    )
    args = parser.parse_args(argv)
    tree = args.tree

    if not args.sha:
        print(f"Kernel tree: {tree}")
        if not tree.exists():
            print("(does not exist)", file=sys.stderr)
            return 1
        head = git(tree, "rev-parse", "HEAD", allow_fail=True)
        desc = git(tree, "describe", "--abbrev=0", "--tags", allow_fail=True)
        print(f"HEAD: {head}")
        print(f"Nearest tag: {desc}")
        return 0

    sha = args.sha
    print(f"sha:     {sha}")
    print(f"date:    {commit_date(tree, sha)}")
    print(f"version: {commit_version(tree, sha)}")
    n, last = fixes_referencing(tree, sha)
    print(f"fixes:   {n} (latest {last})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
