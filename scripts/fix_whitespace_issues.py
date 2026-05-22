#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Whitespace fixer for fs-features. Strips trailing whitespace, ensures a
single terminating newline, caps consecutive blank lines at two.
"""

import argparse
import sys
from pathlib import Path


SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "venv",
    "build",
    "dist",
}
SKIP_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".ico", ".woff", ".woff2"}


def fix_text(text: str) -> tuple[str, int]:
    """Return (cleaned_text, fixes_applied)."""
    fixes = 0
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        stripped = line.rstrip()
        if stripped != line:
            fixes += 1
        cleaned.append(stripped)

    # cap consecutive blank lines at 2
    out = []
    blank_run = 0
    for line in cleaned:
        if line == "":
            blank_run += 1
            if blank_run <= 2:
                out.append(line)
            else:
                fixes += 1
        else:
            blank_run = 0
            out.append(line)

    # strip trailing blank lines and add a single newline
    while out and out[-1] == "":
        out.pop()
        fixes += 1
    result = "\n".join(out) + "\n"
    if result != text:
        fixes = max(fixes, 1)
    return result, fixes


def process_file(path: Path) -> int:
    try:
        with open(path, "rb") as fp:
            raw = fp.read()
    except OSError:
        return 0
    if b"\0" in raw:
        return 0
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return 0
    cleaned, fixes = fix_text(text)
    if cleaned != text:
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(cleaned)
        return fixes
    return 0


def iter_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_EXTS:
            continue
        yield path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Files or directories to fix. Defaults to current directory.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report files needing fixes but do not modify them.",
    )
    args = parser.parse_args(argv)

    total_fixes = 0
    files_fixed = 0
    for target in args.paths:
        root = Path(target).resolve()
        if root.is_file():
            files = [root]
        else:
            files = list(iter_files(root))
        for path in files:
            if args.check:
                with open(path, "rb") as fp:
                    raw = fp.read()
                if b"\0" in raw:
                    continue
                try:
                    text = raw.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                cleaned, fixes = fix_text(text)
                if cleaned != text:
                    print(path)
                    total_fixes += fixes
                    files_fixed += 1
            else:
                fixes = process_file(path)
                if fixes:
                    print(f"fixed: {path} ({fixes} change{'s' if fixes != 1 else ''})")
                    total_fixes += fixes
                    files_fixed += 1
    if args.check and files_fixed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
