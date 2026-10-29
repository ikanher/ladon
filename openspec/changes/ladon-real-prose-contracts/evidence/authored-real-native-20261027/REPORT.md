# Attributed native Real records — Task 2.1

Ladon now produces a separately versioned native Real reading from fresh,
source-bound recognition. The public producer takes an interpretation, selected
context, alternative ID and author. It observes and checks the input again;
it accepts no caller-supplied admission or feature projection.

The new `real-bound-prose-v1` record retains global or explicit set scope, the
complete telescope, all guards, coefficient permissions, original-expression
subjects and input/output/coefficient-guard origins. Its exact source-map and
interpretation owners come from the observation already retained by recognition.
Batch validation requires full artifact equality, including byte/column ranges.
It reconstructs features and subjects from the retained observation rather than
trusting content hashes or caller labels.

Admission stays unresolved, fidelity stays attributed-unreviewed, native
checkerAuthority stays none and checkRunRefs is empty. This is an attributed
reading with checked arithmetic syntax, not an admitted predicate, a proof of
the estimate, a formal connection or detection of an exposition fault.

See [the public workflow](../../../../../docs/REAL_PROSE_NATIVE.md),
[the frozen engineering contract](CONTRACT.md), [source snapshot](runtime/),
and [verification](VERIFICATION.json).

## Native transport and custody

Direct embedding would conflict with native ProofIR's depth-64, integer-only
scalar and single-string limits. The new closed history codec stores the exact
ordinary JSON observation in ordered ASCII chunks no larger than 64 KiB. It
checks aggregate length/digest, canonical partition/text, duplicate keys,
finite numbers and nesting before semantic reconstruction. It applies neither
a native safe-integer bound nor rounding to opaque historical Nat/float values.
No decompression or global native bound change is used.

A feasibility capture measured the complete selected escaped native artifact
and supervised worker output at about 5.74 MB, below the unchanged 8 MiB cap.
This measurement used earlier history only and receives no fresh checking
credit. Actual fresh production and replay are qualified separately below.
The saved native artifact retains the entire recognition, including exact
proposition, context, kernel equality goals/terms, inventories and receipts;
there is no digest-only success stub.

Content hashes establish identity and integrity, not authenticated execution or
authorship. Coordinated rebuilding with a new author/alternative produces a
new attributed identity. Two alternatives may coexist; changing a field alone
or mixing owners is rejected. Inspection/reporting return authority none,
freshCheck false and evidenceAuthentication not-established. Root-aware
inspection additionally checks current source/runtime/toolchain/import custody;
it does not replay Lean.

Production and replay run recognition, native construction and final custody
checks under one outer deadline and RSS/output caps. Prior-history validation
on replay is inside that supervisor. Nested observation/recognition scratch is
owned by the outer temporary directory, so timeout cleanup removes it.
No timeout or memory retry increases a cap or resets the clock.

## Verification

Initial codec and native integration: 18 tests passed. Public command integration:
21 tests passed. Expanded owner, scope, codec, report, missing-guard, timeout and
SQLite cases: 32 tests passed. Independent source review then found an unknown
stopped-status label accepted by historical validation. Root reproduced it as
an expected failing assertion, restricted stopped states to rejected/incomplete,
and passed the new regression.

The final native suite includes 33 new checks and 29 old native/provider
compatibility checks: **62 passed in 157.68 seconds**. SQLite checks cover full
canonical artifact and record/provenance preservation, export/rebuild, foreign
keys, the existing source index and rollback after injected projection failure.
No database schema migration or new index was necessary.

New authored contracts are rejected by existing Nat comparison, propagation,
application-probe and source-provider entry points, and by the extracted Real
record validator. The source-provider boundary now rejects unsupported profiles
before consuming their fields. Native ProofIR inspection has an explicit
authored-profile summary; reporting does not manufacture admission or proof
authority. The unchanged older observation/recognition regression suite is
recorded separately in REGRESSION-91.txt: **91 passed in 371.28 seconds**.
The final two suites therefore contain 153 passing checks in total.

Scoped Ruff, strict_quality_issues, compileall, child/parent OpenSpec strict
validation and whitespace checks are recorded in the packet. This is scoped
qualification; the full repository/release suite is not claimed.

The codec acceptance file remains frozen unchanged. Two newly authored frozen
acceptance files received an independently reviewed helper-only quality
refactor, preserving all 27 assertion ASTs and every case. Original red versions,
patches, proposed copies, hashes and explicit board supersessions remain in
quality-proposal/. No assertion or case was weakened. The whole board still
reports one unrelated older rational-encoder mismatch, already matching HEAD
before this work; this task neither edits nor clears that baseline mismatch.

## Public Mathlib qualification

The selected reading, unrelated global/set estimates, and incorrect coefficient
alias use actual Mathlib Real under their existing pinned Lean 4.34.0-rc2
contexts. The procedural test fixture deliberately uses a Nat-backed type named
Real under Lean 4.32.1; that fixture establishes ownership/execution controls
only. Counts and process measurements for the actual Mathlib matrix are in
VERIFICATION.json and live/*-process.json.

| Actual Mathlib operation | Outcome | Seconds | Peak tree RSS |
|---|---|---:|---:|
| Selected production | Authored, global / loss 4 | 59.08 | 5.13 GiB |
| Selected current-source inspection | Historical, no fresh check | 5.64 | 0.10 GiB |
| Selected fresh replay | Authored, global / loss 4 | 67.61 | 5.18 GiB |
| Unrelated global | Authored, loss 5 | 17.54 | 3.45 GiB |
| Unrelated set-indexed | Authored, loss 7 | 17.12 | 3.45 GiB |
| Incorrect coefficient alias | Unresolved, no native contract | 16.43 | 3.46 GiB |

These represent three distinct authored readings, one unresolved reading and one
fresh selected replay; inspection and replay are not additional mathematical
successes. Zero semantic admissions and zero formal connections were emitted.

All public operations share one 600-second absolute clock with 12 GiB RSS and
8 MiB output caps, including selected production, historical inspection, fresh
replay and generic controls. The original selected interpretation, symbol map
and proposition are retained unchanged. Its prior explicit source relocation
is preserved; source-fidelity review is not inferred from the transport.

## Independent review and remaining work

Luna scouts independently mapped consumers and proposed falsification controls.
A separate green worker proposed only the history codec; root inspected,
corrected and integrated it. Root authored production integration and every
Lean/test/SQLite execution. An independent auditor reviewed the exact 24-file
production revision, reported the malformed-status issue and approved the
assertion-preserving test refactor (1943). After the fix it verified all final
hashes and found no additional source/documentation issue (1947).
An evidence follow-up (1950) confirmed the public receipts and noted missing
explicit RSS/size assertions in the verifier. Root added those assertions and
reran verification successfully without changing production code.
The first audit start event was omitted and explicitly recorded without
backdating (1944); the renewed audit has a proper start event (1946).
Reviews are source/evidence review, not independent runtime executions.

VERIFICATION.json checks protected primary files and all earlier sealed
source-pair, norm, proposition-feasibility, observation and shape-recognition
evidence unchanged. New code adds no dependency, cache, paper edit, theorem
placeholder, commit or push.

Task 2.1 covers attributed record production, persistence, reporting and
consumer boundaries. Checked connections to formal contracts remain Task 2.2;
final source-pair qualification and both skill updates remain Task 3.1.
The parent propagation and unfamiliar-source discovery gates remain open.
No predicate admission, mathematical falsity or discovery benefit is credited.
