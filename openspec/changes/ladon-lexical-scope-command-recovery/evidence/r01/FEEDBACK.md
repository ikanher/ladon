# Ladon 0.3.0 lexical namespace loss in Mathlib field use

The source is GDP swarm-board work in the matrix-factorization project on 2026-10-24. The checkout is `/home/codex/projects/lean/matrix-factorization`; the companion index is `.ladon/index/mathlib-proof-search.sqlite`; the Mathlib revision is in `mathlib-rev.txt`, and the Ladon version is in `ladon-version.txt`. Only read-only queries and direct SQLite reads (`mode=ro`) were used. No index writes or Lean were run.

## Symptom

Ladon-first discovery with fully qualified names returns zero rows for some existing Mathlib theorems, while other theorems in the same namespace are found.

| Query (`search name --query-mode phrase --freshness stored`) | Result |
| --- | --- |
| `Real.exp_one_lt_d9` | 1 qualified exact match (`Mathlib/Analysis/Complex/ExponentialBounds.lean:38`) |
| `Real.exp_bound_div_one_sub_of_interval` | **0 rows**: no exact match and no lexical suggestion |
| `Real.add_one_le_exp` | **0 rows** |
| `exp_bound_div_one_sub_of_interval` | the row is found (`Mathlib/Analysis/Complex/Exponential.lean:618`, `namespace: "Real"`, `ranking.contribution: "exact"`), but `candidateName: null` and `matchSummary.exactMatches = basenameExactMatches = 0` |
| `add_one_le_exp` | same pattern, at line 633 |

The full JSON outputs are in `name-*.json`. There are two consumer-visible defects:
1. A qualified query misses the declaration entirely, without even a basename suggestion.
2. The match summary reports zero exact or basename matches while the ranked row says `contribution: "exact"`.

In the same session, several swarm workers recorded "name search returned no candidates (not semantic absence)" and fell back to `rg`. Board posts #945, #948, #1009 and #1010 show this: Ladon-first discovery is losing its value on exactly the kind of library lemmas agents most often need.

## Scale (companion index, read-only)

- 240,583 declaration rows; **8,024 (3.3%)** have `candidate_name IS NULL`, and 7,450 of those have a non-empty recorded `namespace`. They are spread over 294 files.
- The project (Mf) indexes have only about 200 null rows each. Project code rarely uses the triggering syntax.

## Root cause (source reading of `src/ladon/lexical_declarations.py`)

`_SCOPE_COMMAND_RE = ^[ \t]*(namespace|section|end|mutual)\b...` recognizes scope commands only when the keyword starts the line. Three Lean 4 / current-Mathlib forms then desynchronize the frame stack. After desync, `permanently_unresolved` or `_invalidate_unbalanced_scope_rows` clears candidate names for the rest of the file, or for everything inside the first unclosed frame, which can include earlier rows.

1. **Modifier-prefixed section openers are not frames, but their bare `end` is.** Current Mathlib contains `@[expose] public section` (4,956 occurrences), `public section` (2,721), `noncomputable section` (1,271), `public meta section` (308), `meta section` (49) and similar. A bare `end` closing a `noncomputable section` pops the *enclosing namespace* frame, and the following `end Ns` then finds an empty or mismatched stack.
   - Example: `Mathlib/Analysis/Complex/Exponential.lean`. The bare `end` at :68 closes a `noncomputable section`, but the extractor pops `namespace Complex` (:35) instead. `end Complex` at :70 then meets an empty stack, which sets `permanently_unresolved`. Every later row in the file loses its candidate name, including `Real.exp_bound_div_one_sub_of_interval` (:618) and `Real.add_one_le_exp` (:633). Rows before :70 keep theirs.
2. **A compound `end A.B` closing two nested scopes.** Lean 4 accepts `section IsInducing` + `namespace IsInducing` … `end IsInducing.IsInducing`, and `section MonoidWithZero` + `section LinearOrder` … `end MonoidWithZero.LinearOrder`. `_close_scope_frame` requires `body == top.name` and fails closed. Frames then stay open at EOF, so rows are invalidated *retroactively* from the first unclosed frame.
   - Examples: `Mathlib/Topology/Maps/Basic.lean:189`, with rows from :62 nulled; `Mathlib/Algebra/Order/GroupWithZero/Basic.lean:718`, with rows from :374 nulled.
   - By the same logic, `namespace A.B` is pushed as one frame named `A.B`, so a later `end B` / `end A` pair would also fail. This is not yet confirmed against Lean's scope semantics.
3. **Frames legitimately left open at EOF.** Lean closes open sections and namespaces at end of file. `_invalidate_unbalanced_scope_rows` treats any EOF-open frame as ambiguous, even when every command was matched. Among the 294 affected files, 33 show no mismatch under the current recognizer. They carry 237 null rows: 169 lie inside EOF-open frames, and 68 have no cause identified here. Examples: `Mathlib/Topology/Order/OrderClosed.lean` (`section ClosedIciTopology`) and `Cache/Infra.lean` (`namespace Cache.Requests`).

## Prototype estimate (not a fix)

A throwaway recognizer was run over the 294 affected files with comments masked. It accepted optional `@[...]` and `public/private/noncomputable/meta` prefixes, treated `end A.B` as closing matching trailing frames, and split `namespace A.B` into components. The result:
- 257 files that desynchronize today become balanced.
- Those files hold **7,888 of the 8,024** null rows.
- 4 files still fail; the remainder fall under cause 3.

This was a regex simulation outside Ladon, not a test of Ladon code.

## Not claimed

No Ladon code was changed or executed beyond the installed CLI's read-only queries. The prototype counts are an estimate. Whether EOF-open frames should be trusted (cause 3) is a design decision, recorded in `design.md`.
