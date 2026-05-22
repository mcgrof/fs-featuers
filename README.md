# fs-features

A data pipeline and report that measures how long it takes to stabilize a
Linux filesystem feature. The lifecycle tracked: first RFC posting on
lore.kernel.org -> merged into Linus's tree -> LSFMM exposure -> shipped as
enabled in SUSE Linux Enterprise and Red Hat Enterprise Linux.

The motivating question is how much wall-clock LBS (Large Block Sizes) saved
versus the historical baseline, and whether the delta is plausibly attributable
to kdevops plus AI-assisted testing. The pipeline also catalogs which features
required core memory-management changes (the class LBS belongs to), how
quickly LBS spread from XFS to ext4 and btrfs once it landed, and whether
Fixes-tag fan-outs correlate with stabilization time.

## Why

XFS stable maintenance and enterprise Linux distribution work has anecdotally
fixed the figure of "ten years to stabilize a new filesystem" as a rule of
thumb. That figure is whole-filesystem. The per-feature number is less well
known. We need data to talk about it concretely, and we need the data to be
re-runnable as new features land.

## Output

The published report lives at `docs/index.html`. It is a single static page,
no JavaScript framework, that loads Tailwind via CDN and renders the feature
grid, derived metrics, and embedded PNG plots. CSV/JSON copies of the
underlying data live in `data/`.

## Running the pipeline

```bash
make             # all stages
make collect     # per-fs feature extraction from kernel tree
make enrich      # join manual RFC/LSFMM/distro data
make analyze     # compute metrics
make plots       # render PNG figures
make report      # build docs/index.html
```

The kernel tree path is configurable. Default is `~/linux`:

```bash
KERNEL_TREE=/path/to/linux make collect
```

## Layout

```
data/        source-of-truth JSON per filesystem, plus aggregated CSV
scripts/     Python collectors, analyzers, plotters, HTML builder
docs/        published HTML report and supporting assets
reports/     generated text summaries (markdown)
PROMPTS.md   log of prompts that shaped this project
CLAUDE.md    contributor guide (also read by AI assistants)
```

## Adding a feature

Append a record to `data/features_<fs>.json` with at least `name`,
`merged_sha`, and `mm_impact`. The pipeline fills in everything else it can
derive automatically from the kernel tree. Manual fields (RFC URL, LSFMM
years, distro enablement) sit alongside the auto-derived ones with explicit
`source:` provenance.

## License

MIT. See LICENSE.
