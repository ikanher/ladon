# Design

## Context

`query_v3_correspondence` returns references, object maps, dimensions and child rows. SQLite already stores `record_json`, `lowered_formula`, fidelity and source references in `proofir_v3_interpretations`, and `slice_json` in the correspondence row. No canonical or projection schema addition is needed.

## Goals / Non-Goals

Deliver these existing objects together with exact owner joins and bounded output. This does not infer missing mappings, certify prose, validate untrusted projections, promote labels to proof authority or replace source-goal checking.

## Decisions

Return a `context` object containing `interpretation` and `formalSlice` components with observed/unavailable/omitted status. Observed interpretation contains the original record, lowered formula, fidelity and sourceRef; formalSlice contains the exact stored slice. Query the interpretation by both owner and local identity. Each component has an independent `max_context_bytes` allowance; inspect SQLite UTF-8 blob lengths before selecting text. Missing tables/rows and byte omissions make overall inspection incomplete. Do not truncate structured mathematical data.

Use native inspection v2 to make changed completeness semantics explicit. Keep the outer v1 envelope and persisted artifacts intact. Expose `--context-max-bytes` on existing investigation inspect, validating before either legacy or v3 dispatch; document its native-projection scope. Stable limitations explain projection-only authority, attributed source mapping and historical freshness. Reuse the existing module rather than create another semantic representation.

## Risks / Trade-offs

- Stored projections can be corrupted → no additional trust is assigned; malformed JSON remains an input error, exact owner mismatches become unavailable.
- Large context obscures the question → default 64 KiB per component with an explicit override and omission receipt.
- Consumers assume v1 native response → native schema v2 makes the change detectable; test existing consumers and outer envelope compatibility.

## Migration Plan

No migration or new dependency. Reverting query/CLI changes restores v1 inspection without changing any stored artifact.

## Stored obligation-to-check bindings

Follow-up 2026-11-16: the producer already retains planId, obligation, mode,
goalDigest, checkedGoal, status and completion receipt digests in
`ladon.correspondence-receipt/v1`. The checker rebuilds source/slice/object-map
plans and closes generated goals without ambient locals. Attach validates row
bindings. Native inspection currently hides these extensions behind check refs.

Add `checkEvidence` to the unreleased native inspection v2. Resolve each referenced
check by owner and local identity, retrieve its full stored extension only within
the allowance, and compare the producer plan convention (`correspondence:` plus
planId), obligation ID, canonical goal digest, prove/refute checkedGoal, status
and check operation against stored rows. Report `matched-stored-records`,
`mismatched` or `unavailable`; dimensions remain unchanged. This is byte-level
record consistency, not signature authentication or fresh replay.

The existing row limit also bounds checkEvidence. Its receipt payloads share a
single context byte allowance, preventing the allowance from multiplying by the
number of checks. Stored digest sentinels remain unavailable; raising the query
allowance cannot recover discarded payloads. Incomplete evidence or a mismatch
makes inspection coverage incomplete. Displayed non-open obligations without a
matching receipt are listed explicitly and also prevent complete coverage. A plan ID identifies a source/slice/map
bundle, but no new per-obligation mapping-dependency graph is inferred. Reuse
existing payloads and query helpers; no canonical/schema migration is needed.

## Mathematical reading qualification

Use actual applications in a local Lean-only project with three exposed controls.
Keep the source interpretation identical for faithful and shifted Fin-to-Nat maps,
and separately check the source proposition true; refuting the shifted route must
not become a source-falsity verdict. Use a pointwise natural-number upper-bound
theorem against a uniform interpretation to test conclusion quantifiers. Retain
full native bundles and inspect through the ordinary CLI with enough allowance.
Root writes a source/goal/check disposition from visible records. If existing
formula, map, generated goals and receipts express these distinctions, consolidate
the recipe rather than add an unmotivated graph. This does not establish reader
benefit, blind discovery or coverage of richer stochastic contexts.

## Existing MF evidence qualification

Reuse the retained inherited-order fDP countermodel and general DP-Adam source
constructor as exposed cases. Trace source spans, attributed interpretations,
object definitions, premise proofs, conclusion and source consequence. Verify
retained manifests and source-to-process binding without rerunning Lean or claiming
current donor freshness. Keep ordinary compilation, native completion and source
interpretation distinct. Test the existing receipt admission boundary before
proposing any import of ordinary compilation evidence.

The deliverable is a reproducible, hash-bound review trace and a disposition of
representation, production and delivery gaps. This review trace is not a new
ProofIR schema or accepted native evidence. Add runtime behavior only after an
actual unsupported relationship or failing existing operation is demonstrated.
A missing native artifact from an earlier ordinary-Lean audit is not, by itself,
a projection defect. The broader source audits and comparative value remain open.

## Reproduced MF inventory boundary

The actual fDP slice extracted successfully with 11034 imported modules, then
failed native correspondence production at the generic 10000-item canonical
limit. DP-Adam extraction carries 12222 modules. Extend the existing 32768-module
allowance to the two exact correspondence slice inventory paths, selected only
at the root envelope (or standalone slice during SQLite projection) and consumed
while descending those paths. List children
reset to generic bounds. This retains canonical bytes, schema versions, all
semantic validators and the 8-MiB artifact/32-MiB batch limits. No paper-specific
behavior or module omission is permitted. Root TDD and actual public alignment
reproduction qualify the fix; independent review is not claimed.

The extended-timeout checks exposed a third serialization site: native receipt
and identity hashing includes the goal capture's compiled inventory. Permit the
same bounded module list at its exact path in generated-obligation receipts and
the exact `{planId, receipt}` hash wrapper. Recognize the origin, capture schema
and operation, without recursively recognizing unrelated nested objects. This
preserves existing hash bytes and every replay/trust requirement. Test receipt
hashing directly, including overflow and attempts to escape the selected path.
