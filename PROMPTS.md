# PROMPTS.md

This file records the prompts that drove this project. Each entry is preserved
verbatim. New entries are appended.

## 2026-05-22 -- initial scoping prompt

The Linux kernel enterprise industry has known that it takes about 10 years to
stabilize a new Linux filesystem. I know because I worked for SUSE for years
and for a few years there and outside of SUSE I was also responsible for XFS
stable maintenance. I have a serious appreciation for what Enterprise Linux
distributions need for testing and stabilizing a filesystem, and new features.
What I don't know is how long it takes to stabilize a new XFS filesystem
feature.  But there have been many! Can you evaluate all XFS's new features by
evaluating when they posted as patches as RFCs first down to them being merged,
how many talks about them at LSFMM per year, then to being publicly shipping in
Linux enterprise releases like SUSE or Red Hat as enabled. Document all of the
features in a grid by this breakdown and then give me an empirical assessment
for how long on average it has taken to stabilize a new filesystem feature.
Then do the estimate without taking LBS into account as that feature as heavily
impacted by the positive use of AI through kdevops evolution and testing and my
goal is to evaluate how much *faster* did LBS get merged total from initial RFC
too final merging into Linux compared to the other features! Also as part of
the evaluation take into consideration that some filesystem features are core
XFS only, but others required core memory management changes, and LBS was one
of the most impactful changes to core memory management so we want to do an
analysis also on which features also depending on similar core MM changes.
Then we can analyze and compare against features which did impact mm as well.
We can also also answer and analyze after LBS was merged with XFS enabled how
long it took to enable LBS on other filesystems, as now ext4 and btrfs have
some level of support for LBS. Evaluate what level of support they had and how
long it took also to introduce LBS into ext4, btrfs. To make that worthy then
do the same feature analysis on ext4 and btrfs. Yes this is expected to take
long. Yes, use the local code for inspection like fo rexample this may be
useful to you on include/linux/fs.h struct file_system_type [...] so FS_LBS is
useful. Do also an inspection lore.kernel.org if you ar eallowed to for RFCs,
and lwn.net for article sand LFSMM coverage. your output will be a cvs file
with all the data collected, json files, whatever, and put them into a new
directory. Then you want to analyze them and also provide a comprehenseise
html output file which matches the style of thee pages in https://knlp.io/ and
you want to make the code you use to analyze this to be scalable so we can
re-run this late rin the future. Generate beautiful comprehensive graphs. Put
this all into a new project git tree, in ~/devel/fs-features/ and commit
atomically as you go. Document the prompt I just gave you in a file called
PROMPTS.md and also copy the licensing and practices patch submitting
guidelines and study CLAUDE.md there and create a similar one for us which
will help us ensure we commit things in a clear way. We want to measure the
analysis of filesystem featurees across the board wstarting with xfs, ext4,
and btrfs and the impact with mm. The impact AI has had one stabilizing
filesystem features will be inferred afterwards through an analysis. Also I
forgot: take into consideration Fixes tags for commits which have annotation
for fixes to the filesystems mentioning the original commits that added the
features.
