# Integrated correspondence capability

The implementation connects source-bound prose interpretations to actual Lean
application slices, generated correspondence obligations, bounded replay, native
ProofIR evidence and immutable independent review. The constructed comparative
pilot found **no detection or cost benefit**: both arms localized three justified
faults and correctly assessed four controls; assistance used more wall time.
Autonomous detection of the historical exposition issue remains unestablished.

The final production revision passed the default strict quality gate:
**3,415 tests passed, zero failed, zero skipped**, including 153 correspondence
and source-goal consumers. Quality, lint and compilation were clean. Independent
source audits closed the database and native CLI findings, with no further
actionable issue. Final OpenSpec task closure and validation are recorded below.

## Implemented path and scope

Packages A/B establish an actual selected application and one complete portable
positive/negative correspondence through the ordinary CLI. Package C preserves
bounded local contexts, providers, all ordered proof premises, branches and
witness ownership. Conditional validity, premise/provider establishment, parent
support, prose fidelity and method correspondence remain separate outcomes.
Package D reuses the same native subjects through investigation v3, sanitized
challenges, immutable first responses, separate corrections and completion queues.
V1/v2 remain available; unsupported Rust kinds fail explicitly.

The source guide is [NL_LEAN_CORRESPONDENCE.md](../../../../docs/NL_LEAN_CORRESPONDENCE.md).
Detailed accepted mechanism evidence remains in
[M1 acceptance](M1-ACCEPTANCE.md) and [C/D qualification](CD-QUALIFICATION.md).
The final source-only audits and root reconciliation are preserved in
[the integration evidence](integration/source-audit.json), alongside the two
meaningful migration reds, final 75-consumer receipt and repository-relative
source identities. The final default strict [receipt and totals](integration/final-gate-summary.json),
[log](integration/strict-final5.log) and [JUnit cases](integration/strict-final5-junit.xml)
preserve actual execution after the final production edit and source audit.
The fresh evaluation and source/key qualifications are in
[E-PILOT.md](E-PILOT.md), with a versioned source-first snapshot and frozen scoring
harness. Passing implementation tests is separate from the unmet benefit result.

The final implementation inventory is
`.codex/state/nl-lean-c/final-production-native-choices.json` (artifact 364):
40 production/document owners, two new frozen migration regressions and the
actual pre-change v8 SQL input. Earlier inventories were explicitly superseded.
The first final inventory omitted native schema owners; independent audit caught
that coverage gap, and all relevant source identities were added without changing
the code or granting missing test authority.

## Final integration changes

Parser construction now lives in `proof_search_parser.py`, with the previous
parser symbols re-exported from `proof_search_cli.py`. Entry-point routing retains
lazy imports, and rational-witness helpers retain validation/error order and exact
arithmetic. These changes resolve repository-wide complexity failures without
changing command contracts or proof semantics. Private pre-integration probes
matched 12 parser cases/help output and 187 rational outcomes/errors; root's final
57 entry-point/parser/legacy consumers passed. The entry-point and rational
staged bytes still match their integrated versions. The parser subsequently
received the native choices from its public CLI wrapper, as described below;
the earlier equivalence probes are evidence for that earlier revision.

The next actual full strict gate passed 3,414 tests but failed one existing
source-inspection assertion: extracting the parser had removed native mode
declarations from `proof_search_cli.py`. Root preserved that assertion and its
red receipt, restored the authoritative nine evidence kinds in the CLI, and
passed them to the extracted parser factory. The strings now determine actual
accepted choices; they are not inert additions for the test. The public CLI
builder remains nullary, its parser-class alias remains the same class, and the
original two-name `__all__` remains once. All 121 changed-parser, native CLI,
source-goal, semantic, discovery and entry-point consumers passed after the
final edit. Only those two source owners changed from artifact 362; the other
41 identities, including the database fix, remain unchanged.

The independent audit also found an actual schema lifecycle defect: an existing
v8 projection could be stamped v9 while retaining its older artifact-kind CHECK.
Root reproduced seven failures against an actual HEAD v8 SQL fixture, alongside
two valid controls, before freezing the new regression. `create_v3_schema` now
checks the existing owned artifact table's normalized definition before any
schema/metadata mutation, rejecting stale or relabeled definitions with an
explicit disposable-rebuild diagnostic. Standalone unrecognized nonzero versions
are rejected; current embedded projections preserve their owner's global version.
This is an explicit rebuild policy, not an in-place migration. Tables with a
different SQL definition also require rebuilding.

All 75 migration, version-owner, native-projection and embedded index-history consumer tests
passed after the guard edit. Old data, table definitions and version metadata
remain unchanged on rejected creation/projection. Fresh/current creation remains
idempotent. Root retained the failed filename-only test invocation separately;
it provides no test credit. The initial broad source audit is stale for the
changed schema owner; the same independent auditor reviewed the fix against the
new source barrier. The follow-up review caught a missing standalone-version
check when no native table existed; root reproduced four failures and one valid
embedded control before freezing the additional regression. Version validation
now precedes that early return, preserving unrelated owner data/version on
rejection. This supersedes the earlier guard-only source barrier. Final source
audit 321 confirmed all 43 source identities and found no remaining actionable
defect in the requested standalone and embedded version cases. The auditor ran
no tests; root owns the 75 consumer checks and final full suite. Its stale
report-reference observation was reconciled in root post 322; the live report
already used the final manifest and assignment.

The user explicitly approved the three-file helper-only frozen-test refactor
(65 assertion ASTs retained; 41 checks passed), and the additional four-file
lint-only patch (18 assertion ASTs retained; six checks passed). Original bytes,
exact reviewable patches and explicit supersessions remain on the board. Earlier
two authorized test corrections and their red receipts also remain preserved.
No frozen assertion was weakened to close a gate.

## Verification evidence

| Gate | Current evidence and disposition |
| --- | --- |
| Root default strict quality | [Final receipt](integration/final-gate-summary.json); default `src tests scripts` quality/lint/compileall clean; 3,415 passed, zero failures/errors/skips, 1,106.59 pytest seconds (1,117.61 total seconds) |
| Final SQLite consumers | `.codex/state/nl-lean-c/schema-owner-green.json`; 75 passed after final owner-guard edit |
| Final CLI/parser/legacy consumers | `.codex/state/nl-lean-c/final-refactor-focused.json`; 57 passed after factoring |
| Final native choices consuming path | [Final consumer receipt](integration/native-cli-owner-green2.json); 121 passed after final choices/alias edit |
| Final public application extraction | `.codex/state/nl-lean-e/root-replay/fresh-slices/commands-qualified.json`; all eight exact terms/ordered arguments/local contexts match |
| Pilot original goals/refutations | Versioned [36 replay receipts](pilot/root-replay-receipts.json); 28 accepted, eight expected rejections; no retroactive first-response credit |
| Frozen comparative scoring | `.codex/state/nl-lean-c/score-reproduction.json`; aggregate exactly reproduced from 16 versioned rows; five scoring-contract controls pass |
| Independent broad source audit | Board 311; source, test authorization, contracts and E counts reviewed; migration defect 309 held acceptance |
| Independent fix reviews | Assignment 320 / source-only audit 321 against artifact 362 closes database defects; root reconciliation 322. Final CLI source-only audit 325 against artifact 364 found no further actionable issue; root launch 326 |
| Source/target preservation | [Final preservation receipt](integration/preservation.json); 399 original files present; only authorized source/task changes; external source/report bytes unchanged; all 43 final owners match after the full suite |
| Frozen artifacts | `.codex/state/nl-lean-c/artifact-verification-final.json`; all current artifacts match or explicitly superseded |
| Strict OpenSpec | [Final validation receipt](integration/openspec-final.json); strict validation passed before 6.3 closure and again after all 27 tasks were checked; apply instructions confirm `all_done` |

The accepted scoped/resource/real-source receipts are reused only where exact
relevant inputs and semantic implementation bytes remain unchanged. The guide's
added Unicode/binder limitations and legacy parser factoring do not alter those
Lean/helper obligations. The migration edit requires the fresh database consumers
above. The real-source development result remains conditional/provider support
for a one-dimensional datum, with physical/object/quantifier transfer unresolved;
it is not detection of the historical fault.

Previous full gates remain historical: revision 3 passed 3400 checks but failed
global complexity; the first default final gate failed lint before pytest; the
second was explicitly interrupted at 437.35 seconds after the audit found the
schema defect. The next run was stopped at 109.27 seconds for the additional
version-owner correction. Final4 then completed with 3,414 passes, one native
CLI source-inspection failure and zero skips in 1,100.11 pytest seconds
(1,111.13 total seconds); its failing assertion remains unchanged. None is a
complete pass for the final revision. Final5 completed after both final edits
and the independent re-review. Every required Lean-backed test executed; the
JUnit receipt contains zero skipped cases. All 43 production/input identities
still matched after the full run. Previous gate failures remain preserved in
[the gate dispositions](integration/final-gate-dispositions.json).

## Limits and reproducibility

Extraction observes bounded elaborated application/context/provider fragments,
not every source step or an entire analytic proof. Prose meanings, object maps
and method identity are attributed inputs; Lean checks encoded original goals,
not author intent. Missing counterparts, unsupported syntax, uncertain readings,
unexpanded providers and exhausted bounds remain explicit. Process, expression,
depth and output bounds retain cleanup and frontier behavior.

The pilot exposed two practical gaps: Unicode-subscript locals can block mapped
transfer, and callers can submit tactics that introduce the wrong generated
binders. The guide now explains both. Three assisted full-pipeline attempts
retained unresolved parent links; their correct mathematical judgments did not
silently promote those links to checked correspondence. The pilot's calibration
key and alternative-method control also needed source qualification. General
analytic passage detection and incremental audit benefit require further work.

Run from the current Ladon directory, with the current source import explicitly
set. Use a fresh output directory for each executable example:

```sh
PYTHONPATH="$PWD/src" .venv/bin/python scripts/demo_correspondence.py \
  --output .ladon/new-portable-correspondence
PYTHONPATH="$PWD/src" .venv/bin/python scripts/demo_correspondence_review.py \
  --output .ladon/new-scoped-review
PYTHONPATH="$PWD/src" .venv/bin/python scripts/python_quality.py --strict
openspec validate ladon-nl-lean-correspondence-umbrella --strict
.venv/bin/python openspec/changes/ladon-nl-lean-correspondence-umbrella/evidence/pilot/score.py \
  openspec/changes/ladon-nl-lean-correspondence-umbrella/evidence/pilot/normalized-first.json \
  .ladon/pilot-score-reproduced.json
```

The Lean examples require the existing pinned Lean 4.32.1 environment. Example
reviewer labels are attributed demo output, not verified independent identities.
The stored pilot snapshot can reproduce scoring; it cannot recreate unseen
auditor contexts, and its exposed cases cannot be reused as fresh inputs.
No full-paper rerun, archive, release, commit or manuscript change is part of
this implementation.
