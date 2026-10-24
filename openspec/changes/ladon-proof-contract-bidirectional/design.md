# Design

## Context

See proposal.md. correspondence_check.py already checks premise supply and conclusion transfer in reconstructed contexts. New planning must reuse those checks, while exploiting producer contracts and propagation frontiers to select smaller goals.

## Goals / Non-Goals

**Goals:** locate a supported-fragment discrepancy and state the exact outstanding bridge. **Non-Goals:** infer necessity from a sufficient condition, reverse a theorem implication, or label one failed route as falsity of the endpoint.

## Decisions

### Backward transformers

For an admitted rule R and desired output Q, a backward transformer returns premise obligations P together with a certificate that P suffices to produce Q through R. Call these sufficient preconditions. Do not claim a weakest precondition unless an exact preimage/equivalence theorem is supplied. An unsupported inverse returns a residual rather than guessed constraints. Backward branches retain all premise occurrences and alternative routes.

Start with typed application, supported estimate composition, domain restriction and witness-dependence rules from domain. Quantified contexts remain ordered telescopes. Every requirement is attached to the original desired contract and reading; strengthening the source assumptions is not a successful comparison.

### Forward/backward meet

Compare each available forward contract with the backward requirement under the exact object map. Generate premise-supply, domain/representation and conclusion-transfer obligations through the existing correspondence layer. No goal can assume its disputed conclusion, unfinished parent theorem, or a missing premise. A checked bridge closes the specific route's gap; it does not erase a method difference elsewhere.

Emit a deterministic frontier ordered by source location, route identity and explicit heuristic priority. Explain the earliest unresolved comparison on each explored route. Do not call this a globally minimal cut or unique cause. Alternative route support and described-route support remain separate.

### Demand-driven checking

The obligations operation outputs exact generated-goal subjects plus existing source/application references. Check supplied proof terms through source_goal_completion.py and independent replay. If missing evidence requires a deeper formal slice, output a bounded slice request; the orchestrator decides whether the remaining budget permits it. Generated positions never masquerade as original Lean source observations.

Outputs distinguish checked-support, candidate-contract-mismatch, unresolved-bridge, unsupported and budget-exhausted. Mathematical falsity is a separate evidence dimension and requires a suitable counterexample.

## Risks / Trade-offs

- Backward analysis is mistaken for theorem inversion → include a one-way implication whose converse fails and a sufficient-but-not-necessary precondition control.
- Shared goals accidentally import missing assumptions → closed-context replay and forged-context negative fixtures are mandatory.
- Localization depends on search order → expose all examined routes and residuals, make only route-local claims.
- Backward rules add no useful focus → within 30 minutes and parent bounds, demonstrate a three-step estimate with a localized bridge and a valid alternative route. If localization only reproduces the whole theorem, record the feasibility limit before widening the profile.

## Migration Plan

Add the obligation variant and command, preserving existing correspondence/check APIs. Version generated templates and bind exact rule/profile IDs. Changes to source readings invalidate old plans rather than rewriting prior check receipts.

