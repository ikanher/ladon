## Why

The latest literature review points to a stronger Ladon roadmap: use Lean-owned
module, import, lint, axiom, and elaboration evidence to route review and
refactoring work without pretending to prove theorem truth. Ladon already has
claim-authority and proof-surface route auditing, so the next umbrella should
extend the surrounding Lean-review workflow rather than reimplement that core.

## What Changes

- Add a Lean module-system readiness track for public/private boundary pressure,
  facade/API shape, namespace-vs-module drift, and rebuild-scope risk.
- Add a Lean import-diet witness track that can consume or orchestrate
  Lean-owned evidence such as `lake shake`/minimal-import outputs and compare it
  with Ladon's text DAG.
- Treat proof-surface trust audit as an existing capability; add only the
  missing handoff for opt-in Lean verifier witnesses, report integration, and
  route-evidence completeness.
- Define a staged proof-xray enrichment path for optional elaborated evidence
  such as tactic skeletons, proof-state shape, axiom/sorry/unsafe footprints,
  and premise/dependency rows.
- Add refactoring-prescription output so findings map to concrete review
  actions such as extract-common-layer, move-bridge, split-large-owner,
  demote-implementation-import, promote-public-facade, run-import-diet, or add
  proof-surface witness evidence.
- Preserve Ladon's boundary: all new rows are review-routing evidence and must
  carry backend/source/confidence metadata where they rely on Lean or external
  tools.

## Capabilities

### New Capabilities

- `ladon-lean-module-readiness-audit`: Audits Lean module-system readiness,
  public/private boundary pressure, facade/API shape, namespace/module drift,
  and rebuild-scope risk.
- `ladon-lean-import-diet-witnesses`: Consumes optional Lean-owned import
  minimization witnesses and compares them against Ladon's observed import DAG.
- `ladon-proof-surface-witness-generation-handoff`: Defines the opt-in handoff
  from project-local Lean verifier scripts into the already-implemented
  proof-surface witness route audit.
- `ladon-proof-xray-staging`: Stages optional elaborated proof-shape evidence
  with strict authority labels and no parser-edge proof-dependency overclaims.
- `ladon-refactoring-prescription-output`: Converts existing and future review
  findings into concrete, prioritized refactoring prescriptions with source
  evidence and non-claim text.

### Modified Capabilities

None. Existing proof-surface/claim-authority route auditing remains the source
of truth for trust diagnostics; this umbrella only defines adjacent evidence
handoffs and reviewer workflow integration.

## Impact

- Affected future code: module DAG analysis, Lean helper/extractor contracts,
  optional witness ingestion, report rendering, atlas/reviewer cards, benchmark
  oracles, architecture policy summaries, generated/facade metadata, and CLI
  surfaces for opt-in Lean-backed checks.
- Affected future artifacts: `.ladon/` policy examples, optional import-diet
  witness files, optional proof-surface witness generator outputs, synthetic
  Lean fixtures, public Lean repo smoke reports, and follow-on OpenSpec child
  packets.
- Affected workflow: maintainers should get source-located review cards that
  say what to inspect first, which refactor direction is plausible, which
  evidence is Lean-owned or quoted, and which proof/trust claims remain outside
  Ladon's authority.
