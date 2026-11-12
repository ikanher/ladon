# Proposal

## Why

The current correspondence goals check premise supply and conclusion transfer under the interpreted hypotheses. They do not separately establish whether those hypotheses are jointly inhabitable, so an impossible context can support every implication vacuously.

## What Changes

- Generate separate witness and contradiction obligations for the complete local context captured at a selected proof position, with explicit fixed-parameter assignments and retained derived-value dependencies.
- Accept only fresh checked evidence for `witnessed` or `inconsistent`; keep failed search, unsupported contexts and exhaustion unresolved.
- Exclude the tested hypotheses and downstream consequences from witness construction; bind the exact parameter policy and full selected context.
- Surface context feasibility without invalidating legitimate conditional or proof-by-contradiction reasoning.

Detailed acceptance is in [the capability specification](specs/ladon-assumption-feasibility/spec.md). Success is evidence for the declared bounded behavior, with limitations visible to the caller.

## Capabilities

### New Capabilities

- `ladon-assumption-feasibility`: Checked feasibility diagnostics for exact local assumption contexts.

### Modified Capabilities

None. Existing probe, identity, authority and coverage requirements remain in force; these additions do not reinterpret historical results.

## Impact

Extend existing typed-context and source-goal checking paths, with bounded evidence records and focused tests. Requires acceptance of the four feasibility baseline cases under the [staged baseline policy](../ladon-pitfall-baselines/specs/ladon-pitfall-regression-evaluation/spec.md) before semantic runtime implementation; does not change the meaning of existing correspondence support.

