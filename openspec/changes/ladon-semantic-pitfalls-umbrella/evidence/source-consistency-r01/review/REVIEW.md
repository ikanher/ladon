# Independent review: exposed source-consistency recipe qualification

Reviewer: Codex, independent review agent (attributed to `/root/source_consistency_recipe_review`)
Reviewed: 2026-11-12
Scope: exposed scalar qualification artifacts and the three requested recipe/skill passages. Review-only; no Lean or tool tests run.

## Decision

Accept the bounded supplied-obligation qualification. I found no mathematical or reporting error requiring correction. This acceptance does not validate the correspondence of the rational fixtures to the PLD probability source, establish formula discovery, or certify a finalized Ladon investigation.

## Goal / assignment / status reconciliation

I reconciled the four registered case IDs and their exact AST goals, assignments, retained outputs, and RUNS.json status fields:

| ID | Exact conclusion | Assignment | Premises and conclusion in retained output | Review |
|---|---|---|---|---|
| `inverse` | `x = a*y`, premises `a>0`, `x>0`, `y=a*x` | `(a,x,y)=(2,1,2)` | All premises true (`2>0`, `1>0`, `2=2`); conclusion `1=4` false; `counterexample` | Correct refutation of this rational implication. |
| `repair` | `x = y/a`, same three premises | `(2,1,2)` | All premises true; conclusion `1=1`; `not-counterexample` | Correct sampled result, explicitly not treated as universal proof. |
| `unit` | `x = a*y`, same premises plus `a=1` | `(1,1,1)` | All four premises true; conclusion `1=1`; `not-counterexample` | Faithful degenerate control. |
| `invalid_assignment` | `x = a*y`, original three premises | `(2,1,3)` | `a>0` and `x>0` true, but defining premise `3=2` false; conclusion `1=6`; `outside-assumptions` | Correct rejection; it cannot refute the original implication. |

The assignments and all four outcomes match `expected.json`. The raw stdout files agree with `RUNS.json`, including exact evaluated values. The input and pre-review manifest hashes independently recomputed without mismatch (14 and 38 entries respectively). The distinction between native status and process exit code is accurately stated: all commands exit 0 while status carries the mathematical outcome.

## Mathematical controls and scope

The inverse claim fails because the defining identity yields `a*y=a*(a*x)=a²*x`, which need not equal `x`; at the supplied positive rational assignment the values are `4` and `1`. The proposed repair is universally valid over rationals under the stated premises: `a>0` entails `a≠0`, and `y=a*x` gives `y/a=(a*x)/a=x`. The unit control is also universally valid under its extra premise: `a=1` and `y=a*x` imply `y=x`, hence `a*y=x`. These universal algebraic arguments are separate from the single-point `not-counterexample` executions, as the report says.

The rational fixtures have authored scalar domains and do not establish realizability as probability laws or integrals. In particular, replacing the PLD parameter `exp(t)` with a rational `a` does not itself establish the source map, normalization, smoothness, differentiation, or law constraints. REGISTRATION.md, FIRST-REPORT.md, and the requested guidance consistently preserve that limit and direct the reader to the separately reviewed Gaussian source witness for the actual PLD finding. No probability counterexample is claimed from these four cases.

## Workflow completion and guidance

The reports correctly characterize this as four exposed, supplied-goal/supplied-assignment checks, with no discovery test, held-out evaluation, Lean check, or comparison advantage claim. Preparation used the existing demo to produce v2 plans/challenges, but those plans remain unfinished fixtures; there is no claim of native investigation finalization or independent challenge ingestion. The reported subprocess sum excludes preparation/review and is not end-to-end audit cost. These limitations are visible rather than promoted as completed workflow guarantees.

The “Check a formula against its definitions” section, bundled skill paragraph, and shared reference section agree on the important boundaries: substitute into defining identities; freeze original goal and separate repair; require premise-satisfying and source-realizable witnesses; treat rationalization as an authored abstraction; distinguish `outside-assumptions` and `not-counterexample`; specify source/formal maps; reconcile stable IDs; freeze evidence; and claim no automatic formula discovery or semantic-equivalence guarantee. The guidance is consistent with this supplied qualification.

Reviewed IDs: `inverse`, `repair`, `unit`, `invalid_assignment`. The accepted coverage is exactly these supplied obligations and controls.
