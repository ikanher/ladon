## Context

An unfinished Lean file may not build as a module, but Lean's frontend can expose
goals and context at an instrumented location. Probes must be isolated because query
work must not edit or import generated scratch content into production modules.

The existing implementation already has candidate application, ordered local
context evidence, residual expression rows, compact projections, supervised
scratch replay, and source/toolchain identity checks. It does not yet establish
source-position capture. `SemanticExpression` currently carries display/structural
types, not an independently bound context for each residual. The text renderer
prints an application containing metavariables without printing the residual
propositions. Extend these owners rather than introduce another checking core.

## Goals / Non-Goals

**Goals:** location-based goal/context capture, local-binder matching, compiler-error
queries, separate minimal examples, compact contextual residuals, and explicit
application completion with supervised Lean confirmation and trust evidence.

**Non-Goals:** no editor protocol replacement, automatic insertion, tactic search, or
claim that a scratch probe proves the production theorem. No universal claim
language, project-wide premise extraction, or implicit Lean execution during
offline exposition inspection.

## Decisions

- Capture one explicitly selected goal through the pinned Lean frontend, using
  its elaborated information in a temporary snapshot tied to the original source
  bytes/range. Prefer observing that information over textual instrumentation
  that shifts positions. An instrumentation fallback must demonstrate equivalent
  context and range binding before use. Ambiguous goal selection fails explicitly.
- Return local declarations with binder info, types, values only when safe/available,
  ordered dependencies, namespace/open scopes, imports/options, environment and
  exact source position. Preserve binder identity rather than reconstructing it
  from display names or sorting declarations. Hand-written input retains its
  caller-supplied evidence status.
- Treat parsed compiler errors as user-supplied query evidence until re-elaborated.
- Generate a minimal `example` with explicit imports and hypotheses in a temporary
  artifact; compile it under the normal process supervisor and retain diagnostics.
- Never write the probe into the target repository or include it in default builds.
- Foreground candidate, instantiated term and each exact residual proposition.
  Bind residuals to their observed local contexts, including introduced variables;
  do not guess per-residual context from display text. Evolve strict helper/result
  protocols explicitly if that information needs new fields. Keep exact expansion
  references and disclosed omissions under existing projection bounds.
- Keep exploration's optional scratch behavior. Add an explicit completion
  operation that consumes a capture and full proposed term, rechecks source and
  environment identity, checks against the preserved original goal, and requires
  independent replay. A receipt for a different goal cannot satisfy completion.
  Replay rejection, residuals, missing trust evidence and execution failure remain
  separate outcomes; compiler exit zero alone is insufficient.
- Default completion excludes placeholder dependencies such as `sorryAx` and
  reports observed axiom dependencies against a declared policy. Ordinary allowed
  foundational axioms are distinct from placeholders. Unknown dependency coverage
  cannot become an unqualified completed application. Do not infer trust from a
  lexical scan or an old check of the selected declaration.
- Selected-declaration premise views consume the elaborated type and binder
  evidence from existing owners. Authored explanations and definition expansions
  retain provenance; neither claims all mathematically necessary assumptions.
  Exposition-specific component scope remains owned by the result layer.

Alternative considered: require replay for every exploratory candidate. Rejected
because partial applications are useful and unnecessary replay adds cost. Another
alternative is changing backends immediately; existing interaction facilities can
be compared for contract-compatible reuse, but no new dependency or rewrite is
assumed by this plan.

## Risks / Trade-offs

- [Position shifts during instrumentation] → Anchor by source hash and syntax range.
- [Initializers execute] → Apply the same trusted-repository warning and supervision
  as other Lean-backed operations.
- [Probe context differs from owner] → Record every import/open/hypothesis and keep the
  confirmation scoped to the probe.
- [Source capture cannot reproduce a real local context] → Before expanding the
  workflow, test one source-position fixture with dependent ordered locals, a
  local let/notation and two selectable goals. Require exact binding or an explicit
  unsupported result under the existing deadline and 32 GiB process-tree limit;
  record actual RSS/time. Stop dependent completion work if context fidelity
  cannot be demonstrated, rather than silently substituting a hand-written goal.
- [Replay accepts an admitted proof] → Check transitive placeholder/axiom evidence
  for the generated application and retain coverage and policy separately from
  process success. Include an admitted dependency and ordinary foundational-axiom
  control in the focused integration checks.

## Migration Plan

First expose the existing residual propositions without changing checker authority.
Then qualify single-goal source capture, contextual residuals and explicit completion
together. Add compiler-error normalization after capture is stable. Keep existing
exploration CLI behavior compatible and document the additive completion contract.
Temporary artifacts are disposable rollback state. The umbrella owns separate
application/exposition evaluations; their omissions do not automatically establish
a runtime defect or a model-configuration failure.
