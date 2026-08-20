## Why

The lineage model needs an ordinary discoverable command so a person or tool can
supply a theorem name and receive the same evidence. CLI behavior must make database
freshness, any Lean refresh, output bounds, and proof-authority nonclaims obvious.

## What Changes

- Add `ladon theorem lineage THEOREM` with explicit view, boundary, edge-kind,
  depth/node/route caps, index path, refresh, format, and output options.
- Reuse a fresh stored closure by default and run the existing theorem planner only
  under the command's explicit refresh policy.
- Emit a versioned JSON envelope and compact text routes with source locations,
  authority, freshness, omissions, truncation, and nonclaims.
- Keep stdout/stderr separation, exit codes, help, interruption, and resource limits
  consistent with other installed Ladon commands.

## Capabilities

### New Capabilities

- `ladon-theorem-lineage-cli-and-renderers`: Caller-neutral theorem-lineage CLI and
  stable text/JSON output contract.

### Modified Capabilities

None.

## Impact

- Extends `theorem_cli.py`, CLI help, rendering, installed-entrypoint tests, and
  result models.
- Depends on lineage ingestion, SQL queries, and projection packets.
