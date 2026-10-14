# Closed profiles and field qualification

The lowering-integrity and context-transport specs own these profiles.

| Surface | Current write/check profile | Historical read boundary |
|---|---|---|
| Lowering | `typed-operators-v2`; each named operator is annotated with its declared type at application use | Missing native `loweringProfile` means `untyped-operators-v1`; validate its original lowering without relabeling it |
| Prepared plan | `ladon-correspondence-plan-v2`, explicit `loweringProfile` | Old plans need fresh preparation/checks/reviews before receiving current guarantees |
| Scoped extraction | `scoped-identity-transport-v2` | Prior `scoped-local-argument-v1` and declaration-only observations remain structural historical inputs; fresh extraction identity must match for checking |
| Object map | `local-identity-v1`, entries keyed by observed original fvar identity | Raw display-name maps resolve only when each selected local is unique; absent/ambiguous references reject |
| Compiler transport | `fvar-substitution-v1`, dependent substitution in ordered live Lean context | No display-name rewriting substitutes for this profile |
| Work blockers | `work-blockers-v1`, exact current queue-item digest | No arbitrary hidden queue items; policy-limited scopes remain unverified |
| Terminal receipt | `ladon-investigation-progress-v1` | Historical identity validation uses its recorded time, and never grants current termination authority |

Unknown closed profiles reject. Native artifacts and check receipts are stored
observations, not authenticated fresh compiler authority. New typed checks bind
actual elaborated expression DAGs and operator/operand types into their check
receipt; independent prose review remains separate. An interpretation P → P
check demonstrates typing and supplies no proof of P or prose fidelity.

Finite bounds remain: 4096 interpretation nodes/symbols/map entries, depth 64,
1 MiB individual text/Expr encodings, 8 MiB generated source/process output/frame,
60-second per-process timeout, 32 GiB per-process RSS, 16 supplied attempts,
32 MiB complete compact public bundles and structured investigation plans.
The typed operator fragment excludes dependent application signatures;
unsupported interpretations retain residuals. Compiler limits are enforced by
existing capture/completion/supervisor paths. Budget 90 minutes is a workflow
clock, not a compiler timeout.

Observed minimized red tests: portable Rat/Nat numeral-only semantics,
identity-keyed Unicode transport, premature public finalization, complete
near-cap public output and nested-module sibling-import shadowing. Board
artifacts 395/396/398/399 and replacements 401/402/403 preserve test provenance.
Replacements changed import formatting only; exact originals and non-import
AST equality are recorded in `test-format-supersession.json`.

Measured qualification remains design/work-packages C: cone six, corrected
numeric six, adjacent-derivative eight goals; three paired trials each, no
concurrent full build. Exact plans/terms and command/timing files are under
`real-cases-attempt03/`. These preliminary correctness replays do not yet satisfy
the paired benchmark gate. Freeze a corrected source snapshot and all commands
before optimizing, then disclose stage/process/resource/output accounting.
Required median gain is at least 30% for cone and regression at most 10% for each
other workload. No failure, unattempted goal or trust check may be dropped to
meet the gate. The helper/context reuse feasibility limit is 20 engineering
minutes; failure leaves execution tasks open and retains the safe route.

Request preparation now declines source text containing a `local` or `private`
keyword (including comments, conservatively). Every admitted reused obligation
still observes its closed proposition in the original copied source. Its exact
structural expression must equal Lean's separately captured prepared goal before
proof completion; a mismatch remains unresolved with
`prepared-goal-subject-mismatch`. This checks proposition identity per goal,
without asserting equality of all command, notation or tactic state.
