#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Build docs/case_studies/index.html: a landing page that lists every
case study with its title, subtitle, dates, and metadata chips. Also
exposes a "contribute" pane explaining how to submit a new case study.

Reads metadata from the YAML frontmatter of every case_studies/*.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "case_studies"
OUT = ROOT / "docs" / "case_studies" / "index.html"

sys.path.insert(0, str(ROOT / "scripts"))
from render_case_study import (  # noqa: E402
    FS_COLOR,
    MM_COLOR,
    _meta_chip,
    parse_case_study,
)


CARD_TEMPLATE = """
        <a href="{slug}.html" class="card rounded-lg p-6 block">
          <div class="flex items-start justify-between mb-2">
            <div>
              <h3 class="text-xl font-semibold text-cyan-300">{title}</h3>
              <p class="text-sm text-gray-400 mt-1">{subtitle}</p>
            </div>
          </div>
          <div class="mt-4 flex flex-wrap gap-2">
            {chips}
          </div>
        </a>
"""


def card_for(meta: dict, slug: str) -> str:
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
        chips.append(_meta_chip("merged", meta["first_landed_date"]))
    return CARD_TEMPLATE.format(
        slug=meta.get("slug", slug),
        title=meta.get("title", slug),
        subtitle=meta.get("subtitle", ""),
        chips="\n            ".join(chips),
    )


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Case studies -- fs-features</title>
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
  </style>
</head>
<body class="min-h-screen text-gray-100">
  <div class="max-w-5xl mx-auto px-6 py-12">

    <nav class="mb-8 text-sm">
      <a href="../index.html" class="text-gray-400 hover:text-gray-200">
        &larr; fs-features
      </a>
    </nav>

    <header class="mb-10">
      <h1 class="text-4xl font-bold mb-3">Case studies</h1>
      <p class="text-lg text-gray-400 max-w-3xl">
        Deep biographies of individual Linux filesystem features: first
        idea, mailing-list discussions, LSFMM topics, design pivots,
        merged implementation, and post-merge stabilization. One page per
        feature, hand-written by people who lived through the work.
      </p>
    </header>

    <section class="mb-14">
      <h2 class="text-2xl font-bold mb-4 text-gray-100">Published</h2>
      <div class="grid md:grid-cols-2 gap-4">
{cards}
      </div>
    </section>

    <section class="mb-14">
      <div class="card rounded-xl p-8">
        <h2 class="text-2xl font-bold mb-3 text-gray-100">
          Contribute a case study
        </h2>
        <p class="text-gray-300 mb-3">
          If you maintained, designed, or stabilized a major Linux
          filesystem feature, your account of how it actually happened is
          worth more than the catalog row. Case studies in this site are
          authored by the people who lived through the work; we cross-link
          them from the per-feature row in the main grid so readers find
          them where they would naturally look.
        </p>
        <p class="text-gray-300 mb-3">
          The shape of a case study is:
        </p>
        <ol class="list-decimal ml-6 space-y-1 text-gray-300 mb-4">
          <li>YAML frontmatter with slug, title, filesystems, mm-impact,
              first-idea date, merged date, maintainers, authors.</li>
          <li>A short "what and why" intro that names the unit of work.</li>
          <li>A timeline-of-attempts table when the feature has more than
              one RFC, with lore.kernel.org or LWN links.</li>
          <li>A "what was different about the attempt that landed" section
              naming the prerequisites and the inflection point.</li>
          <li>A per-phase narrative of how the feature actually merged,
              with commit SHAs.</li>
          <li>A small numbers table comparing the catalog metrics.</li>
          <li>A short reflection on what the feature suggests about how
              Linux fs features mature.</li>
          <li>A references section: kernelnewbies pages, LWN articles,
              key lore threads, and any companion tooling (e.g. kdevops).</li>
        </ol>
        <p class="text-gray-300 mb-3">
          Open a pull request adding
          <code class="px-1.5 py-0.5 rounded bg-gray-900 text-cyan-300 font-mono text-sm">case_studies/&lt;slug&gt;.md</code>.
          Use
          <a href="lbs.md" class="text-cyan-400 hover:underline">lbs.md</a>
          as the template; the schema and Tailwind layout are picked up
          automatically by
          <code class="px-1.5 py-0.5 rounded bg-gray-900 text-cyan-300 font-mono text-sm">scripts/render_case_study.py</code>
          on the next
          <code class="px-1.5 py-0.5 rounded bg-gray-900 text-cyan-300 font-mono text-sm">make</code>.
        </p>
        <p class="text-gray-300">
          See
          <a href="../../CONTRIBUTING.md" class="text-cyan-400 hover:underline">CONTRIBUTING.md</a>
          for the submission checklist and the conventions inherited from
          Linux kernel mailing-list etiquette (Signed-off-by, narrative
          commit messages, atomic commits).
        </p>
      </div>
    </section>

    <footer class="text-center text-gray-600 text-sm mt-12 pt-8 border-t border-gray-800">
      <p class="mb-2">
        <a href="../index.html" class="hover:text-gray-400">fs-features</a>
        <span class="mx-2">&middot;</span>
        <a href="../findings.html" class="hover:text-gray-400">findings</a>
        <span class="mx-2">&middot;</span>
        <a href="https://github.com/mcgrof/fs-features" class="hover:text-gray-400">source</a>
      </p>
      <p>MIT License &middot; Luis Chamberlain and contributors</p>
    </footer>
  </div>
</body>
</html>
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)

    metas = []
    for src in sorted(SRC_DIR.glob("*.md")):
        meta, _ = parse_case_study(src)
        meta.setdefault("slug", src.stem)
        metas.append(meta)

    cards = "\n".join(card_for(m, m["slug"]) for m in metas)
    page = PAGE_TEMPLATE.format(cards=cards)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(page, encoding="utf-8")
    print(f"wrote {args.out} ({len(metas)} case studies)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
