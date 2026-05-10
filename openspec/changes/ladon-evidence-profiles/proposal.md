# Ladon Evidence Profiles

## Why

Packet evidence currently uses one generic score. That is useful, but it mixes
review packets and witness bundles. The r37 packet should be described as a
review packet with enough review evidence, not as a failed witness bundle.

## What

- Add evidence profiles: `generic`, `review_packet`, `witness_bundle`, and
  `release_bundle`.
- Preserve existing generic score/status fields.
- Add profile-specific status and required checks.
- Expose a `--packet-profile` CLI option.

## Non-Goals

- No checker execution.
- No witness correctness claim.
- No repo-specific packet rules.
