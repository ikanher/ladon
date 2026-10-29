# Proposal

## Why

Scoped extraction stops at 8,192 visits on the original diagnostic theorem, whose existing traversal needs 109,620 visits. The user requested a larger, CLI-configurable allowance and performance measurements before accepting an optimization.

## What Changes

- Expose `proof-search proof slice --max-nodes` and the Python `max_nodes` keyword for both profiles, with default 131,072 and accepted range 1–1,048,576.
- Bind the selected allowance to slice identity and retain it on both correspondence freshness replays. Keep process, memory, depth and output limits independent.
- Compare cached and original traversal on identical inputs. Retain the original implementation unless the measured benefit warrants extra complexity.
- Preserve dependent instance names in closed proof exports and source-goal completion, retaining empty-context type/proof checks and each consumer's resource bounds.
- Replay the actual theorem and existing application controls, preserving every historical diagnostic and reporting any subsequent boundary.

Acceptance is specified in [the slice delta](specs/ladon-lean-proof-slices/spec.md). Passing an answer-informed target establishes its extraction scope, not autonomous discovery or a theorem refutation.

## Capabilities

### New Capabilities

- `ladon-lean-proof-slices`: Add explicit traversal-allowance requirements to the capability already planned in the NL/Lean correspondence umbrella but not yet synchronized into main specs.

### Modified Capabilities

None in the synchronized main specification set.

## Impact

Both Lean slice helpers and their shared printing material, the Python extractor, CLI, validator, implementation identity and correspondence replay consumers; focused regressions and bundled/shared skill guidance. No new dependency, schema change, full-suite rerun, full-paper audit, or push.
