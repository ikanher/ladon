from pathlib import Path
import json
base=Path('.codex/state/real-native');out=Path('openspec/changes/ladon-real-bound-contracts/evidence/native-admission-20261025')
v=json.loads((base/'VERIFICATION.json').read_text());run=json.loads((base/'qualification-final/RESULTS.json').read_text())
rows='\n'.join(f"| {r['case']} | {r['loss']} | {r['status']} | {', '.join(r['goals'])} | {r['seconds']:.2f} | {r['peakRssBytes']/1024**3:.2f} |" for r in run['cases'])
report=f'''# Native Real-bound admission — task 3.1

Native real-bound-v1 records now require fresh source-bound predicate and
canonical Real scalar checks. Five final positive cases admitted, four negative
attempts remained unresolved without native artifacts, and one explicit replay
executed both checks again. This admits an interpretation of the observed
statement. It does not certify the source theorem proof, the paper-norm bridge,
mathematical falsity or unfamiliar-source discovery.

## Reachable behavior

The public plan-real-bound/admit-real-bound commands consume an exact existing
bound-prefix or derivative-prefix plan and caller-supplied proofs for both
predicate-admission and scalar-semantics. The latter compares the actual K/C
guards and output product to canonical Real functions compiled before target
commands. Original proof premises cannot discharge this scalar obligation.
All operations retain the complete ordered telescope and lexical coefficient
permissions; no declaration names or losses are hardcoded in product code.

The existing proofir.contract kind and disposable SQLite tables carry a new
closed profile/record. Native expressions are typed scoped fingerprints; full
Lean syntax and process receipts remain in bounded ordinary replay data.
Exact source-map, predicate check-run and scalar check-run owners precede the
contract. Stored provenance has checkerAuthority:none and recorded-checked.
Inspection/report always return validated-historical, authority:none and
freshCheck:false, and do not authenticate saved receipts. Optional root-aware
inspection verifies current source/environment/helper/checker identity. Replay
requires those identities and performs fresh checking. Old Nat comparison,
propagation, obligations and probe paths reject Real semantics.

## Final public operation matrix

| Case | Observed loss | Native result | Predicate, scalar | Admission seconds | Peak GiB |
| --- | ---: | --- | --- | ---: | ---: |
{rows}

The generic positives ran before the informed cases. The named-measure case
uses a dependent polymorphic telescope and a sample family distinct from the
derivative adapter. All three counterfeit Real dictionaries pass predicate
admission and fail scalar admission. The placeholder proof is rejected by the
existing no-placeholder trust policy. These are semantic check outcomes rather
than resource stops. Symbolic loss remains unsupported.

The fresh replay took {v['replayFresh']['seconds']:.2f} seconds, with a distinct
supervised worker request and peak {v['replayFresh']['peakRssBytes']/1024**3:.2f} GiB.
The cap remained 12 GiB; each admission/replay had an explicit 600-second shared
deadline, 60-second compiler phases and 8 MiB worker I/O. No cache was added.
Costs are observations of these cases, not general bounds.

## Validation and preserved history

- 322 focused/native/parent-consumer tests passed after the final production edit
  ([final-tests.log](final-tests.log)); 45 native tests include all public worker
  binder spellings and their negative API spellings.
- Eight actual CLI boundary cases rejected invalid deadlines, output collisions,
  edited source bytes or stale checker reuse. Old evidence remained readable
  offline with no fresh authority ([boundary-checks.json](boundary-checks.json)).
- All admitted artifact batches passed native validation and actual in-memory
  SQLite projection/database validation with no foreign-key violations.
- Scoped Ruff/strict complexity checks, OpenSpec strict validation, bundled/shared
  skill validation and git diff checks passed. The final wheel contains exact
  checkout bytes for the new Python modules and scalar Lean helper.
- All {v['primaryFilesUnchanged']} primary input hashes and all 445 artifacts in
  five prior frozen evidence packets are unchanged. The five historical Nat
  recognition/profile/production/formal modules in VERIFICATION.json are unchanged;
  dispatch additions preserve old native identities and consumer tests.
- The pre-existing board mismatch for test_rational_lean_encoder_v2.py remains
  outside this frontier. An import-order-only native test correction preserved
  original frozen bytes and normalized AST equality in frozen-test-lint/.

The initial public attempt passed the closed case, then exposed a native binder
enum bug on the polymorphic loss-seven case: the validator used Lean API names
instead of the worker's instance-implicit/strict-implicit protocol strings.
That failed attempt is preserved under qualification/ and its original source
identity in attempt1-INTEGRATED-IDENTITY.json. A new frozen red regression preceded
the correction; qualification-final/ is a distinct fresh attempt. No failed run
was relabelled as a pass or used to reset an inherited deadline.

Two initial independent Luna workers supplied consumer and scalar-trust findings
with peer challenges. A third worker reviewed the integrated implementation at
board post 1663 and re-reviewed the final enum correction at 1668. These are
source audits; root owns the runtime results above. See board-native.jsonl,
consumers/INVENTORY.md and trust/FINAL.md.

## Remaining scope

Task 3.1 is complete. Task 3.2 must implement explicitly checked Real comparison
and individually admitted propagation rules; the old Nat rules remain unavailable
for this profile. Task 4.1's full qualification matrix remains open. The informed
cases now have 2/2 native interpretation contracts while their paper-norm bridge
remains unresolved. No exposition fault or whole-paper correctness is established.
The parent umbrella's independent discovery/evaluation gates remain open. Nothing
was pushed.
'''
(out/'REPORT.md').write_text(report)
