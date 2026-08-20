# Design Notes

## Canonical Surface

Atlas JSON remains canonical. SQLite is a derived artifact that can be deleted
and regenerated.

## Tables

- `nodes`: all graph nodes with JSON data.
- `edges`: all graph edges with JSON data.
- `reports`: report nodes with root and count columns.
- `findings`: finding nodes joined to their report.
- `review_regions`: review-region nodes joined to their report.
- `signals`: review-region signal nodes joined to their region and report.
- `declaration_highlights`: report-to-declaration highlight edges.
- `module_highlights`: report-to-module highlight edges.

## Canned Queries

- `hotspots`: recurring finding subjects across reports.
- `recurring_declarations`: declaration highlight recurrence across reports.
- `review_region_pressure`: review-region kinds by report count and signal
  pressure.
- `proof_family_pressure`: proof-family findings/signals by subject.
