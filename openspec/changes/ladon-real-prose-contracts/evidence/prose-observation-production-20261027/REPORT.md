# Public typed prose observation — Task 1.2

## Result

The current checkout now provides a public producer for an attributed proposition
in a pinned Lean source context. It captures the proposition's **value**, without
requiring or asserting a proof, and preserves exact source/context ownership.
The frozen Navier interpretation successfully passes public observation,
current-source historical inspection, and explicit replay.

The operation records `authority: syntax-only`, `fidelity: attributed-unreviewed`,
`admission: unresolved` and `contract: null`. Only existing native source-map and
interpretation artifacts are emitted. This establishes typed proposition capture,
not native Real feature recognition, source fidelity, admission, formal connection,
mathematical refutation or a whole-paper audit.

## Public behavior

See [the user guide](../../../../../docs/REAL_PROSE_OBSERVATION.md) for input
schemas and complete commands. Run from the current checkout with `PYTHONPATH=src
.venv/bin/python -m ladon.entrypoint`.

- `investigation contract observe-prose-bound --interpretation RECORD --context
  REQUEST --root ROOT --output FILE` captures the exact lowered proposition.
- `investigation contract inspect --input FILE [--root ROOT]` validates saved
  history with `authority: none` and `freshCheck: false`. A root additionally
  checks current source, runtime, toolchain and compiled-module identities.
- `investigation contract replay-prose-bound --input FILE --root ROOT --output
  FILE` performs a fresh supervised observation after validating the original
  snapshot and its current context within the same deadline.

Successful syntax capture exits 0; malformed, unsupported, unavailable and
resource-stopped operations exit 2. Existing output files are preserved. Old
formal shape-observation exit semantics and historical profiles are unchanged.

## Implementation

The [frozen runtime source snapshot](runtime/src/ladon/real_prose_observation.py)
and other new `real_prose_*` modules own a closed context request, bounded worker,
source preparation, exact expression validation, historical inspection and public
command dispatch. The context file is recompiled with a generated root-scoped
`def : Prop`; the helper reads its value and verifies local ownership/type.
There is no theorem selector, new axiom, `sorry` or placeholder proposition.

The Lean renderer checks its 100,000-node/128-depth budget before descending into
an expression. Typed binders, levels, de Bruijn scope and constructor shapes are
preserved and validated independently of display text. Malformed non-object
worker JSON is rejected explicitly. Source/helper/runtime/toolchain identities
are checked around execution. The conservative implementation identity covers
all shipped Python/Lean files; unrelated runtime changes can therefore require
fresh observation. This is a deliberate freshness restriction, not a cache.

Successful capture observes twice, with exact loaded-module and sidecar inventory
checks around the second observation; their output must match. Preparation and
Lean descendants run under one supervised operation deadline and configured RSS
cap. Replay freshness is inside that same supervised job, with its clock starting
before historical validation. Memory exhaustion uses the existing stop-and-report
message and never automatically retries. Requests and worker outputs retain their
8 MiB caps; default RSS is 12 GiB and callers can explicitly configure the cap
within the ordinary shared validation limits.

## Verification

**42 focused tests pass on the final revision** in 137.69s: 29 new observation
and boundary cases plus 13 existing prose/CLI/Real-observation checks. They cover
an actual false proposition, ill-typed and opaque readings, source/context changes,
rehashed tampering, compiled-context changes, historical inspection, explicit
replay, actual depth exhaustion, owner substitution, configured caps, simulated
memory/timeout/output stops and old semantic-consumer rejection.

The frozen acceptance file retains all 12 cases and 25 assertion ASTs. Before
implementation, one expected message article was corrected to match the shared
resource diagnostic; both versions are retained. The later independently reviewed
quality refactor extracted existing assertions into a helper, preserving all
conditions and cases. Board supersession records preserve both earlier paths.
No existing repository acceptance test was weakened. Earlier development failures
and the source-audit findings remain in the packet; they are not counted as
passing checks.

Scoped Ruff, `strict_quality_issues`, compileall, OpenSpec strict validation and
whitespace checks pass. The quality wrapper's full-suite mode was deliberately
not invoked; whole-repository/release qualification remains Task 3.1.

## Informed public qualification

| Final operation | Outcome | Seconds | Peak process-tree RSS |
|---|---|---:|---:|
| Observe selected interpretation | Observed, syntax only | 32.64 | 5.07 GiB |
| Inspect against current source/context | Validated history, no fresh check | 3.79 | 0.04 GiB |
| Replay selected interpretation | Observed, syntax only | 36.55 | 5.10 GiB |

These are one selected source case with separate observation/inspection/replay
outcomes, not three independent mathematical successes. The final typed
propositions agree exactly. Final process time totals 72.98s; sampled peak is
5.10 GiB. All public attempts, including the earlier 33.26s intermediate capture,
shared the original 600-second qualification clock and 12 GiB cap. There were no
resource stops or clock resets. That intermediate capture predates the replay
fix and is preserved as superseded evidence, with no final-runtime credit.

The selected formula and symbol map are unchanged. Its source text was copied
with identical content/span into the isolated Lean project, with only the
interpretation ID and relative source path changed explicitly; [the relocation
record](live/RELOCATION.json) binds the original owner. No prior source-fidelity
review is silently transferred to this new observation.

[VERIFICATION.json](VERIFICATION.json) checks 2,670 primary files, 67 prior source
pair files, 34 norm-bridge files and 41 proposition-feasibility files unchanged.
Of 610 pre-existing runtime files, 609 are unchanged and only the CLI dispatcher
was edited; seven Python modules and one Lean helper were added. The source
module was loaded from this checkout, not the installed package. No dependency,
cache, original source, theorem proof, commit or push was introduced.

## Independent review and remaining gate

Luna workers provided a red-test proposal and an isolated helper proposal; root
integrated and executed the code. Final independent source reviews are at board
posts 1896 and 1898, with checkpoint hashes matched. Their reports are in
[reviewer/FINAL-AFTER-FIX.md](reviewer/FINAL-AFTER-FIX.md) and
[reviewer/FINAL-AFTER-REPLAY.md](reviewer/FINAL-AFTER-REPLAY.md). Reviewers did not
rerun Lean or tests. Review led to broader implementation-identity coverage;
root also fixed malformed worker JSON and the replay deadline boundary. An early
RSS finding was withdrawn after distinguishing the configured cap from the
12 GiB default/qualification cap; its history is preserved.

Task 1.2 is complete. Task 1.3 remains next: separately versioned global/set-indexed
recognition and checked alias normalization. Native authored Real records and
checked formal connections are later tasks. Parent Task 2.1 and the propagation,
source-qualification and discovery-benefit gates remain open.
