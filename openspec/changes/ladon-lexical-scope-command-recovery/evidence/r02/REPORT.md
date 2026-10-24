# Lexical scope recovery qualification

The implemented v6 lexical extractor reduces missing candidate names in the
pinned Mathlib companion population from **8,024 to 119** out of **240,583**
declarations. It recovers 7,905 rows (98.5% of the previously missing names).
Both reported failures, `Real.add_one_le_exp` and
`Real.exp_bound_div_one_sub_of_interval`, now return one qualified exact match
through the public CLI. The control `Real.exp_one_lt_d9` remains exact. All
three CLI receipts report a fresh index.

## Behavior and migration

Section commands recognize exposed attributes and the supported `public`,
`private`, `noncomputable` and `meta` prefixes. Namespace and section names are
split into components at dots outside escaped identifiers. Compound ends must
match the trailing frames; malformed names and unknown prefixes fail closed.
Safe open frames close implicitly at EOF under the accepted Lean 4.33 rule.
Unsafe mutual blocks and inconsistent scope sequences remain unresolved.
`noncomputable namespace` is rejected under the current grammar.

ASCII basename counters now include rows whose candidate name is NULL,
matching the ranked exact-row predicate. Counter scope remains the selected
indexed population, which can exceed a bounded returned result set.

Proof-search extractor v6 refreshes v5, v4 and v3 indexes without source edits.
Regressions check archived retained evidence and subsequent byte-stable no-op
updates. The separate source-index algorithm advances from 5 to 6 so its module
cache also re-extracts names. Its context-completeness status retains its
separate conservative EOF behavior.

## Verification

- Frozen scope regressions before implementation: 8 failed, 11 controls passed
  ([red log](red.log)). Additional malformed-command/section controls: 5 failed,
  3 passed ([log](invalid-red.log)). The frozen cache regression fails under the
  v5 producer identity ([log](source-cache-frozen-red.log)).
- Private replay of the three reported owners: **490 missing names to zero**,
  with the same 548 declaration rows. [Before](baseline.json),
  [after](recovered.json).
- Full disposable Mathlib rebuild: **72.96 seconds**, sampled process-tree RSS
  peak **80.35 MiB**, no swap, no cgroup OOM event. The build stayed within its
  600-second/1-GiB bounds. [Resource receipt](full-mathlib-build.json),
  [build and queries](mathlib-after.json), [baseline](mathlib-before.json).
  These measurements are observations, not a controlled performance comparison
  with the earlier feedback run.
- **248 affected contracts passed** in 6.22 seconds, covering lexical scopes,
  signatures, source indexing, name/type queries, history/update/publication and
  CLI contracts. [Log](contracts.log), [verification](verification.json).
- Repository Ruff, changed-file strict quality, compilation, diff whitespace
  and strict OpenSpec validation pass. All three new frozen test hashes match
  their board records ([freeze evidence](frozen-tests.json)).
- Independent Luna audit found no material issue in either the scope/count/
  migration change or the additive source-cache invalidation. Board reviews
  #1460 and #1462 retain the reviewed surface and bounded test commands.

The full repository strict gate was not rerun for this packet. The earlier
49-minute full run and its live sibling source-identity failures remain under
the proof-contract umbrella; this report does not close that umbrella gate.

## Remaining lexical limits

The 119 remaining unresolved rows occur in 24 modules: 98 are in unsupported
mutual blocks, 15 are under `namespace $typeName` in a generated command
template, and 6 occur in whitespace-linter command quotations with syntax such
as `end)`. [Residual rows](mathlib-after.json) and
[scope events](residual-scope-events.json) preserve the observations. These
classes remain outside the supported lexical subset.

The rebuild wrote only a disposable index under ignored task state. Existing
sibling indexes and mathematical sources were not modified. Candidate names
retain lexical authority; this work does not add compiler-generated declaration
coverage or elaborated types. Nothing was committed or pushed.
