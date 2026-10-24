# Source-bound atomic premise construction

The Python operation `instantiate_source_bound_premise` now turns one selected
backward requirement into a generated, source-bound Lean goal. The controlled
fixture checks that goal through the existing source-goal completion API. This
is a narrow implementation result supporting tasks 1.2 and 2.2; neither task is
complete.

## What was demonstrated

The operation recomputes the exact backward request/result and selects an
ordered branch and premise occurrence. It verifies parent/provider snapshots,
freshly observes their actual Lean statements, and compares stable semantic
fields. A self-consistent, rehashed fabricated statement that passes the older
snapshot freshness verifier is rejected by this fresh comparison.

For the admitted fragment, symbols and types come from the observed AST. Only
the selected regularity offset changes. Distinct named coefficients remain
distinct even when their coarse contracts coincide. The generated proposition
is a closed two-binder Nat estimate, without visible proof hypotheses. Its
structural expression is checked against the requirement, including the builtin
Nat instances. Display text has no proposition authority.

The context contains the exact source prefix before the parent declaration,
plus disclosed `import Lean` instrumentation. It excludes the completed parent
and its source module from the generated environment. Open scopes are closed
using Lean's actual command-scope metadata. A separate completed prefix probe
passes through the existing strict statement frontend before incomplete-goal
capture. This checks the exclusion guards and rejects earlier frontend errors.
The incomplete goal also retains its own guards, exact selected tactic span,
source digest and compiled-import checks.

The retained public fixture selects offset 1 from a parent request of offset 3
and a provider with offset 0. Construction returns `candidate-goal`. The
provider-based term then completes with accepted independent replay and axiom
coverage; the observed axiom is `propext`. Separate actual-source tests reject
citations to the omitted parent and generated goal itself. A construction with
no term makes no proof or falsity claim.

Repeating the identical request preserves request, generated-source, prefix and
capture identities. The original source remains unchanged. Fresh observation
receipt identities are retained separately and need not remain identical.

## Verification and measured failures

The final compatibility selection passes **763 tests in 107 files**, including
real Lean capture/completion and the new negative controls. Eleven additional
frozen stage checks pass. Whole-repository no-cache Ruff and strict quality
checks pass; all 48 frozen test entries verify. Exact commands, source hashes
and JUnit results are in [SOURCE-ATOMS.json](SOURCE-ATOMS.json) and its linked
artifacts.

The negative controls exposed problems that passing positive tests missed:

| Failure | Retained observation | Repair |
| --- | --- | --- |
| A failed standalone command was ignored before goal capture | The proposed variant passed six public cases, but the new generated-prefix control still returned a candidate | Require a completed strict frontend prefix check |
| Moving the guard inside the tactic still allowed recovery | The same control continued to fail with an exact `skip` span | Retain the strict prefix check; tactic-span selection alone supplies no guard authority |
| Rejected metadata echoed oversized values | Both occurrence fields returned the rejected large strings | Bound and type-check returned metadata |
| Resource stops lost their reason and memory instruction | Three resource tests failed | Preserve the shared memory diagnostic and distinct timeout/output reasons |
| The original backward deadline did not constrain source work | Two deadline controls failed | Clamp all source stages to the earlier inherited deadline |
| An existing probe collision caused an unbounded read | Independent review reproduced a 9 MiB read | Use the descriptor-bounded reader on both collision paths; three regression tests pass |

The denied proposal and initial reports remain preserved. These are constructed
engineering regressions, not held-out mathematical discovery metrics.

The retained fixture run took **46.31 seconds**, including input observations,
two constructions and one successful completion. Its sampled supervised Lean
process-tree peak was **3,733,647,360 bytes** (about 3.48 GiB). All stages used the
12 GiB RSS cap and 8 MiB output cap. Individual subprocesses were capped at
30 seconds; construction, completion and the repeat shared the same 120-second
request deadline. This single run is not a general performance estimate.

Independent Luna medium reviews covered the producer budget plumbing and
adapter integration. Review found the collision defect and checked its repair;
the final review reported no additional actionable defect. See
[SOURCE-ATOMS-REVIEW.json](SOURCE-ATOMS-REVIEW.json).

## Reproduce and inspect

Use the current checkout:

```sh
PYTHONPATH=src .venv/bin/python -m pytest -q \
  tests/test_proof_contract_source_obligations.py \
  tests/test_proof_contract_source_obligation_boundaries.py \
  tests/test_proof_contract_source_obligation_instances.py \
  tests/test_proof_contract_source_obligation_guards.py \
  tests/test_proof_contract_source_obligation_resources.py \
  tests/test_proof_contract_source_obligation_parent_deadline.py \
  tests/test_proof_contract_source_obligation_collisions.py \
  tests/test_proof_contract_producer_bounds.py

PYTHONPATH=src:tests .venv/bin/python \
  openspec/changes/ladon-proof-contract-bidirectional/evidence/run_source_atom_fixture.py \
  --output .codex/state/proof-contract-analysis/atomic-source-fixture-fresh
```

The second command requires a fresh output directory. Retained actual results,
generated Lean files and their digest manifest are in
[atomic-source](atomic-source/MANIFEST.json). Archived copies preserve the
original bytes; the driver regenerates an executable context and new receipts.

## Remaining boundaries

The admitted fragment is two explicit universal Nat binders, builtin arithmetic
and order, plain supported constant names, and one global named coefficient.
The desired contract must match the observed parent statement; the selected
provider contract may differ only in its offset. This does not yet bind an
arbitrary intermediate planner requirement to the original paper goal.

Input and report bounds are 8 MiB, input depth 128; the structural codec is
limited to 1 MiB, 4096 nodes, depth 64 and 65,536 expanded expression nodes.
Proof checking still uses the existing fresh-recapture/replay/trust operation.
Unsupported transports remain incomplete. Source reading IDs are attributed
labels, not authenticated prose interpretations.

Ordered collections of premise-supply obligations, domain/representation
transport, conclusion transfer, provider-slice requests, native round trips and
the public obligations CLI remain open. No whole-method support, prose fidelity,
manuscript error detection, or beam-search improvement is established here.
