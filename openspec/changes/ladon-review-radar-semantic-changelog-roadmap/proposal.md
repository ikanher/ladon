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
- Add a semantic theorem-surface changelog contract for before/after
  declaration changes, especially theorem type, assumptions, conclusions,
  names, imports, and source evidence.
- Preserve Ladon's clean-core trust boundary: parser/backend observations are
  review context; Lean or explicitly quoted external artifacts remain the only
  sources for proof-truth or proof-correctness claims.
- Establish the optional "Proof X-Ray" lane as elaborated-backend enrichment
  for theorem surface, tactic/proof-shape, axiom/sorry/unsafe footprint, and
  dependency context, with authority labels on every field.
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
- `ladon-semantic-theorem-changelog`: Before/after classification for Lean
  declaration and theorem-surface changes, including proof-only changes,
  theorem-type changes, added/removed assumptions, weakened/strengthened
  conclusions, renamed-but-equivalent surfaces, and doc/comment-only changes.
- `ladon-proof-xray-enrichment`: Optional elaborated-backend enrichment for
  theorem surfaces, proof-shape context, tactic skeletons, axiom/sorry/unsafe
  footprints, and dependency metadata without making Ladon a proof authority.

### Modified Capabilities

None.

## Impact

- Affected artifacts: OpenSpec roadmap, future child packets, report schema
  contracts, benchmark fixtures, and reviewer-card examples.
- Affected code in future child packets: CLI entry points for diff/review
  commands, declaration extraction and comparison modules, atlas/reviewer-card
  rendering, ProofIR bridge integration surfaces, and optional Lean helper
  enrichment.
- Affected workflow: maintainers should be able to run a review/diff command
  over a Lean repo or PR and receive bounded review priorities instead of raw
  metric dumps or theorem-truth claims.
- Affected trust model: every output must distinguish observed structural
  context, source-evidence attachment confidence, quoted external claim status,
  and any Lean-elaborated fact with tool/version/hash metadata.
