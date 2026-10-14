# Proposal

## Why

The Quux Navier–Stokes audit checked formal endpoints and mapped broad construction stages yet missed two intermediate correspondence discrepancies. Ladon's completed r70 investigation already explains one of those discrepancies; the missing evidence is whether a source-first audit can find such problems without being given their locations, and expose omissions before endpoint checks create misplaced confidence.

## What Changes

- Establish a bounded correspondence-discovery workflow that starts with a selected exposition's claims and reasoning steps, retains unmapped passages, and follows their proposed formal support backwards through actual consumers and premise producers.
- Compare exact local mathematical contracts: hypotheses, quantifiers, domains, derivative orders and variables, norm exponents, constant dependencies, and conclusions. Keep statement correspondence and proof-method correspondence separate.
- Require an explicit implication or a visibly unresolved obligation when the existing formal result differs from the prose. Preserve the original proposition before attempting a repair or an alternative argument.
- Organize four work packages: source coverage and triage; quantitative contract comparison; consumer-directed local checking; and withheld-case evaluation. Runtime changes belong to separately scoped children justified by observed missing operations; reuse existing result, search and checking facilities first.
- Preserve this conversation's blind failure and post-reveal diagnosis as development evidence. Use both Navier–Stokes examples as known controls, alongside faithful and equivalent reformulations, then evaluate detection on separately withheld material.
- Deliver a usable audit recipe, reproducible findings and a measured decision about Ladon's contribution. Stop after one frozen evaluation and its analysis; an unsuccessful evaluation completes the investigation but leaves the detection-benefit objective unmet. See the [acceptance contract](specs/ladon-correspondence-discovery/spec.md).

## Capabilities

### New Capabilities

- `ladon-correspondence-discovery`: source-scoped discovery of informal/formal discrepancies, including explicit audit coverage, local contract comparison, evidence-directed follow-up and evaluation without disclosed fault locations.

### Modified Capabilities

None. Existing artifact identity, attachment, checking and attributed-review contracts retain their authority and formats. This capability consumes those facilities; it does not replace them.

## Impact

Ladon owns the workflow and any justified implementation. Likely integration points are `result_manifest_summary.py`, `result_assessments.py`, result exposition views, declaration lookup and source-goal checking; exact runtime edits are selected only from an observed consumer need. The existing `ladon-proof-correspondence-audit-umbrella` stays closed, with its known-case findings intact.

Quux supplies historical audit evidence and optional development experiments. Portable Ladon tests and production code must work without a Quux checkout, a research repository, network access or an implicit model service. No change to Quux's active packet, no public API commitment and no full-paper certification is included in this planning change.
