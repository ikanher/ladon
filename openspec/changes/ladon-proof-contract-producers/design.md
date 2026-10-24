# Design

## Context

See proposal.md. Existing interpretation records are attributed, source-bound and lowerable only in a restricted typed fragment. Existing Lean helpers observe elaborated statements, local contexts and selected applications. Quux's subset/subtype experiment demonstrates that raw binder capture does not automatically supply dependent-domain semantics.

## Goals / Non-Goals

**Goals:** produce auditable independent contracts for both sides and expose feature-level coverage. **Non-Goals:** certify prose fidelity through elaboration, infer full semantics from printed theorem signatures, or require whole-proof extraction before a useful observation.

## Decisions

### Separate source channels

Prose production consumes original source spans, explicit symbol maps and an attributed structured interpretation. An LLM can author it through the existing workflow; the command does not require a particular model API. Freeze the interpretation and alternative readings before formal counterpart matching. Each feature points to the exact span and interpretation node that supports it. Fidelity review is independent and remains required for claims about the manuscript.

Formal production consumes an environment-scoped declaration or selected application. Recognize registered elaborated expression shapes for the domain profile, preserving binder identity, order, implicit parameters, local definitions and dependent domains. Lean performs definitional reduction and type checking under bounded worker execution; Python does not parse pretty text as a substitute. Representation changes such as subset-to-subtype need checked transport, not a text whitelist.

### Statement first, targeted expansion

Extract a declaration's contract without serializing its entire proof. Reuse statement/expr-graph helper ownership; add a focused helper only if the existing producer cannot return bounded summaries. Explicit premise or uniformity questions may request selected application slices through proof_slice.py. Record statement coverage separately from provider/route coverage. Missing bodies, unsupported domains, extraction caps and opaque expressions leave stable residuals and do not block source observation capture.

Record binder permission rather than claimed necessity: a witness after a parameter may depend on it; this does not establish that no uniform witness exists. A formal theorem proving a weaker contract is evidence about that theorem only, not disproof of a stronger statement.

### Consumer surface and tests

Implement produce under the parent command group, accepting source interpretation inputs or a formal declaration selector and output artifact path. Reuse native source maps and correspondence identities. Development fixtures include alpha-renaming, implicit binders, nested existentials, restricted domains, let aliases, unknown norm scales and one true transport equivalence. A mutation that moves a witness across a quantifier or drops membership must be visible.

Acceptance uses original small Lean declarations, not manually copied JSON alone. Per-feature coverage and exact residuals must survive inspect/report. Test source drift, stale environments and look-alike declaration names.

## Risks / Trade-offs

- General extraction proves too expensive → gate on six supported statements and two deliberately unsupported declarations in one 30-minute run, shared 12 GiB worker cap; success requires automatic formal summaries and accurate residuals, not manual substitutes labeled extracted.
- Matching biases interpretation → preserve pre-match snapshots and compare fidelity before inspecting reference judgments.
- Feature detection is overconfident → retain the full proposition and unknown fields, then check exact bridge goals.

## Migration Plan

Use the domain profile and existing interpretation/source-map readers. New production is opt-in; existing interpretation outputs and historical findings remain unchanged. No new scan of sibling experiments or reference solutions is part of this producer.

