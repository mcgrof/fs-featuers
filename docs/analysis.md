# Filesystem feature stabilization analysis

Total features tracked: 55. Per filesystem: btrfs 18, ext4 13, xfs 24.

## RFC to merge

RFC -> merge (all) (n=55): mean 0.71y, median 0.48y, p90 1.27y, min 0.04y, max 4.98y
RFC -> merge (LBS excluded) (n=52): mean 0.71y, median 0.47y, p90 1.29y, min 0.04y, max 4.98y

Per filesystem:
- btrfs RFC -> merge (n=18): mean 0.49y, median 0.3y, p90 0.96y, min 0.1y, max 1.51y
- ext4 RFC -> merge (n=13): mean 0.71y, median 0.49y, p90 1.12y, min 0.04y, max 3.12y
- xfs RFC -> merge (n=24): mean 0.89y, median 0.59y, p90 1.49y, min 0.04y, max 4.98y

By mm-impact bucket:
- mm_impact=none RFC -> merge (n=38): mean 0.65y, median 0.35y, p90 1.24y, min 0.04y, max 4.98y
- mm_impact=minor RFC -> merge (n=12): mean 0.92y, median 0.86y, p90 1.29y, min 0.04y, max 3.12y
- mm_impact=major RFC -> merge (n=5): mean 0.68y, median 0.77y, p90 0.91y, min 0.34y, max 0.97y

## Merge to enterprise (first SUSE or RHEL enablement)

Merge -> enterprise (all) (n=44): mean 2.24y, median 2.13y, p90 2.95y, min 0.71y, max 8.05y
RFC -> enterprise (all) (n=44): mean 2.82y, median 2.59y, p90 4.29y, min 1.21y, max 8.09y

## LBS biography

- btrfs LBS: RFC 2024-11-27, merged 2025-09-23 (v6.18-rc1), RFC-to-merge 0.82y, first-idea-to-merge 18.36y, fixes-tag count 1.
- ext4 LBS: RFC 2025-07-25, merged 2025-11-28 (v6.19-rc1), RFC-to-merge 0.34y, first-idea-to-merge 18.54y, fixes-tag count 0.
- xfs LBS: RFC 2023-09-15, merged 2024-09-03 (vfs-6.12.blocksize), RFC-to-merge 0.97y, first-idea-to-merge 17.31y, fixes-tag count 2.

LBS adoption after XFS:
- ext4 LBS merged 2025-11-28 (1.23y after XFS LBS)
- btrfs LBS merged 2025-09-23 (1.05y after XFS LBS)

## Per-feature detail

| fs | feature | RFC | merged | RFC->merge (y) | merge->enterprise (y) | mm-impact | fixes |
|---|---|---|---|---|---|---|---|
| btrfs | btrfs_compress_lzo | 2010-10-08 | 2010-12-22 | 0.21 | 2.53 | none | 0 |
| btrfs | btrfs_mixed_groups | 2010-09-22 | 2010-10-29 | 0.1 | 2.67 | none | 0 |
| btrfs | btrfs_qgroups | 2011-09-14 | 2012-07-12 | 0.83 | 2.29 | none | 2 |
| btrfs | btrfs_send_receive | 2012-04-12 | 2012-07-25 | 0.28 | 2.26 | none | 1 |
| btrfs | btrfs_extended_iref | 2012-06-13 | 2012-10-09 | 0.32 | 2.05 | none | 2 |
| btrfs | btrfs_raid56 | 2011-12-15 | 2013-02-01 | 1.13 | - | none | 0 |
| btrfs | btrfs_no_holes | 2014-08-19 | 2015-07-11 | 0.89 | 3.01 | none | 0 |
| btrfs | btrfs_free_space_tree | 2015-09-23 | 2015-12-17 | 0.23 | 4.59 | none | 0 |
| btrfs | btrfs_compress_zstd | 2017-04-12 | 2017-08-15 | 0.34 | 0.92 | none | 3 |
| btrfs | btrfs_raid1c34 | 2019-09-13 | 2019-11-18 | 0.18 | 1.59 | none | 2 |
| btrfs | btrfs_async_discard | 2019-12-04 | 2020-01-20 | 0.13 | 2.42 | none | 0 |
| btrfs | btrfs_subpage | 2020-04-08 | 2021-02-08 | 0.84 | 2.36 | minor | 0 |
| btrfs | btrfs_zoned | 2020-09-30 | 2020-12-08 | 0.19 | 2.53 | minor | 0 |
| btrfs | btrfs_verity | 2021-03-23 | 2021-08-23 | 0.42 | - | minor | 3 |
| btrfs | btrfs_block_group_tree | 2022-06-29 | 2022-09-26 | 0.24 | 1.71 | none | 1 |
| btrfs | btrfs_raid_stripe_tree | 2022-04-07 | 2023-10-12 | 1.51 | - | none | 0 |
| btrfs | btrfs_simple_quotas | 2023-09-01 | 2023-10-12 | 0.11 | - | none | 2 |
| btrfs | btrfs_lbs | 2024-11-27 | 2025-09-23 | 0.82 | - | major | 1 |
| ext4 | ext4_extents_64bit | 2006-06-22 | 2006-10-11 | 0.3 | 2.45 | none | 0 |
| ext4 | ext4_mballoc | 2007-08-13 | 2008-01-29 | 0.46 | 1.15 | none | 4 |
| ext4 | ext4_metadata_csum | 2011-12-19 | 2012-01-04 | 0.04 | 2.81 | none | 0 |
| ext4 | ext4_inline_data | 2012-06-13 | 2012-12-10 | 0.49 | 1.5 | none | 1 |
| ext4 | ext4_dax | 2014-08-26 | 2015-02-16 | 0.48 | 1.72 | major | 0 |
| ext4 | ext4_encrypt | 2015-01-06 | 2015-01-19 | 0.04 | 3.49 | minor | 0 |
| ext4 | ext4_casefold | 2018-09-21 | 2019-04-25 | 0.59 | 2.16 | none | 0 |
| ext4 | ext4_verity | 2018-05-31 | 2019-08-12 | 1.2 | 1.86 | minor | 2 |
| ext4 | ext4_fast_commit | 2019-12-31 | 2020-10-21 | 0.81 | 3.64 | none | 2 |
| ext4 | ext4_orphan_file | 2020-12-08 | 2021-08-30 | 0.73 | 2.79 | none | 3 |
| ext4 | ext4_iomap_dio | 2016-09-22 | 2019-11-05 | 3.12 | 2.53 | minor | 4 |
| ext4 | ext4_atomic_writes | 2024-09-23 | 2025-05-20 | 0.65 | - | minor | 0 |
| ext4 | ext4_lbs | 2025-07-25 | 2025-11-28 | 0.34 | - | major | 0 |
| xfs | xfs_delaylog | 2009-12-01 | 2010-05-24 | 0.48 | 1.75 | none | 1 |
| xfs | xfs_v5_crc | 2012-11-08 | 2013-04-27 | 0.47 | 1.5 | none | 0 |
| xfs | xfs_ftype | 2013-07-25 | 2013-08-22 | 0.08 | 2.31 | none | 0 |
| xfs | xfs_finobt | 2013-12-12 | 2014-04-24 | 0.36 | 1.64 | none | 0 |
| xfs | xfs_dax | 2014-08-26 | 2015-06-04 | 0.77 | 1.43 | major | 0 |
| xfs | xfs_spinodes | 2015-01-26 | 2015-05-29 | 0.34 | 2.28 | none | 0 |
| xfs | xfs_meta_uuid | 2015-04-29 | 2015-07-29 | 0.25 | 2.11 | none | 1 |
| xfs | xfs_rmapbt | 2015-10-12 | 2016-08-03 | 0.81 | 1.95 | none | 0 |
| xfs | xfs_reflink | 2015-11-16 | 2016-10-03 | 0.88 | 2.59 | minor | 0 |
| xfs | xfs_scrub | 2017-04-13 | 2017-10-26 | 0.54 | 2.74 | none | 0 |
| xfs | xfs_pnfs | 2014-04-15 | 2015-02-16 | 0.84 | 1.72 | none | 1 |
| xfs | xfs_swapfile | 2018-04-08 | 2018-05-15 | 0.1 | 1.11 | minor | 1 |
| xfs | xfs_iomap_buffered | 2018-09-25 | 2019-10-21 | 1.07 | 0.75 | minor | 2 |
| xfs | xfs_bigtime | 2020-06-30 | 2020-09-15 | 0.21 | 1.67 | none | 0 |
| xfs | xfs_inobtcount | 2020-05-27 | 2020-09-15 | 0.3 | 1.67 | none | 0 |
| xfs | xfs_needsrepair | 2020-08-31 | 2020-12-09 | 0.27 | 1.43 | none | 0 |
| xfs | xfs_repair_online | 2018-04-30 | 2018-05-15 | 0.04 | 8.05 | none | 0 |
| xfs | xfs_log_xattrs | 2019-07-31 | 2022-05-09 | 2.77 | 2.1 | none | 0 |
| xfs | xfs_nrext64 | 2021-08-19 | 2022-04-11 | 0.64 | 2.17 | none | 0 |
| xfs | xfs_exchrange | 2022-12-30 | 2024-04-15 | 1.29 | - | minor | 0 |
| xfs | xfs_parent | 2019-05-01 | 2024-04-23 | 4.98 | - | none | 0 |
| xfs | xfs_metadir | 2023-04-07 | 2024-11-05 | 1.58 | - | none | 0 |
| xfs | xfs_zoned | 2023-12-04 | 2025-03-03 | 1.25 | - | minor | 2 |
| xfs | xfs_lbs | 2023-09-15 | 2024-09-03 | 0.97 | 0.71 | major | 2 |
