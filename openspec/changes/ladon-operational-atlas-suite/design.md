# Design Notes

## Operating Principle

The atlas should answer operational questions directly:

- What is hot across reports?
- What recurs across roots?
- What changed since the previous report set?
- Which packet metadata contradicts task evidence?
- What should a reviewer read first?

## Data Shape

The existing atlas JSON remains the canonical interchange surface. SQLite is a
derived query artifact, not a replacement. This keeps packet outputs easy to
diff while allowing reviewers and scripts to run stable SQL queries.

## Suggested SQLite Tables

- `reports`: one row per report root/file.
- `findings`: normalized finding rows with severity/category/root/report.
- `review_regions`: review-region classifications per root/report.
- `declarations`: declaration/recurrent-symbol rows where available.
- `unresolved_references`: unresolved-reference class rows.
- `packets`: OpenSpec packet metadata and inferred task completion.

## Canned Queries

- Hot modules across all reports.
- Recurring declarations across reports.
- Roots whose review-region class changed between report sets.
- Reports with proof-family pressure.
- Packets whose metadata status disagrees with task completion evidence.

## Diff Policy

Diffs should be stable and explainable before they are clever. The first
implementation should compare normalized row sets and report added, removed, and
changed rows by category.

## Reviewer Cards

Cards should be short enough to skim and strong enough to route review:

- root/report identity
- extraction backend
- top findings
- review-region class
- strongest evidence
- known non-claims
- links to source report JSON/text

## Literature Tie-In

This umbrella follows the local literature extension: graph-query papers justify
queryable atlas storage, architecture-evolution work motivates atlas diffs, and
proof-engineering work motivates explicit proof/evidence surfaces.
