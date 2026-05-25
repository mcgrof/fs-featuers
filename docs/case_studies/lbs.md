---
slug: lbs
title: Large Block Sizes
subtitle: From Lameter 2007 to LBS-everywhere 2026 — anatomy of an eighteen-year arc
filesystems: [xfs, ext4, btrfs]
mm_impact: major
first_idea_date: 2007-05-15
first_landed_date: 2024-09-03
first_landed_version: v6.12
status: shipping
authors:
  - Christoph Lameter (original compound-page proposal, 2007)
  - Nick Piggin (fsblock attempt, 2007–2009)
  - Dave Chinner (multi-year design guidance, 2014/2018/2023)
  - Pankaj Raghav (XFS LBS series that landed, 2023–2024)
  - Luis Chamberlain (block layer LBS, buffer-head bdev cache, large sector sizes)
  - Hannes Reinecke (block layer collaborator)
  - Matthew Wilcox (folio infrastructure)
  - Darrick Wong (XFS reviewer / co-author)
  - Qu Wenruo (btrfs LBS series)
maintainers: Pankaj Raghav, Luis Chamberlain, Hannes Reinecke
related: [dax, large_folios]
last_updated: 2026-05-25
---

# Large Block Sizes (LBS)

## What and why

LBS lets a filesystem use a logical block size larger than the system's
`PAGE_SIZE`. Storage hardware has been quietly shipping 16 KiB indirection
units for years, databases speak in 16 KiB / 32 KiB pages, and the bigger
the filesystem block the smaller the metadata overhead. The Linux page
cache, however, was wired to `PAGE_SIZE` everywhere — and that single
assumption is what made LBS a seventeen-year story instead of a one-cycle
patch series.

This case study is the worked example of how core filesystem features
actually mature in Linux. It catalogs every serious attempt, the
mailing-list and LSFMM discussions that pulled the design back into the
ditch and out of it again, and the eventual landing across XFS, the
block-device cache, ext4, and btrfs.

## Timeline of attempts

| Year | Author | Posting / venue | Outcome |
|---|---|---|---|
| 2007-05 | Christoph Lameter | [Variable Order Page Cache](https://lwn.net/Articles/232757/) — compound pages in the page cache | Stalled |
| 2007-07 | Nick Piggin | [fsblock](https://lwn.net/Articles/239621/) — replace `buffer_head` to support larger blocks | Stalled |
| 2009-03 | Nick Piggin | [Updated fsblock patches](https://lwn.net/Articles/321390/) | Did not land |
| 2014-01 | Dave Chinner | [Why prior LBS efforts failed and what to try instead](https://lore.kernel.org/linux-mm/20140123082121.GN13997@dastard/) | Design analysis |
| 2017-03 | LSFMM 2017 | [Page-cache larger than PAGE_SIZE](https://lwn.net/Articles/717953/) — group discussion | Inconclusive |
| 2018-11 | Dave Chinner | [Block size > PAGE_SIZE attempt](https://lwn.net/ml/linux-fsdevel/20181107063127.3902-1-david@fromorbit.com/) | Stalled |
| 2023-03 | Dave Chinner | [LBS design guidance to Pankaj Raghav](https://lore.kernel.org/all/20230308075952.GU2825702@dread.disaster.area/T/#u) | Inflection point |
| 2023-09 | Pankaj Raghav et al | [Enable block size > page size in XFS](https://lore.kernel.org/all/20230915183848.1018717-1-kernel@pankajraghav.com/) | Landed |
| 2024-09 | Pankaj Raghav | [XFS LBS merged](https://lore.kernel.org/linux-xfs/?q=7df7c204c678) — `7df7c204c678` | v6.12 |
| 2024-11 | Luis Chamberlain | [Large sector sizes via the bdev cache](https://lore.kernel.org/all/20241113094727.1497722-1-mcgrof@kernel.org/T/#mdea8649dd7254d1237d358c53dff17b02a60bf33) | RFC |
| 2025-02 | Luis Chamberlain | [Enable bs > ps for block devices](https://lore.kernel.org/linux-fsdevel/?q=block%2Fbdev+lift+block+size+restrictions+to+64k) — `47dd67532303` and friends | v6.15 |
| 2025-03 | Luis Chamberlain | `FS_LBS` flag gate added to `include/linux/fs.h` — `a64e5a596067` | v6.15 |
| 2025-09 | btrfs LBS | `98077f7f2180` (Qu Wenruo) — experimental bs > ps | v6.18 |
| 2025-11 | ext4 LBS | `cab8cbcb923a` (Luis Chamberlain) — block sizes > PAGE_SIZE on ext4 | v6.19 |
| 2026-01 | XFS | `4d6d335ea955` — LBS promoted from experimental together with metadirectory | v7.0 |

Eighteen years and three months of wall-clock between Lameter's first
mailing-list posting and XFS LBS shipping as a non-experimental,
default-buildable feature.

## What was different about the 2023 attempt

The first four attempts (Lameter 2007, Piggin 2007/2009, Chinner 2018)
all collided with the same wall: `struct page` was the page-cache unit,
and every page-cache helper assumed a single page meant `PAGE_SIZE`
bytes. Anything LBS-shaped had to either replace `buffer_head` (Piggin's
direction), introduce compound pages everywhere (Lameter's direction),
or wait for a generalized larger-than-page unit in the page cache.

By 2023 the generalized unit existed. `struct folio` had landed in v5.16
(Wilcox, 2021), multi-page folios were maturing in the page cache, and
the XFS iomap conversion (Hellwig 2019, v5.5) had already moved XFS's
buffered I/O path off `buffer_head`. The prerequisites for an LBS that
*was not also a rewrite of the page cache* were finally in place.

Dave Chinner's [March 8 2023 message to
Pankaj Raghav](https://lore.kernel.org/all/20230308075952.GU2825702@dread.disaster.area/T/#u)
captured the new design constraint: build on folios, don't touch
`buffer_head`-based filesystems yet, layer the changes (mm first, fs
second), and lean on `fstests` + `kdevops` for the test surface that the
prior attempts never had. That message is the inflection point. The
Raghav series that landed in v6.12 is recognizable as the direct
implementation of that guidance.

The other piece of the story is testing. LBS exercises corners of the
page cache, iomap, and the block layer that no normal workload reaches.
The 2023 series was the first LBS effort whose test matrix was driven
end-to-end by [kdevops](https://github.com/linux-kdevops/kdevops) —
provisioning matrices of block sizes, page sizes, filesystems, and
workloads, and triaged with AI-assisted summarization of `fstests`
output. The prior attempts had nothing comparable; bugs that would have
killed earlier RFCs were caught in test instead of in review.

## How LBS landed in XFS (v6.12, September 2024)

The XFS LBS series merged in seven mm/iomap/fs patches:

- `ab95d23bab22` filemap: allocate `mapping_min_order` folios in the page cache (2024-08-23)
- `26cfdb395eef` readahead: allocate folios with `mapping_min_order` in readahead (2024-08-23)
- `e220917fa507` mm: split a folio in minimum folio order chunks (2024-09-02)
- `743a2753a02e` filemap: cap PTE range to allowed zero fill in `folio_map_range()` (2024-09-02)
- `10553a91652d` iomap: fix `iomap_dio_zero()` for fs bs > system page size (2024-09-02)
- `79012cfa00b5` xfs: expose block size in stat (2024-09-02)
- `cebf9dacd5c3` xfs: make the calculation generic in `xfs_sb_validate_fsb_count()` (2024-09-02)
- `7df7c204c678` xfs: enable block size larger than page size support (2024-09-03)

All seven landed via the `vfs-6.12.blocksize` topic branch under
Christian Brauner. The XFS-side change is small because the heavy lifting
is in mm and iomap — exactly the layering Chinner's 2023 message
prescribed.

## Phase 2: the bdev cache and buffer heads (v6.15, February–March 2025)

XFS LBS works because XFS is iomap-native. ext4 still drives its
buffered I/O through `buffer_head`, and the block device cache itself
uses `buffer_head` for the partition-table read, the superblock probe,
and a thousand small things. Without LBS on the bdev cache, no
`buffer_head`-based filesystem could ever see a >PAGE_SIZE block.

The "Enable bs > ps for block devices" series authored by Luis
Chamberlain (with review from Hannes Reinecke, Christian Brauner,
Christoph Hellwig, and Pankaj Raghav) closed that gap in v6.15:

- `26fff8a4432f` block/bdev: use helper for max block size check (2024-12-18)
- `753aadebf2e3` fs/buffer: simplify `block_read_full_folio()` with `bh_offset()` (2025-02-24)
- `8b45a4f4133d` fs/mpage: use `blocks_per_folio` instead of `blocks_per_page` (2025-02-24)
- `e59e97d42b05` fs/buffer fs/mpage: remove large folio restriction (2025-02-24)
- `47dd67532303` block/bdev: lift block size restrictions to 64k (2025-02-24)
- `3c20917120ce` block/bdev: enable large folio support for large logical block sizes (2025-02-24)
- `425fbcd62d2e` bdev: use `bdev_io_min()` for statx block size (2025-02-24)
- `a64e5a596067` bdev: add back `PAGE_SIZE` block size validation for `sb_set_blocksize()` — the `FS_LBS` gate (2025-03-07)

The companion ["large sector sizes" series](https://lore.kernel.org/all/20241113094727.1497722-1-mcgrof@kernel.org/T/#mdea8649dd7254d1237d358c53dff17b02a60bf33)
posted November 2024 was the design lead-in for this work: it sketched
how the block layer could expose logical block sizes greater than
`PAGE_SIZE` to filesystems without burning down the bdev cache, and
walked through the buffer_head implications.

The `FS_LBS` flag in `include/linux/fs.h` is the bouncer: filesystems
that have audited their I/O path for LBS set the flag, and
`sb_set_blocksize()` refuses any non-LBS filesystem from mounting at
blocksize > `PAGE_SIZE`. This is what unblocked ext4.

## Phase 3: ext4 picks it up (v6.19, November 2025)

ext4 LBS landed in `cab8cbcb923a` after the bdev-cache runway was in
place. The ext4 series is much smaller than the XFS one — most of the
real work had already been done in mm, iomap, the block layer, and the
bdev cache. The ext4 RFC-to-merge was 0.34 years, the fastest of any
ext4 feature in the catalog except `ext4_encrypt` (which only had to
reserve codepoints to merge).

## Phase 4: btrfs follows (v6.18, September 2025, experimental)

btrfs LBS landed as experimental in `98077f7f2180` (Qu Wenruo). btrfs
had to extend its pre-existing subpage machinery — already used for
4 KiB blocks on 64 KiB-page ARM systems — to symmetric bs > ps territory,
which is why the btrfs RFC-to-merge of 0.82y is longer than ext4's.

## Numbers

| metric | XFS | ext4 | btrfs |
|---|---|---|---|
| First-idea date | 2007-05-15 | 2007-05-15 | 2007-05-15 |
| Successful-attempt RFC | 2023-09-15 | 2025-07-25 | 2024-11-27 |
| Merged | 2024-09-03 (v6.12) | 2025-11-28 (v6.19) | 2025-09-23 (v6.18) |
| RFC → merge | 0.97y | 0.34y | 0.82y |
| First idea → merge | 17.31y | 18.54y | 18.36y |
| Lag after XFS LBS | — | 1.23y | 1.05y |
| Enterprise first | RHEL 10.0 (2025-05-20) | not yet | not yet |
| Merge → enterprise | 0.71y | — | — |

`merge → enterprise` for XFS LBS at 0.71 years is the fastest of any
feature in the catalog. RHEL 10 picked it up the next merge window. The
broader pattern: the fs-level RFC pace looks ordinary on each LBS
landing, but the first-idea-to-merge wall-clock is the longest of any
feature tracked, and the enterprise adoption pace is the fastest. The
two extremes are the same story told from different ends.

## What this case study suggests about how Linux fs features mature

Three patterns repeat across LBS that are worth watching for the next
case study:

1. **The hard problem is rarely in the filesystem.** XFS LBS is six
   small XFS patches sitting on top of years of mm, iomap, folio, and
   block-layer work. The per-feature RFC measures only the visible
   tip; the iceberg is the dependency chain.

2. **Stalled prior attempts are signal, not failure.** Lameter 2007,
   Piggin 2007/2009, and Chinner 2018 each named what was wrong and
   built shared vocabulary. The 2023 attempt did not start from
   scratch — it inherited a decade and a half of vocabulary about what
   "doing LBS right" had to look like.

3. **Testing surface matters more than reviewer count.** What changed
   in 2023 was less the design and more the test matrix that exercised
   it. The kdevops + AI-triage pipeline made it possible to catch
   bs/ps/workload combinations that broke the page cache in corners
   nobody would think to look at by eye. Without that, the 2023 RFC
   would have been "Chinner 2018 redux."

## References and further reading

- [kernelnewbies LBS project page](https://kernelnewbies.org/KernelProjects/large-block-size) — canonical chronology, kept up to date by the project.
- [LWN: A larger-than-page page cache](https://lwn.net/Articles/610174/) — DAX-era LWN coverage of the folio direction that ultimately enabled LBS.
- [LWN: LSFMM 2017 page-cache > PAGE_SIZE](https://lwn.net/Articles/717953/) — the discussion that revived the topic.
- [LWN: LSFMM 2023 block-size > page-size session](https://lwn.net/Articles/932900/) — coverage of the run-up to the 2023 RFC.
- [Pankaj Raghav's XFS LBS announcement](https://lore.kernel.org/all/20230915183848.1018717-1-kernel@pankajraghav.com/) — the RFC that landed.
- [Dave Chinner's design guidance, 2023-03-08](https://lore.kernel.org/all/20230308075952.GU2825702@dread.disaster.area/T/#u) — the inflection point.
- [Luis Chamberlain's large sector sizes RFC, 2024-11-13](https://lore.kernel.org/all/20241113094727.1497722-1-mcgrof@kernel.org/T/#mdea8649dd7254d1237d358c53dff17b02a60bf33) — the lead-in to the bdev-cache LBS work.
- [linux-kdevops](https://github.com/linux-kdevops/kdevops) — the test orchestration framework that exercised the 2023+ LBS series end-to-end.
