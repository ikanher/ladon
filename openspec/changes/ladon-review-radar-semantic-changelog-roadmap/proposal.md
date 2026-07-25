## Why

External review identified Ladon's clearest non-toy niche as Lean project
observability and review intelligence: Lean proves, Lake builds, doc-gen4
documents, proof-agent tooling interacts with proof states, and Ladon routes
human review. The next roadmap needs to turn that product posture into ordered
work so Ladon can answer what changed, what became riskier to maintain, what
claims are licensed by the current Lean surface, and what evidence is missing
without overclaiming theorem truth.

## What Changes

- Define "Ladon Review Radar" as the umbrella product slice for PR/root/module
  review cards over changed Lean artifacts.
- Delegate the concrete semantic theorem-surface changelog contract to the
  bounded `ladon-theorem-surface-changelog` child, which consumes the alpha
  declaration surface.
- Preserve Ladon's clean-core trust boundary: parser/backend observations are
  review context; Lean or explicitly quoted external artifacts remain the only
  sources for proof-truth or proof-correctness claims.
- Keep optional "Proof X-Ray" content as a consumer-availability contract:
  direct declaration facts come from the alpha declaration surface, quoted
  trust rows come from staging, and future tactic/InfoTree rows come from the
  retained proof-xray roadmap.
- Keep Review Radar and semantic changelog useful before elaborated extraction:
  text/parser-backed import deltas, declaration deltas, root closure pressure,
  proof-family clusters, ProofIR attachment diagnostics, and packet evidence
  should already produce reviewer-facing cards.
- Defer UI-first rewrites, graph database work, automatic refactoring, full
  proof-dependency ownership, Rust rewrites, and general LLM explanation until
  the report contracts and benchmarks stabilize.

## Capabilities

### New Capabilities

- `ladon-review-radar`: Reviewer-facing changed-root/module cards that combine
  changed modules, changed declarations, import pressure, evidence attachment
  changes, proof-region hints, and non-claims.
- `ladon-proof-xray-enrichment`: Optional elaborated-backend enrichment for
  Review Radar that consumes separately owned declaration, quoted-witness, and
  future proof-shape evidence without making Ladon a proof authority.

### Modified Capabilities

None.

## Impact

- Affected artifacts: OpenSpec roadmap, future child packets, report schema
  contracts, benchmark fixtures, and reviewer-card examples.
- Affected future code belongs to later bounded children: semantic comparison
  in `ladon-theorem-surface-changelog`, then Review Radar orchestration and
  rendering in a separately proposed MVP.
- Affected workflow: maintainers should be able to run a review/diff command
  over a Lean repo or PR and receive bounded review priorities instead of raw
  metric dumps or theorem-truth claims.
- Affected trust model: every output must distinguish observed structural
  context, source-evidence attachment confidence, quoted external claim status,
  and any Lean-elaborated fact with tool/version/hash metadata.
