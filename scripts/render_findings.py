#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Render reports/findings.md as docs/findings.html using the same dark
Tailwind aesthetic as docs/index.html.

Inline post-processing tags the markdown-emitted elements with Tailwind
classes so we don't need to rewrite the markdown in HTML by hand: the
narrative lives in one source-of-truth file (findings.md) and we just
style it on the way out.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SRC = ROOT / "reports" / "findings.md"
DEFAULT_OUT = ROOT / "docs" / "findings.html"


# Map markdown-emitted tags to Tailwind classes. Each entry pairs a tag
# name with the classes to inject. We splice the classes into the
# opening tag whether markdown emitted attributes (e.g. id="...") or
# not. Closing tags are left alone.
TAG_CLASSES: dict[str, str] = {
    "h1": "text-4xl font-bold mb-6 text-gray-100",
    "h2": (
        "text-2xl font-bold mt-12 mb-4 pb-2 border-b border-gray-700 "
        "text-gray-100"
    ),
    "h3": "text-xl font-semibold mt-8 mb-3 text-cyan-300",
    "h4": "text-lg font-semibold mt-6 mb-2 text-gray-100",
    "p": "text-gray-300 leading-relaxed mb-4",
    "ul": "list-disc ml-6 space-y-1 mb-4 text-gray-300",
    "ol": "list-decimal ml-6 space-y-1 mb-4 text-gray-300",
    "li": "leading-relaxed",
    "code": (
        "px-1.5 py-0.5 rounded bg-gray-900 text-cyan-300 font-mono text-sm"
    ),
    "pre": (
        "bg-gray-900 border border-gray-700 rounded-lg p-4 "
        "overflow-x-auto mb-4"
    ),
    "table": "w-full text-sm border-collapse mb-6",
    "thead": "border-b border-gray-700 text-gray-400",
    "tr": "border-b border-gray-800",
    "th": "text-left py-2 px-3 font-medium",
    "td": "py-2 px-3 text-gray-300 align-top",
    "strong": "font-semibold text-gray-100",
    "em": "italic text-gray-200",
    "a": "text-cyan-400 hover:text-cyan-200 hover:underline",
    "blockquote": (
        "border-l-4 border-cyan-700 pl-4 my-4 text-gray-400 italic"
    ),
    "hr": "border-gray-700 my-8",
}


def _inject_class(tag: str, classes: str, html_in: str) -> str:
    """Add a class= attribute to every opening <tag ...> in html_in.

    The negative-lookahead (?![a-zA-Z0-9]) guards against partial-name
    matches: a rule for "th" would otherwise also hit "thead". If a
    class attribute already exists (e.g. from a markdown extension or
    a prior rewrite), we merge.
    """
    boundary = r"(?![a-zA-Z0-9])"
    # <tag ... class="..."> -> merge
    open_with_class = re.compile(
        rf'<{tag}{boundary}([^>]*?)\sclass="([^"]*)"([^>]*)>'
    )
    html_in = open_with_class.sub(
        lambda m: f'<{tag}{m.group(1)} class="{classes} {m.group(2)}"{m.group(3)}>',
        html_in,
    )
    # <tag ...> (no class)
    open_no_class = re.compile(rf"<{tag}{boundary}(\s[^>]*)?>")

    def fill(m: re.Match[str]) -> str:
        attrs = m.group(1) or ""
        return f'<{tag}{attrs} class="{classes}">'

    html_in = open_no_class.sub(fill, html_in)
    return html_in


def style_html(raw: str) -> str:
    out = raw
    for tag, classes in TAG_CLASSES.items():
        out = _inject_class(tag, classes, out)
    return out


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>fs-features: Findings</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {{ background: #0f172a; }}
    .card {{
      background: linear-gradient(145deg, #1e293b, #1a2332);
      border: 1px solid #334155;
    }}
    .prose-card h2:first-child {{ margin-top: 0; }}
    a code {{ color: inherit; }}
  </style>
</head>
<body class="min-h-screen text-gray-100">
  <div class="max-w-4xl mx-auto px-6 py-12">

    <nav class="mb-8 flex items-center justify-between text-sm">
      <a href="index.html" class="text-gray-400 hover:text-gray-200">
        &larr; back to fs-features
      </a>
      <div class="flex gap-3">
        <a href="features_all.csv"
           class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded font-medium">
          CSV
        </a>
        <a href="analysis.json"
           class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded font-medium">
          JSON
        </a>
        <a href="findings.md"
           class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded font-medium">
          .md
        </a>
      </div>
    </nav>

    <article class="card rounded-xl p-8 md:p-12 prose-card">
{body}
    </article>

    <footer class="text-center text-gray-600 text-sm mt-12 pt-8 border-t border-gray-800">
      <p class="mb-2">
        <a href="index.html" class="hover:text-gray-400">report</a>
        <span class="mx-2">&middot;</span>
        <a href="https://github.com/mcgrof/fs-features" class="hover:text-gray-400">source</a>
      </p>
      <p>MIT License &middot; Luis Chamberlain and contributors</p>
    </footer>
  </div>
</body>
</html>
"""


def render(src: Path, out: Path) -> None:
    md_text = src.read_text(encoding="utf-8")
    body_html = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "attr_list", "toc"],
        output_format="html5",
    )
    styled = style_html(body_html)
    page = PAGE_TEMPLATE.format(body=styled)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=DEFAULT_SRC)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    render(args.src, args.out)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
