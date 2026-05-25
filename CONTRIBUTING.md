# Contributing

This project welcomes two kinds of contributions:

1. New features added to the catalog (a row of data).
2. Case studies for features that already exist in the catalog (a page
   of narrative).

The first is mechanical: append a JSON record, run `make`. The second is
the more valuable contribution and is what this document focuses on.

## Who should write a case study

If you maintained, designed, reviewed, or stabilized a major Linux
filesystem feature, you. The catalog row gives the numbers; only the
people who were on the threads can give the context. Co-authors and
contributors who lived only a part of the arc are welcome too — the
authors list in the frontmatter is plural for a reason.

If you are interested in writing a case study but did not live through
the feature directly, please open an issue first so we can pair you with
someone who did. The case studies are first-person where it matters; we
do not want second-hand history that is hard for readers to verify.

## What a good case study looks like

The shape of the LBS case study is the template
(`case_studies/lbs.md`). It is opinionated on structure precisely so
that the site can render every case study consistently and so contributors
do not have to invent the wheel each time.

A case study should contain:

1. **YAML frontmatter** with at minimum: `slug`, `title`, `subtitle`,
   `filesystems` (list), `mm_impact` (`none`/`minor`/`major`),
   `first_idea_date`, `first_landed_date`, `first_landed_version`,
   `status`, `authors`, `maintainers`, `last_updated`.
2. **A "what and why" intro** that names the unit of work in one
   paragraph and the motivation in another.
3. **A timeline-of-attempts table** when the feature has more than one
   RFC, with lore.kernel.org or LWN links for every entry. The bigger
   the prior history, the more important this table.
4. **A "what was different about the attempt that landed" section**
   naming the prerequisites (the mm/iomap/folio work that opened the
   runway) and the inflection point (the design guidance, the LSFMM
   session, the test infrastructure that finally made it tractable).
5. **A per-phase narrative** of how the feature actually merged with
   commit SHAs and dates. This is the part future maintainers will
   reference.
6. **A small numbers table** comparing the catalog metrics
   (RFC-to-merge, first-idea-to-merge, merge-to-enterprise, lag after
   the lead implementation if multi-fs).
7. **A short reflection** on what the feature suggests about how Linux
   filesystem features mature. Two or three patterns max; do not over-
   generalize from a single case.
8. **A references section**: kernelnewbies pages, LWN articles, the
   key lore threads, and any companion tooling
   (e.g. [kdevops](https://github.com/linux-kdevops/kdevops)).

## Style conventions

- **Be specific, not breezy.** Prefer "v6.12 (2024-09-03), commit
  `7df7c204c678`, authored by Pankaj Raghav and reviewed by Christian
  Brauner / Christoph Hellwig / Darrick Wong" over "merged in late
  2024."
- **Name the people.** Linux is a community of authors. Saying "the
  XFS reflink series was merged" loses the fact that Darrick Wong
  wrote it. The case study should make that clear.
- **Link to primary sources.** Lore threads, LWN articles,
  kernelnewbies pages — every claim of fact should be reachable in one
  click.
- **Show your work for the numbers.** If you cite "the series took
  0.97 years from RFC to merge," that number should be derivable from
  the dates already in the table.
- **Avoid hype adjectives.** "Comprehensive", "robust", "powerful"
  decorate without informing. Replace with what the work actually does
  and measures.
- **Write prose, not bullet farms.** Bullets are for lists, not for
  paragraphs in disguise. Narrative paragraphs read better and survive
  longer.
- **No marketing voice.** This is engineering history. The audience is
  other filesystem maintainers.

## Submitting

1. Fork the repository.
2. Create a branch named after the feature: `case-study-<slug>`.
3. Add `case_studies/<slug>.md`. Use `case_studies/lbs.md` as the
   template. Edit the YAML frontmatter and write the body.
4. Run `make case-studies` to render `docs/case_studies/<slug>.html`.
   Open it in a browser and confirm the layout reads cleanly.
5. Optionally run `make` to regenerate the whole site so the per-feature
   case-study link picks up on the main report.
6. Commit with a kernel-style message (see below).
7. Open a pull request.

## Commit messages

This project follows the same commit-message conventions as Linux
kernel patches:

```
<area>: <one-line subject capped at 70 chars>

A paragraph or two of body, also wrapped at 70 chars, explaining what
changed and why. Reference commits with full or short SHA, lore
threads by their canonical URL.

Signed-off-by: Your Name <you@example.com>
```

- The Signed-off-by line is required and constitutes your assertion of
  the [Developer Certificate of Origin](https://developercertificate.org/).
- Atomic commits: one logical change per commit. A case study is one
  commit unless you have a genuine reason to split it.
- Subject in imperative mood ("add", "fix", "rewrite"), not past tense.
- No "Co-Authored-By:" or "Generated with X" trailers.
- 70-character wrap on both subject and body.

## Pipeline changes

If your contribution touches the pipeline (`scripts/`, `Makefile`):

- Keep changes idempotent — running `make` twice should produce
  identical output.
- Preserve provenance: do not overwrite manually-curated fields with
  derived values without a deliberate flag.
- Whitespace: run `make whitespace-fix` before committing.
- The pipeline is deliberately Python-stdlib heavy with a small set of
  pinned third-party libs (`matplotlib`, `markdown`, `pyyaml`). New
  dependencies require justification in the commit message.

## Catalog changes

When adding or amending a feature row in `data/features_<fs>.json`:

- The `merged_sha` must resolve in the upstream Linus tree.
- Manual fields carry an explicit `source:` ("manual", "lore",
  "lwn:<article-id>") so re-enrichment can leave them alone.
- For multi-RFC features, use `first_idea_date` for the earliest
  proposal and `historical_attempts` for every prior failed attempt.
  Do not bury that history inside the main `rfc_date` field — the
  whole point of the dual fields is to make the long arc visible.

## Code of conduct

Be kind. Critique work, not people. If a case study disagrees with
your memory of the history, open a comment on the PR with the
primary source you would cite instead and we will work it out.

Thanks for contributing.
