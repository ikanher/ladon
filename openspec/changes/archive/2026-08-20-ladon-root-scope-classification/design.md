# Design

## Classifications

First slice:

- `public_root_narrow_inventory`: one-segment public root in a broad repo.
- `narrow_owner_broad_import`: deep owner root with large direct import closure.
- `narrow_owner`: deep owner root with high unreachable ratio but no broad
  direct import closure.
- `broad_inventory_scope_gap`: fallback for broad inventory reachability gaps.

These are explanation labels, not severity labels.
