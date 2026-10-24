# Proposal

## Why

Field use on the Mathlib companion index (evidence/r01/FEEDBACK.md) shows that 3.3% of declaration rows (8,024 of 240,583, in 294 files) have no lexical candidate name. Qualified name search therefore returns zero rows for real theorems such as `Real.add_one_le_exp` and `Real.exp_bound_div_one_sub_of_interval`. Agents doing Ladon-first discovery fall back to `rg`, and the exact-match counters in the match summary disagree with the ranked rows.

The cause is the lexical scope tracker. It does not recognize modifier-prefixed section commands (`noncomputable section`, `public section`, `@[expose] public section`, `meta section`), yet it does recognize their bare `end`. It also rejects a compound `end A.B` that closes two nested scopes. And it treats frames left open at end of file as ambiguous, although Lean closes them implicitly. Each desync clears candidate names for the rest of the file, and sometimes retroactively.

## What Changes

- Recognize section commands with optional attribute and `public`/`private`/`noncomputable`/`meta` modifiers as section frames. Anonymous `end` must then pair with the correct frame.
- Accept `end A.B…` when its components close a matching suffix of the open frame stack, including multi-component `namespace A.B`. Mismatches still fail closed.
- Retain candidate names in safe frames left open at EOF when no mismatch occurred, following current Lean 4.33 behavior.
- Make the match summary's exact and basename counters consistent with the ranked rows' `contribution` for the same query.
- Advance the lexical extraction identity, so `index update` re-extracts affected cached rows through the existing evidence-preserving path.

Acceptance is defined in `specs/ladon-lexical-scope-tracking/spec.md`.

## Capabilities

### New Capabilities

- `ladon-lexical-scope-tracking`: recognition of scope commands for lexical candidate names, fail-closed boundaries, and consistent exact-match accounting.

### Modified Capabilities

None in synchronized main specs. Lexical signature extraction (`ladon-let-signature-recovery`) and index-history ownership are unchanged.

## Impact

Affected: `src/ladon/lexical_declarations.py` scope tracking, name-search match accounting, the lexical extraction identity used by freshness/update, and the source-index cache algorithm identity. Consumers (name/type-text search, exact counts and owner projection) gain candidate names for the affected rows after one compatible update. No Lean invocation, new dependency, schema change or compiled-evidence reuse is involved.
