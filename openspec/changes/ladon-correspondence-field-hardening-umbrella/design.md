# Design

## Context

See `proposal.md` for motivation and `evidence/BASELINE.md` for exact source and
field evidence. The predecessor umbrella is implemented and unarchived. Native
interpretation, selected application extraction, original connecting goals,
source-goal replay, and sanitized review already exist. This work repairs their
demonstrated boundaries rather than introducing a parallel correspondence stack.

The current lowering emits a global symbol name and arguments but does not apply
the symbol's authored function type at the use site. A separate `#check` of that
type cannot prevent a different overloaded instance from being selected later.
Formal context reconstruction uses display names and printed expressions despite
already retaining expression DAGs and local identities. Replay copies and
elaborates the selected source repeatedly per obligation. Finalization status is
already honest, but an agent can stop and write prose while it says `continue`.

## Goals / Non-Goals

**Goals:** preserve typed interpretation meaning; transport the observed scoped
context; reduce measured redundant work under unchanged checking authority; make
run termination a separately auditable public operation.

**Non-goals:** discover the target-paper fault, formalize its whole exposition,
infer author intent automatically, accept arbitrary Lean syntax in object maps,
write a general dependent-type elaborator in Python, introduce a persistent
cross-run theorem cache, or claim a CLI can prevent an agent writing plain text.
No runtime dependency on Quux and no new model service are introduced.

## Decisions

### A. Typed lowering with observed elaboration

Keep structured interpretations and use-site expected types together. In the
admitted fragment, elaborate a declared operator at its declared type before
applying its arguments; propagate expected operand types to numeral-only
subexpressions. Retain explicit casts and distinguish intended Nat, Int, Rat,
and Real operations. Do not force all division to Real. Unsupported dependent or
polymorphic signatures remain explicit residuals until a consuming case needs
them. Validate the actual application, not merely whether the declaration can
inhabit a separately asserted type.

Have the Lean helper return the actual elaborated interpretation and types in a
bounded structural form with readable rendering. Check agreement with the typed
structured subject under an explicitly versioned lowering profile. Constructor,
binder, and instantiated operator identities are authoritative for this check;
display text is review material. Any normalization used for comparison must be
performed or justified by Lean in the pinned environment. A type mismatch or
ambiguous unsupported encoding prevents support of the advertised interpretation.

The existing `P → P` obligation remains typing-only if retained. It cannot serve
as evidence that P is true or faithfully represents the manuscript. Source
review receives the actual elaborated proposition, its typed literals/operators,
the original quote, and remaining interpretation limits. Blindly adding type
annotations to pretty text or comparing pretty strings is insufficient.

Semantic changes produce new interpretation/plan/check identities; changed
helpers enter `implementation_digest`. Old artifacts stay readable as historical
observations but cannot inherit the new fidelity guarantee or checks. Use an
explicit closed profile revision and bind it in native identity; do not insert
unregistered top-level fields or silently mutate canonical v3 semantics.

### B. Transport local identity through Lean

Use the extracted ordered context and `localId` references as the mapping source
of truth. Allocate fresh generated binder names in Lean and substitute fvars in
actual `Expr` structures, including local types, let values, application arguments,
and premise providers. Re-abstract in dependency order and independently check the
result. Preserve original display names solely for source navigation and review.

The supported extension must handle the recorded A₀/A₁ functional matrix context,
Unicode/subscript and quoted names, repeated display names in separate scopes,
leading and nested lets, and existing admitted witness/branch contexts. Reject
future/escaped locals, self-providers, unmapped proof hypotheses, and illegal
cross-branch transport. Unsupported dependent patterns retain residuals.

Offer identity-keyed maps in a versioned map profile. Existing name-keyed input
remains accepted only when it resolves uniquely to one observed local; ambiguity
requires an explicit identity and cannot be guessed. Keep source module and
namespace identities exact. A basename/module workaround is a different context
and cannot impersonate the selected original context.

Broadening the regular expression for local names is rejected as the primary
fix: it leaves capture and shadowing risks in display-based reconstruction.

### C. Measure first, share only request-local preparation

Instrument extraction, inventory/freshness checks, source preparation, typing,
capture, completion, independent compiler replay, trust inspection, native
serialization, and review export separately. Record process count, input/output
bytes, process-tree memory, phase wall time, timeouts, and external build overlap.
Nested/overlapping durations must not be added into a fictitious wall time.

Target repeated source preparation within one request. Prepare a private source
context once and capture multiple isolated goals against its immutable identity.
Retain per-obligation exact goal/term/result/axiom observations and independent
compiler checking. If using a batched replay module, each result must identify
its own declaration and trust closure; a single process exit cannot stand in
for per-subject acceptance. One failed term cannot invalidate successful siblings
or let them inherit its assumptions. Any batch limit or failure retains the
unattempted frontier and falls back only under the original explicit budget.

Retain fresh extraction and full source/helper/import checks before and after
the request. No stale `.olean`, serialized success, or prior run can replace
those checks. Request-local reuse is invalidated on source, helper, context,
toolchain, compiled sidecar, goal, or term changes. Keep existing process bounds;
an optimization is not permission to raise caps or remove independent replay.

Use compact JSON in the ordinary producer path where it removes repeated
whitespace. Retain parsed equality, canonical identities, all obligations, and
the existing 32-MiB boundary. If a semantically complete compact result still
exceeds that cap, return an explicit bound; do not silently drop evidence or
introduce a new external artifact resolver in this packet.

The before/after benchmark uses frozen portable and selected real-source cases
on the same machine, toolchain, compiled inputs, concurrency and cache policy,
without an overlapping full rebuild. Three paired measured trials per workload,
with first-use setup separately disclosed, are the default. Success target:
at least 30% lower median public-check wall time for the six-obligation cone
workload and no greater than 10% median regression on the corrected numeric and
scoped-context workloads once compared against their semantically equivalent
post-A/B baseline. Report unsupported pre-fix cases separately, not as zero cost.
Missing the target is an unmet performance gate, not a reason to weaken checks.

### D. Explicit checkpoint and finalization operations

Keep status/next/finish as observations. Add ordinary CLI operations:

- `investigation checkpoint --plan ... --root ... --output NEW`: save an immutable
  progress receipt, remaining queue and time, without ending the run.
- `investigation finalize --plan ... --root ... --output NEW [--stop-record FILE]`:
  re-evaluate current inputs/clock and create a bound terminal receipt only for
  recorded completion, elapsed budget, an evidenced no-actionable-work blocker,
  or an explicit user-stop record. Otherwise return the existing continuation
  outcome with exit 2 and no successful terminal receipt.

Keep `mayFinalize` (permission to save an incomplete terminal report) distinct
from mathematical/formal completion. Align v3 budget/blocker meaning with this
distinction without silently relabeling old receipts. A user-stop record states
who supplied it, time, instruction reference, reason, plan and scope; it remains
attributed input, not authenticated user identity. The agent must not invent a
stop instruction. Time remaining alone does not authorize early finalization.

The reference runner/skill protocol consumes exit 2 by selecting actionable work
and preserving the original clock; it may save checkpoints at any time. It must
not wait idly to manufacture budget exhaustion. Unsupported links need specific
blocker records, and blocked work cannot hide remaining actionable source work.
If literature checks are forbidden by run policy, preserve their unverified
scope as policy-limited evidence; do not mark them checked. Human cancellation
always stops work and records incompleteness. No process controller or autonomous
model service is added: test the protocol with a deterministic driver and a
bounded live workflow, and state that arbitrary prose can bypass the CLI.

### E. Qualification and ownership

Packages A and B establish semantic correctness before package C reuses their
work. D can proceed independently after the baseline is frozen. All four join
the final consuming gate; `work-packages.md` defines exact inputs and exits.
Root owns shared production changes/builds. Independent red-test challenge and
final integration review apply during implementation under the authorized swarm
workflow, not as a substitute for actual Lean replay.

## Risks / Trade-offs

- **Typed metadata can still misread prose** → make lowering agreement and source
  fidelity separate; retain independent review and negative controls.
- **Binder serialization crosses dependent scopes** → use actual Lean structures;
  keep unsupported contexts explicit and test capture/branch attacks.
- **Batching changes snapshot/import authority** → before generalized batching,
  run one bounded two-goal portable experiment (20-minute engineering cutoff,
  existing per-process limits): identical goal/context/trust semantics, one
  failing sibling, and mid-request source mutation. If any fails, retain the
  safe per-goal route, record the failure, and revise C before expanding scope.
- **Historical timing includes concurrent builds** → freeze a clean measured
  baseline; the old 274–515 second observations motivate profiling, not speedup claims.
- **Finalization can be bypassed in free prose** → report the enforceable CLI
  boundary and exercise the actual operator workflow; never claim prevention.
- **Dirty parallel work may invalidate evidence** → check baseline hashes before
  each implementation wave and preserve unrelated changes and historical reports.

## Migration Plan

Implement on the current dirty checkout after recording drift from the planning
baseline. Introduce explicit profile revisions only where semantics change;
rebuild disposable projections if schema storage changes. Old canonical content
and reviews remain immutable. Re-author/replay affected interpretations into new
records and link corrections to the originals. Document behavior for old name
maps and legacy investigation plans; do not rewrite them on read.

Rollback restores the prior source implementation and generated disposable
indexes while retaining new evidence files. Consumers lacking a new profile
reject it explicitly. No release or archive is part of applying this packet.
