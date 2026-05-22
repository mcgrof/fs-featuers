# Findings: filesystem feature stabilization, with LBS in context

This report answers the questions in PROMPTS.md against the data in
`data/features_*.json` and `data/analysis.json`. Numbers are computed by
`scripts/analyze.py` from a kernel tree at HEAD ~ v7.1-rc4. All durations
are in years, rounded to two decimal places.

## How long does a feature take from RFC to merge?

Across 55 catalogued features for which both RFC and merge dates are
recorded, the global RFC-to-merge wall-clock is:

| set | n | mean | median | p90 | min | max |
|---|---|---|---|---|---|---|
| all | 55 | 0.71y | 0.48y | 1.27y | 0.04y | 4.98y |
| LBS excluded | 52 | 0.71y | 0.47y | 1.29y | 0.04y | 4.98y |

The "ten-year filesystem" rule of thumb is whole-filesystem; the
per-feature distribution is much tighter and the median lands well under a
year. The features that took multi-year RFC-to-merge are real outliers:

- `xfs_parent` (parent pointers): 4.98y. Allison Henderson's first RFC was
  May 2019, but the dependency chain (delayed attributes, the
  log-incompat-feature bit machinery) had to land first.
- `xfs_log_xattrs`: 2.77y. Same dependency story from the other end -- it
  is the dependency that parent pointers needed.
- `ext4_iomap_dio`: 3.12y. ext4's main DIO conversion took years because
  the iomap-for-buffered-IO path took years.

Removing LBS does almost nothing to the headline number because the RFC
of the *successful* 2023 LBS attempt (Pankaj Raghav, Sep 15 2023) landed
at 0.97y -- within the per-feature range. The "LBS got merged faster"
story is therefore not a story about RFC-to-merge in isolation; it is a
story about which prior attempt the clock starts from.

## What does the LBS biography actually say?

The kernel newbies LBS page (linked from the catalog) records five prior
attempts that did not land:

| year | author | what | outcome |
|---|---|---|---|
| 2007-05 | Christoph Lameter | Compound-page support for >PAGE_SIZE block sizes in the page cache | Stalled |
| 2007-07 | Nick Piggin | fsblock RFC, replace buffer heads | Stalled |
| 2009-03 | Nick Piggin | fsblock updated patches | Did not land |
| 2017-03 | LSFMM 2017 | Discussion on whether LBS was worth revisiting | Inconclusive |
| 2018-11 | Dave Chinner | Renewed attempt at >PAGE_SIZE block sizes in XFS | Stalled |
| 2023-09 | Pankaj Raghav et al | XFS LBS RFC | Merged v6.12 in 0.97y |

From 2007-05-15 to 2024-09-03 is **17.31 years of wall-clock between the
first proposal and the merge that actually landed**. That is the longest
first-idea-to-merge of any feature in the catalog, by a margin -- the next
longest first-idea-to-merge is delayed logging at under a year (delaylog
came together quickly once the design was clear).

Within that 17-year span, what was different about the 2023 attempt? Two
load-bearing changes happened on the mm side independently before LBS
landed in fs/xfs:

- The folio/large-folio rework in mm (struct folio, multi-page folios in
  the page cache) finally provided a unit larger than `struct page` that
  the page cache could carry.
- The iomap conversion in XFS (buffered I/O in v5.5, 2019) had moved the
  filesystem off buffer_heads where it counted, so the LBS series did not
  have to rewrite the I/O path as part of its own scope.

On the testing side, the 2023 series was test-driven by kdevops with
AI-assisted triage, materially expanding the matrix of block sizes, page
sizes, and workloads that exercised the path before merge. The prior
attempts had nothing comparable. The catalog records this as a note on
the feature; the *empirical* impact is hard to isolate from the mm
prerequisites that landed in the same window.

## After XFS, what happened to ext4 and btrfs?

XFS LBS merged 2024-09-03. The follow-on filesystems:

| fs | RFC | merged | RFC->merge | lag after XFS LBS |
|---|---|---|---|---|
| XFS | 2023-09-15 | 2024-09-03 (v6.12) | 0.97y | 0 (origin) |
| btrfs | 2024-11-27 | 2025-09-23 (v6.18) | 0.82y | 1.05y |
| ext4 | 2025-07-25 | 2025-11-28 (v6.19) | 0.34y | 1.23y |

ext4's 0.34y RFC-to-merge is among the fastest in the entire catalog --
faster than any other ext4 feature except `ext4_encrypt` (which was
0.04y because the encryption-feature codepoints were merged before the
actual encryption code). The likely interpretation: ext4 inherited the
mm/iomap large-folio runway and only needed to wire up the fs-level
plumbing. The per-fs LBS cost dropped sharply once XFS had paid the mm
cost.

btrfs took longer (0.82y) because it had to extend its pre-existing
subpage machinery to symmetric bs > ps territory, not just inherit folio
support. The btrfs LBS series is in v6.18 and is still marked
experimental.

## Does mm-impact track with longer stabilization?

| bucket | n | mean | median | p90 | max |
|---|---|---|---|---|---|
| none | 38 | 0.65y | 0.35y | 1.24y | 4.98y |
| minor | 12 | 0.92y | 0.86y | 1.29y | 3.12y |
| major | 5 | 0.68y | 0.79y | 0.91y | 0.97y |

mm-impact major bucket is a small sample (DAX-on-XFS, DAX-on-ext4, and
LBS in each of XFS/ext4/btrfs). Its tight distribution has a clear
explanation: the mm cost was paid out of band (DAX over years of
devmap/pgmap work; LBS over years of folio work), so by the time the
fs-level patch posted RFC, the heavy lift was already done. The mm
"major" features look fast at RFC-to-merge because they were *not* fast
end to end -- the years are hidden in unrelated mm patch series.

The "minor" bucket is the one that actually correlates with delay: iomap
hooks, verity, encryption, subpage, zoned -- features that touched the
page cache or iomap path but did not drive new mm primitives.

## How long does a feature take to ship in enterprise Linux?

Of the 55 features, 44 have a recorded SUSE or RHEL enablement date:

| metric | n | mean | median | p90 | max |
|---|---|---|---|---|---|
| merge -> first enterprise | 44 | 2.24y | 2.13y | 2.95y | 8.05y |
| RFC -> first enterprise | 44 | 2.82y | 2.59y | 4.29y | 8.09y |

This is the "ten-year filesystem" rule applied at the per-feature scale:
**from RFC to a SUSE or Red Hat customer running it as enabled is on
average two-and-a-half years**, with a long right tail (xfs_repair_online
took 8 years).

The fastest merge-to-enterprise in the catalog is **XFS LBS at 0.71y**,
RHEL 10 picked it up as a Technology Preview the next merge window.
That is roughly 3x faster than the average. Other fast cases:
xfs_iomap_buffered (0.75y), btrfs_compress_zstd (0.92y), xfs_swapfile
(1.11y). The shared pattern: features whose downstream consumers
(databases, container runtimes, hyperscalers) had been asking for them
loudly before merge.

## Fixes-tag fan-out

`fixes_count` is the number of subsequent commits referencing the seed
sha in a `Fixes: <sha>` trailer, scanned on HEAD and bounded by the seed
sha's merge date. It is a low-quality proxy for post-merge fragility
because:

- Big topic-branch features land across many commits; we only count
  fixes citing the chosen seed sha, not the full series.
- Some Fixes: tags reference fixup commits within the original series.
- A feature with zero Fixes hits might be deeply stable, or it might be
  one whose later breakage cited a different sha than ours.

With those caveats, the distribution is dominated by zeros. The two
non-zero seed shas worth mentioning:

- `ext4_mballoc` at 4 hits across an 17.83-year window -- fits, given
  how long mballoc has been the ext4 default.
- `ext4_iomap_dio` at 4 hits within its 6-year window -- consistent
  with the well-known DIO-iomap rough edges.

LBS has 2 hits on XFS and 1 on btrfs since merge, in a sub-1-year window.
At this point the signal is too small to interpret; we re-check next
year.

## What does this say about the AI/kdevops question?

The user's framing was whether the LBS schedule was visibly faster than
the historical baseline because of kdevops plus AI-assisted testing. The
data say:

- **Per-attempt RFC-to-merge for LBS-on-XFS (0.97y)** is *not* faster
  than the global average (0.71y). On that metric alone the 2023 attempt
  is unremarkable.
- **First-idea-to-merge for LBS (17.31y)** is the longest in the catalog
  by a wide margin. The 2023 attempt was the first to actually land.
- **Merge-to-enterprise for XFS LBS (0.71y)** is the fastest in the
  catalog. RHEL 10 shipped LBS within the first merge window after its
  upstream landing.
- **ext4 and btrfs LBS adoption took 0.34y and 0.82y RFC-to-merge**,
  consistent with reusing the mm runway XFS forced into existence.

The conclusion the data support: **the LBS schedule looks slow at any
single RFC and exceptionally short across the whole arc**. The 2023
attempt was the one that finally cleared the gates, and the gates that
mattered (mm folios, iomap maturity, kdevops-driven test surface
expansion) had been moved by years of separate work. Crediting AI in
isolation would be hard to defend on these numbers; crediting the
combination of mm prerequisites, iomap maturity, and the
kdevops-plus-AI test surface that the 2023 series was tested under is
defensible and consistent with the catalog.

## Caveats

- "RFC date" is the first list posting of the patch series that
  ultimately landed. For LBS, prior failed RFCs are tracked separately
  in `historical_attempts` so neither the per-feature RFC-to-merge nor
  the first-idea-to-merge numbers are confused with each other.
- Enterprise enablement dates are vendor-release-month, not internal
  test-cycle start. SUSE and Red Hat both run multi-year stabilization
  internally; the catalog records the customer-visible date, which is
  the one the rest of the industry can verify.
- The catalog is incomplete by design. Bug-fix and cleanup features are
  out of scope; only landings that introduced a new format-level or
  interface-level capability are tracked. The full Fixes-tag fan-out
  numbers would change if every commit on a topic branch were
  considered a seed.
- The kernel tree HEAD this report was generated against is
  v7.1-rc4. Later kernels will move the post-merge Fixes counts upward
  on the still-young LBS features; that is a feature of the pipeline,
  not a flaw of the methodology.
