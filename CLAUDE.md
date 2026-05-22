# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

## What this project is

A reusable data pipeline that catalogs Linux filesystem features (XFS, ext4,
btrfs) and the wall-clock time each took to traverse the stabilization
lifecycle: first RFC posting, merge, LSFMM exposure, enterprise distro
enablement. The pipeline emits CSV, JSON, PNG plots, and a static HTML
report styled after the knlp.io aesthetic. Re-runnable: new features and
updated stabilization data can be folded back in without redoing prior work.

The motivating question: how much wall-clock did LBS (Large Block Sizes) save
versus the historical baseline, and is that delta plausibly attributable to
kdevops + AI-assisted testing? Secondary questions: which features required
core MM changes (the harder class LBS belongs to); after LBS landed in XFS,
how long did ext4 and btrfs take to adopt it; do Fixes-tag fan-outs correlate
with stabilization time.

## Git commit practices

### Structure

Small atomic commits. One logical change per commit. Each commit builds.
Run `scripts/fix_whitespace_issues.py` on all touched files before committing.

### Commit message format

```
path/file.ext: brief description of change

Detailed explanation of what was changed and why. Include technical
context concisely as prose, not as bullet lists.

Generated-by: Claude AI
Signed-off-by: Luis Chamberlain <mcgrof@do-not-panic.com>
```

Subject line and body wrap at 70 characters. No exceptions, regardless of
commit size.

Never use `Co-Authored-By:` or `Generated with Claude Code` trailers. The
exact required trailers are `Generated-by: Claude AI` and
`Signed-off-by: Luis Chamberlain <mcgrof@do-not-panic.com>`.

Write commit messages as terse prose. No shopping-list bullets unless a
genuine enumeration aids clarity. Explain the why, not just the what.

## Code style

### Python

`black` formats all Python. PEP 8 is enforced by black. No manual
formatting. Never apply `black` to `.config`, defconfig, or CSV files.

Run `python3 scripts/fix_whitespace_issues.py` on any text file you
touched before committing. Strips trailing whitespace, ensures a single
terminating newline, caps consecutive blank lines at two.

### Markdown and documentation

Write documentation as technical prose, not an outline. State plainly
what the document is for in the first paragraph. Use bullets only when
they genuinely improve readability. Use a short table of contents for
long documents.

Do not write filler like "this document stands on its own" or hedged
commentary inside the doc. Do not apologize for unclear structure --
fix the structure instead. Avoid robotic imperatives ("Use X. Do Y.")
when natural phrasing reads better.

## Avoid silly language

The word "comprehensive" is banned. It says nothing. Replace with
specifics: "covers all features merged through Linux 6.12", "tracks
RFC through enterprise enablement", etc.

Avoid hype adjectives ("beautiful", "powerful", "robust") in committed
prose. Stick to what the work actually does and measures.

## Project layout

```
fs-features/
  data/        # source-of-truth structured data (JSON, CSV)
                # one file per fs: features_xfs.json, features_ext4.json, etc.
                # aggregated outputs: features_all.csv, analysis.json
  scripts/     # data collectors, mergers, analyzers, plotters, html builders
  docs/        # the published HTML report and supporting assets
  reports/     # generated text/markdown analyses
```

`data/` files are hand-curated where automation cannot reach (RFC dates,
LSFMM coverage, distro enablement) and machine-extracted where it can
(merge dates, SHAs, Fixes-tag counts). Hand-curated fields are marked with
`source: "manual"` or `source: "lwn:<url>"` so re-runs preserve provenance.

## Pipeline conventions

The pipeline runs end-to-end via `make` at the project root:

```bash
make collect   # extract per-fs features from the local kernel tree
make enrich    # join manually-curated RFC/LSFMM/distro fields
make analyze   # compute averages, deltas, MM-impact comparisons
make plots     # render PNG figures
make report    # build docs/index.html and per-fs feature pages
make           # all of the above in order
```

Each stage writes to a deterministic output location and resumes by
detecting up-to-date outputs. The kernel tree path is configurable via
`KERNEL_TREE=/path/to/linux make collect`; default is `~/linux`.

## Adding a feature

When you discover a new feature to track:

1. Open `data/features_<fs>.json` and append a feature record. Include
   at minimum: `name`, `short_name`, `merged_sha` (will trigger automatic
   merged-date and version lookup), and `mm_impact` ("none", "minor",
   "major").
2. Add manual fields where known: `rfc_date`, `rfc_url`,
   `lsfmm_years`, `suse_first_enabled`, `rhel_first_enabled`.
3. Run `make` to regenerate the report. The pipeline fills in everything
   that can be derived from the kernel tree automatically.

## Cross-agent access

Some automation looks for agent-specific instruction files. Keep
`CODEX.md` as a symlink to `CLAUDE.md` if other tools later need it.

## Memory

I want you to remember most of our conversations about this project.
