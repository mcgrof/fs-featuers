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

![LBS biography: from Lameter 2007 to LBS-everywhere 2026](images/lbs_biography.png)

## Timeline of attempts

<div class="overflow-x-auto -mx-2">
<table class="w-full text-sm border-collapse mb-6">
<thead class="border-b border-gray-700 text-gray-400">
<tr><th class="text-left py-2 px-3 font-medium whitespace-nowrap">Year</th><th class="text-left py-2 px-3 font-medium whitespace-nowrap">Author</th><th class="text-left py-2 px-3 font-medium">Posting / venue</th><th class="text-left py-2 px-3 font-medium whitespace-nowrap">Outcome</th></tr>
</thead>
<tbody>
<tr class="border-b border-gray-800"><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">2007-05</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Christoph Lameter</td><td class="py-2 px-3 text-gray-300 align-top"><a class="text-cyan-400 hover:text-cyan-200 hover:underline" href="https://lwn.net/Articles/232757/">Variable Order Page Cache</a> &mdash; compound pages in the page cache</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Stalled</td></tr>
<tr class="border-b border-gray-800"><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">2007-07</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Nick Piggin</td><td class="py-2 px-3 text-gray-300 align-top"><a class="text-cyan-400 hover:text-cyan-200 hover:underline" href="https://lwn.net/Articles/239621/">fsblock</a> &mdash; replace <code class="px-1.5 py-0.5 rounded bg-gray-900 text-cyan-300 font-mono text-sm">buffer_head</code> to support larger blocks</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Stalled</td></tr>
<tr class="border-b border-gray-800"><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">2009-03</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Nick Piggin</td><td class="py-2 px-3 text-gray-300 align-top"><a class="text-cyan-400 hover:text-cyan-200 hover:underline" href="https://lwn.net/Articles/321390/">Updated fsblock patches</a></td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Did not land</td></tr>
<tr class="border-b border-gray-800"><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">2014-01</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Dave Chinner</td><td class="py-2 px-3 text-gray-300 align-top"><a class="text-cyan-400 hover:text-cyan-200 hover:underline" href="https://lore.kernel.org/linux-mm/20140123082121.GN13997@dastard/">Why prior LBS efforts failed and what to try instead</a></td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Design analysis</td></tr>
<tr class="border-b border-gray-800"><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">2017-03</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">LSFMM 2017</td><td class="py-2 px-3 text-gray-300 align-top"><a class="text-cyan-400 hover:text-cyan-200 hover:underline" href="https://lwn.net/Articles/717953/">Page-cache larger than PAGE_SIZE</a> &mdash; group discussion</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Inconclusive</td></tr>
<tr class="border-b border-gray-800"><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">2018-11</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Dave Chinner</td><td class="py-2 px-3 text-gray-300 align-top"><a class="text-cyan-400 hover:text-cyan-200 hover:underline" href="https://lwn.net/ml/linux-fsdevel/20181107063127.3902-1-david@fromorbit.com/">Block size &gt; PAGE_SIZE attempt</a></td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Stalled</td></tr>
<tr class="border-b border-gray-800"><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">2023-03</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Dave Chinner</td><td class="py-2 px-3 text-gray-300 align-top"><a class="text-cyan-400 hover:text-cyan-200 hover:underline" href="https://lore.kernel.org/all/20230308075952.GU2825702@dread.disaster.area/T/#u">LBS design guidance to Pankaj Raghav</a></td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Inflection point</td></tr>
<tr class="border-b border-gray-800"><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">2023-09</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Pankaj Raghav et al</td><td class="py-2 px-3 text-gray-300 align-top"><a class="text-cyan-400 hover:text-cyan-200 hover:underline" href="https://lore.kernel.org/all/20230915183848.1018717-1-kernel@pankajraghav.com/">Enable block size &gt; page size in XFS</a></td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Landed</td></tr>
<tr class="border-b border-gray-800"><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">2024-09</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Pankaj Raghav</td><td class="py-2 px-3 text-gray-300 align-top"><a class="text-cyan-400 hover:text-cyan-200 hover:underline" href="https://lore.kernel.org/linux-xfs/?q=7df7c204c678">XFS LBS merged</a> &mdash; <code class="px-1.5 py-0.5 rounded bg-gray-900 text-cyan-300 font-mono text-sm">7df7c204c678</code></td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">v6.12</td></tr>
<tr class="border-b border-gray-800"><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">2024-11</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Luis Chamberlain</td><td class="py-2 px-3 text-gray-300 align-top"><a class="text-cyan-400 hover:text-cyan-200 hover:underline" href="https://lore.kernel.org/all/20241113094727.1497722-1-mcgrof@kernel.org/T/#mdea8649dd7254d1237d358c53dff17b02a60bf33">Large sector sizes via the bdev cache</a></td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">RFC</td></tr>
<tr class="border-b border-gray-800"><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">2025-02</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Luis Chamberlain</td><td class="py-2 px-3 text-gray-300 align-top"><a class="text-cyan-400 hover:text-cyan-200 hover:underline" href="https://lore.kernel.org/linux-fsdevel/?q=block%2Fbdev+lift+block+size+restrictions+to+64k">Enable bs &gt; ps for block devices</a> &mdash; <code class="px-1.5 py-0.5 rounded bg-gray-900 text-cyan-300 font-mono text-sm">47dd67532303</code> and friends</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">v6.15</td></tr>
<tr class="border-b border-gray-800"><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">2025-03</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Luis Chamberlain</td><td class="py-2 px-3 text-gray-300 align-top"><code class="px-1.5 py-0.5 rounded bg-gray-900 text-cyan-300 font-mono text-sm">FS_LBS</code> flag gate added to <code class="px-1.5 py-0.5 rounded bg-gray-900 text-cyan-300 font-mono text-sm">include/linux/fs.h</code> &mdash; <code class="px-1.5 py-0.5 rounded bg-gray-900 text-cyan-300 font-mono text-sm">a64e5a596067</code></td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">v6.15</td></tr>
<tr class="border-b border-gray-800"><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">2025-09</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Qu Wenruo</td><td class="py-2 px-3 text-gray-300 align-top"><code class="px-1.5 py-0.5 rounded bg-gray-900 text-cyan-300 font-mono text-sm">98077f7f2180</code> &mdash; btrfs experimental bs &gt; ps</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">v6.18</td></tr>
<tr class="border-b border-gray-800"><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">2025-11</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Luis Chamberlain</td><td class="py-2 px-3 text-gray-300 align-top"><code class="px-1.5 py-0.5 rounded bg-gray-900 text-cyan-300 font-mono text-sm">cab8cbcb923a</code> &mdash; block sizes &gt; PAGE_SIZE on ext4</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">v6.19</td></tr>
<tr class="border-b border-gray-800"><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">2026-01</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">XFS</td><td class="py-2 px-3 text-gray-300 align-top"><code class="px-1.5 py-0.5 rounded bg-gray-900 text-cyan-300 font-mono text-sm">4d6d335ea955</code> &mdash; LBS promoted from experimental together with metadirectory</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">v7.0</td></tr>
</tbody>
</table>
</div>

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

![Phase 1: XFS LBS lands in v6.12, eight commits over two weeks](images/lbs_xfs_v6_12.png)

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

### What this phase was really for

The phrasing "LBS on the bdev cache" undersells what this work was
about. The end goal is **larger filesystem logical sector sizes** —
allowing a filesystem to expose, and the block layer to honor, a
sector that is the actual unit of failure on modern storage. Modern
NVMe drives are not 512-byte or 4 KiB devices internally. They are
16 KiB, 32 KiB, or larger indirection-unit (IU) devices, and the gap
between the LBA the host writes at and the indirection unit the drive
must rewrite is where write amplification, latency tails, and
QLC-flash wear come from. The drive can paper over the gap with its
own RMW, at a cost. Letting the filesystem speak in the drive's
native unit is how you stop paying that cost.

Larger sector sizes only become safe to use, however, when the
underlying device can guarantee that a sector-sized write either
completes in full or not at all — a *large atomic write*. The NVMe
spec exposes this via per-namespace fields:

- **NAWUPF** (Namespace Atomic Write Unit Power Fail): the largest
  write the namespace will complete atomically across a power loss,
  in logical block units.
- **NPWG** (Namespace Preferred Write Granularity): the namespace's
  preferred write size — for an IU-based drive, this is the
  indirection unit.

The relationship that matters for LBS is **NAWUPF ≥ NPWG**: the
drive will atomically write a unit at least as large as its preferred
granularity. When that holds, the host can use a filesystem block of
NPWG bytes without ever exposing a torn write to userspace. Modern
NVMe drives with large IUs (typical on enterprise QLC parts) ship
with exactly this relationship; the host side just had to be ready
to accept it.

That readiness is what this v6.15 series provides. Phase 1 (XFS LBS
in v6.12) proved LBS could land on a filesystem that did not use
`buffer_head`. Phase 2 extends the same capability to every
filesystem that does, by teaching the bdev cache, `fs/buffer.c`, and
`fs/mpage.c` to work with large folios sized to a >PAGE_SIZE logical
block. ext4's later LBS adoption (v6.19) is the visible payoff; the
broader payoff is that any future filesystem feature whose unit is
"a drive-native sector" — atomic writes proper, untorn
metadata journaling, asymmetric-replication formats — gets to assume
the substrate works.

![Phase 2: bdev cache + buffer heads for LBS, Dec 2024 to Mar 2025](images/lbs_bdev_v6_15.png)

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

![LBS adoption per fs: XFS opened the runway, ext4 and btrfs followed](images/lbs_per_fs.png)

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

## Enterprise enablement of large sector sizes

The XFS LBS row above records RHEL 10's pickup of XFS LBS in v6.12 — but
that is only Phase 1 of the LBS arc landing in enterprise. The bigger
payoff, **a filesystem using a logical sector size larger than
`PAGE_SIZE` on top of a drive that natively wants larger sectors**, also
requires Phase 2 (the v6.15 bdev cache and buffer-head LBS series) plus
hardware that opts in. The XFS-LBS-in-RHEL-10 figure of 0.71 years
understates how long it will take customers to actually run with larger
filesystem sectors on enterprise Linux.

A deployable large-sector-size configuration needs all five of:

1. **Hardware**: an NVMe drive that reports `NAWUPF >= NPWG` so the
   atomic write unit covers the device's preferred write granularity.
   Typical on enterprise QLC with large (16 KiB / 32 KiB / 64 KiB)
   indirection units; rare to absent on consumer drives.

2. **Kernel**: v6.15 or later. v6.12 only delivers XFS LBS on the iomap
   path; the bdev cache, partition probe, and superblock read still went
   through `PAGE_SIZE`-bounded buffer heads. v6.15 lifts that, adds the
   `FS_LBS` gating flag in `include/linux/fs.h`, and is the first
   kernel where the full bs > ps stack works for any filesystem.

3. **Filesystem**: an `FS_LBS`-flagged filesystem that has audited its
   I/O path for >PAGE_SIZE blocks. As of v7.1: XFS (since v6.12),
   bcachefs (since v6.15), btrfs (experimental since v6.18), ext4 (since
   v6.19).

4. **Userspace**: `mkfs` that accepts and validates a logical sector
   size larger than `PAGE_SIZE`, plus monitoring that knows what to
   watch for at the new size (write amplification, atomic-write counters,
   per-namespace power-fail granularity).

5. **Distribution support**: the vendor has run the test matrix for
   their support scope, documented the customer guidance, and is willing
   to take the support call when it goes wrong.

Distribution status as of 2026-05-25:

<div class="overflow-x-auto -mx-2">
<table class="w-full text-sm border-collapse mb-6">
<thead class="border-b border-gray-700 text-gray-400">
<tr><th class="text-left py-2 px-3 font-medium whitespace-nowrap">Distribution</th><th class="text-left py-2 px-3 font-medium whitespace-nowrap">Released</th><th class="text-left py-2 px-3 font-medium whitespace-nowrap">Base kernel</th><th class="text-left py-2 px-3 font-medium whitespace-nowrap">XFS LBS (v6.12)</th><th class="text-left py-2 px-3 font-medium whitespace-nowrap">bdev-cache LBS (v6.15)</th><th class="text-left py-2 px-3 font-medium">Comment</th></tr>
</thead>
<tbody>
<tr class="border-b border-gray-800"><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">RHEL 10.0</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">2025-05</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">6.12</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">yes (TP)</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">no</td><td class="py-2 px-3 text-gray-300 align-top">iomap path only; ships before the v6.15 cycle</td></tr>
<tr class="border-b border-gray-800"><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">RHEL 10.1+</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">TBD</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">6.12 + backports</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">yes</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">likely (backport)</td><td class="py-2 px-3 text-gray-300 align-top">speculative; watch the release notes</td></tr>
<tr class="border-b border-gray-800"><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">SLE 15 SP7</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">2025-06</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">6.4</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">no</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">no</td><td class="py-2 px-3 text-gray-300 align-top">kernel predates LBS upstream</td></tr>
<tr class="border-b border-gray-800"><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">SUSE 16.0</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">~2026-06</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">TBD (≥ 6.12)</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">likely</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">backport-dependent</td><td class="py-2 px-3 text-gray-300 align-top">depends on whether the v6.15 bdev work is backported</td></tr>
<tr class="border-b border-gray-800"><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Ubuntu 24.04 LTS</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">2024-04</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">6.8</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">no</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">no</td><td class="py-2 px-3 text-gray-300 align-top">kernel predates LBS; HWE stream may close the gap</td></tr>
<tr class="border-b border-gray-800"><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Ubuntu 26.04 LTS</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">~2026-04</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">TBD (≥ 6.14 expected)</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">likely</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">likely</td><td class="py-2 px-3 text-gray-300 align-top">first LTS with a base kernel new enough to ship the full stack</td></tr>
<tr class="border-b border-gray-800"><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">Azure Linux 3</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">2024-10</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">6.6</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">no</td><td class="py-2 px-3 text-gray-300 align-top whitespace-nowrap">no</td><td class="py-2 px-3 text-gray-300 align-top">would need a kernel rebase to pick this up</td></tr>
</tbody>
</table>
</div>

(Status above is best-effort from public release notes and kernel
package metadata; corrections via PR welcome. Unreleased rows are
speculation framed against published distro roadmaps.)

The realistic path from "XFS LBS upstream" (September 2024) to "large
filesystem sectors as a documented supported configuration on enterprise
Linux" is at least eighteen months and possibly longer. That puts the
*real* merge-to-enterprise wall-clock for the LBS program closer to two
years than the 0.71-year row the catalog shows for XFS LBS alone.

Two implications worth pulling out:

- The catalog's per-feature `merge_to_enterprise_years` field describes
  the visible step (the vendor flips a flag), not the underlying
  capability arriving in production fleets. For features whose value
  depends on a multi-stage stack — XFS LBS, then bdev cache LBS, then
  mkfs tooling, then validation — the catalog row can be a substantial
  underestimate. Future case studies should call this out where it
  applies; DAX is the obvious next example, with a much worse arc.

- The hardware question is doing more work than the kernel question. An
  enterprise QLC SSD with NAWUPF ≥ NPWG is the prerequisite that decides
  whether a customer actually benefits, and adoption of that hardware in
  the field is not what the kernel project tracks. The fs-features
  catalog records a kernel feature shipping; the enterprise *value* of
  LBS lives in a column we do not have yet, and that is the column most
  worth filling in next.

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
