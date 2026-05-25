# fs-features

A data pipeline and a growing set of case studies that measure how long it
actually takes to stabilize a Linux filesystem feature.

Site: <https://fs-features.do-not-panic.com/>.

The catalog tracks every major feature merged into XFS, ext4, and btrfs
since around 2008 — when it was first proposed on the mailing list, when
it was discussed at LSFMM, when it landed in Linus's tree, and when it
shipped enabled in SUSE Linux Enterprise and Red Hat Enterprise Linux.
Each row is a number; each case study is the human story behind those
numbers, written by the people who lived through the work.

## What's in here

- A catalog of 55 features across XFS, ext4, and btrfs in
  `data/features_*.json`, with hand-curated provenance for every
  manually-entered field.
- A reproducible Python pipeline that derives merge dates, kernel
  release tags, and Fixes-tag fan-out counts from a local kernel tree
  and emits CSV, JSON, Markdown, PNG plots, and the static HTML site
  under `docs/`.
- An in-depth case study for [LBS (Large Block Sizes)](case_studies/lbs.md):
  the seventeen-year arc from Christoph Lameter's 2007 compound-page RFC
  through Nick Piggin's fsblock, Dave Chinner's 2014/2018 attempts and
  2023 design guidance, Pankaj Raghav's XFS series that landed in v6.12,
  the buffer-head/bdev cache LBS work in v6.15, and the ext4 and btrfs
  follow-ons in 2025. This is the template for everything else.
- A [findings page](https://fs-features.do-not-panic.com/findings.html)
  with the empirical conclusions, including the surprising one that
  LBS-on-XFS had the *fastest* merge-to-enterprise wall-clock of any
  feature in the catalog.

## Contributing a case study

If you maintained, designed, or stabilized a major Linux filesystem
feature, your account of how it actually happened is worth more than the
catalog row. The catalog gives the numbers; only the people who were on
the threads can give the context.

We are especially looking for biographies of features that touched core
mm: DAX, large folios, idmapped mounts, the buffer-head retirement
effort, the iomap conversion, online repair, and the next round of
MM-impact filesystem work. The case study schema is small and the
rendering is automatic — write Markdown, open a pull request, the site
picks it up on the next `make`.

The fastest path:

```bash
git clone https://github.com/mcgrof/fs-features
cd fs-features
cp case_studies/lbs.md case_studies/<your-feature>.md
# edit the YAML frontmatter and the body
make case-studies
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full submission checklist
and the conventions inherited from Linux kernel mailing-list etiquette
(narrative commit messages, atomic commits, Signed-off-by).

## Why bother

The enterprise Linux industry has known for two decades that it takes
about ten years to stabilize a brand-new filesystem. That figure is
whole-filesystem and is too coarse to plan against. The per-feature
number is less well known, lives mostly in maintainers' heads, and gets
told differently every time someone tells it. This project pins the
numbers down with provenance so the conversation can move on to the
interesting questions: which features stalled and why, what changed when
they finally landed, where the bottleneck actually is.

## Running the pipeline

```bash
make             # full pipeline: enrich, analyze, plots, report, case studies
make collect     # not yet split out; enrich pulls from a kernel tree
make enrich      # update merged_date, merged_version, Fixes-tag counts
make analyze     # compute metrics
make plots       # render PNG figures
make report      # build docs/index.html + docs/findings.html
make case-studies  # render docs/case_studies/*.html
make clean       # remove generated outputs
```

The kernel tree path is configurable:

```bash
KERNEL_TREE=/path/to/linux make enrich
```

Default is `~/linux`. Enrichment scans HEAD only (no `--all`) and bounds
the Fixes-tag scan to the seed sha's merge date for speed.

## Project layout

```
data/                 source-of-truth feature catalogs (one JSON per fs)
case_studies/         long-form per-feature biographies (Markdown)
scripts/              data collectors, analyzers, plotters, HTML builders
docs/                 the published site (HTML, PNG, mirrored data)
reports/              generated Markdown summaries (findings.md, analysis.md)
PROMPTS.md            log of prompts that shaped this project
CLAUDE.md             contributor guide (also read by AI assistants)
CONTRIBUTING.md       case-study and pipeline contribution checklist
```

## Adding a feature to the catalog

Append a record to `data/features_<fs>.json` with at least `name`,
`merged_sha`, and `mm_impact`. The pipeline fills in everything else it
can derive from the kernel tree. Manual fields (RFC URL, LSFMM years,
distro enablement) sit alongside the auto-derived ones with explicit
`source:` provenance so re-runs preserve hand-curated context.

For a worked example with multi-RFC history (failed prior attempts),
see the `xfs_lbs` entry in `data/features_xfs.json` — it carries a
`historical_attempts` list and a `first_idea_date` distinct from the
RFC that finally landed.

## License

MIT. See LICENSE.
