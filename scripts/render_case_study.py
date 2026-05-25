#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Render a single case_studies/<slug>.md into docs/case_studies/<slug>.html
with the same dark Tailwind aesthetic as the rest of the site.

The .md source carries a YAML frontmatter block bracketed by '---' that
exposes the metadata the listing page uses (slug, title, subtitle,
filesystems, mm_impact, dates, authors, status). The Markdown body is
free-form narrative and may contain tables, code, and inline HTML.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "case_studies"
OUT_DIR = ROOT / "docs" / "case_studies"


FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)


def parse_case_study(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER.match(text)
    if not m:
        raise ValueError(f"{path}: missing YAML frontmatter")
    meta = yaml.safe_load(m.group(1)) or {}
    body_md = m.group(2)
    return meta, body_md


# Tailwind class injection table. The negative-lookahead guard prevents
# rules for short tag names from matching longer ones (e.g. "th" vs
# "thead"). Same approach as scripts/render_findings.py.
TAG_CLASSES: dict[str, str] = {
    "h1": "text-4xl font-bold mb-2 text-gray-100",
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
        "bg-gray-900 border border-gray-700 rounded-lg p-4 overflow-x-auto "
        "mb-4"
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
    "img": (
        "block w-full h-auto rounded-lg border border-gray-700 my-6 "
        "shadow-lg"
    ),
}


def _inject_class(tag: str, classes: str, html_in: str) -> str:
    boundary = r"(?![a-zA-Z0-9])"
    open_with_class = re.compile(
        rf'<{tag}{boundary}([^>]*?)\sclass="([^"]*)"([^>]*)>'
    )
    html_in = open_with_class.sub(
        lambda m: f'<{tag}{m.group(1)} class="{classes} {m.group(2)}"{m.group(3)}>',
        html_in,
    )
    open_no_class = re.compile(rf"<{tag}{boundary}(\s[^>]*)?>")

    def fill(m: re.Match[str]) -> str:
        attrs = m.group(1) or ""
        return f'<{tag}{attrs} class="{classes}">'

    return open_no_class.sub(fill, html_in)


def style_html(raw: str) -> str:
    out = raw
    for tag, classes in TAG_CLASSES.items():
        out = _inject_class(tag, classes, out)
    return out


def _meta_chip(label: str, value: str, color: str = "gray") -> str:
    palette = {
        "gray": "bg-gray-800 text-gray-300",
        "cyan": "bg-cyan-900 text-cyan-300",
        "purple": "bg-purple-900 text-purple-300",
        "emerald": "bg-emerald-900 text-emerald-300",
        "amber": "bg-amber-900 text-amber-300",
        "rose": "bg-rose-900 text-rose-300",
    }
    cls = palette.get(color, palette["gray"])
    return (
        f'<span class="inline-flex items-center gap-1 {cls} px-2 py-1 '
        f'rounded text-xs"><span class="text-gray-500">{label}</span>'
        f'<span class="font-semibold">{value}</span></span>'
    )


FS_COLOR = {"xfs": "cyan", "ext4": "purple", "btrfs": "emerald"}
MM_COLOR = {"none": "gray", "minor": "amber", "major": "rose"}


def header_block(meta: dict) -> str:
    title = meta.get("title", meta.get("slug", "Case study"))
    subtitle = meta.get("subtitle", "")
    chips = []
    for fs in meta.get("filesystems", []):
        chips.append(_meta_chip("fs", fs, FS_COLOR.get(fs, "gray")))
    mm = meta.get("mm_impact")
    if mm:
        chips.append(_meta_chip("mm-impact", mm, MM_COLOR.get(mm, "gray")))
    status = meta.get("status")
    if status:
        chips.append(_meta_chip("status", status, "emerald"))
    if meta.get("first_idea_date"):
        chips.append(_meta_chip("first idea", meta["first_idea_date"]))
    if meta.get("first_landed_date"):
        chips.append(
            _meta_chip(
                "merged",
                f"{meta['first_landed_date']} ({meta.get('first_landed_version', '?')})",
            )
        )
    last = meta.get("last_updated")
    if last:
        chips.append(_meta_chip("updated", last))
    chip_html = "\n            ".join(chips)

    authors = meta.get("authors", [])
    author_html = ""
    if authors:
        items = "\n              ".join(
            f'<li class="text-sm text-gray-400">{a}</li>' for a in authors
        )
        author_html = f"""
        <div class="mt-6">
          <div class="text-xs uppercase tracking-wide text-gray-500 mb-2">
            authors / contributors
          </div>
          <ul class="list-disc ml-6 space-y-1">
              {items}
          </ul>
        </div>
        """

    maintainers = meta.get("maintainers", "")
    maint_html = ""
    if maintainers:
        maint_html = (
            '<div class="mt-3 text-sm text-gray-400">'
            f'<span class="text-gray-500">maintainers:</span> '
            f'<span class="text-gray-300">{maintainers}</span></div>'
        )

    return f"""
    <header class="mb-10 pb-8 border-b border-gray-700">
      <p class="text-xs uppercase tracking-wide text-cyan-400 mb-2">
        Case study
      </p>
      <h1 class="text-4xl font-bold text-gray-100 mb-2">{title}</h1>
      <p class="text-lg text-gray-400">{subtitle}</p>
      <div class="mt-6 flex flex-wrap gap-2">
            {chip_html}
      </div>
      {maint_html}
      {author_html}
    </header>
    """


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} -- fs-features case study</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {{ background: #0f172a; }}
    .card {{
      background: linear-gradient(145deg, #1e293b, #1a2332);
      border: 1px solid #334155;
    }}
    a code {{ color: inherit; }}
    /* a markdown image followed only by the implicit alt text reads
       as a figure caption */
    p > img + br + em,
    p:has(> img) > em {{
      display: block;
      color: #94a3b8;
      font-size: 0.875rem;
      text-align: center;
      margin-top: -0.75rem;
    }}
  </style>
</head>
<body class="min-h-screen text-gray-100">
  <div class="max-w-4xl mx-auto px-6 py-12">

    <nav class="mb-8 flex items-center justify-between text-sm">
      <div class="flex gap-4">
        <a href="../index.html" class="text-gray-400 hover:text-gray-200">
          &larr; fs-features
        </a>
        <a href="index.html" class="text-gray-400 hover:text-gray-200">
          case studies index
        </a>
      </div>
      <div class="flex gap-3">
        <a href="{slug}.md"
           class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded font-medium">
          .md source
        </a>
        <a href="https://github.com/mcgrof/fs-features/edit/master/case_studies/{slug}.md"
           class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded font-medium">
          edit on GitHub
        </a>
      </div>
    </nav>

    <article class="card rounded-xl p-8 md:p-12">
      {header}
{body}
    </article>

    <footer class="text-center text-gray-600 text-sm mt-12 pt-8 border-t border-gray-800">
      <p class="mb-2">
        <a href="../index.html" class="hover:text-gray-400">fs-features</a>
        <span class="mx-2">&middot;</span>
        <a href="index.html" class="hover:text-gray-400">case studies</a>
        <span class="mx-2">&middot;</span>
        <a href="https://github.com/mcgrof/fs-features" class="hover:text-gray-400">source</a>
      </p>
      <p>MIT License &middot; Luis Chamberlain and contributors</p>
    </footer>
  </div>
</body>
</html>
"""


def render(src: Path, out: Path) -> dict:
    meta, body_md = parse_case_study(src)
    slug = meta.get("slug") or src.stem
    meta.setdefault("slug", slug)
    body_html = markdown.markdown(
        body_md,
        extensions=["tables", "fenced_code", "attr_list", "toc"],
        output_format="html5",
    )
    body_styled = style_html(body_html)
    page = PAGE_TEMPLATE.format(
        title=meta.get("title", slug),
        slug=slug,
        header=header_block(meta),
        body=body_styled,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    # Also mirror the source .md alongside the html for direct download
    (out.parent / f"{slug}.md").write_text(
        src.read_text(encoding="utf-8"), encoding="utf-8"
    )
    return meta


def render_all(src_dir: Path = SRC_DIR, out_dir: Path = OUT_DIR) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    metas = []
    for src in sorted(src_dir.glob("*.md")):
        out = out_dir / f"{src.stem}.html"
        meta = render(src, out)
        metas.append(meta)
        print(f"wrote {out}")
    return metas


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "sources",
        nargs="*",
        type=Path,
        help="Specific .md files to render (defaults to all in case_studies/)",
    )
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args(argv)

    if args.sources:
        for src in args.sources:
            out = args.out_dir / f"{src.stem}.html"
            render(src, out)
            print(f"wrote {out}")
    else:
        render_all(out_dir=args.out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
