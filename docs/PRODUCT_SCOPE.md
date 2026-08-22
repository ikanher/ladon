# Ladon product scope

Ladon's near-term product consists of three supported workflows. Other command
surfaces remain available, but they are optional layers and do not define the
core compatibility boundary.

## Supported workflows

### 1. Architecture review

Run the ordinary analyzer to inspect module ownership, imports, declaration
structure, architecture-policy violations, review regions, and calibrated
quality signals. Text-only analysis is the safe default; target builds and Lean
extraction remain explicit operations.

```bash
ladon --repo-root /path/to/project --root Project/Owner.lean \
  --architecture-policy docs/ladon-architecture-policy.json \
  --format json --output report.json
```

### 2. Declaration search and experimental proposition verification

Use the disposable proof-search index for bounded lexical/type-text shortlists.
Index construction is lexical and does not invoke Lean. These search commands
are contract-supported, but they do not establish Lean applicability.

```bash
ladon proof-search index build --repo-root /path/to/project
ladon proof-search search type-text --repo-root /path/to/project --pattern 'Nat → Nat'
ladon proof-search check candidate --repo-root /path/to/project \
  --module Project.Owner --goal 'True' --candidate Project.Owner.goal
```

The explicit candidate checker is an experimental proposition-only profile for
trusted repositories under a selected toolchain. Caller-supplied local context
is held and `proof-search discover --local` fails closed. Scratch replay is
advisory process evidence and does not promote candidate authority. Shortlist
rows remain discovery evidence, not elaboration results or proofs.

### 3. Evidence and lineage inspection

Use read-only ProofIR dossier, route, slice, alternative, and triage queries for
stored evidence. Use theorem lineage for an exact compiled proof-value
dependency closure when a pinned Lean environment is available.

```bash
ladon proof-search evidence theorem Project.Owner.goal --repo-root /path/to/project
ladon theorem lineage Project.Owner.goal --repo-root /path/to/project \
  --refresh missing --view routes
```

Stored evidence, structural routes, and lineage dependencies do not become
unqualified theorem-truth claims.

## Optional layers

- Reportsets, runsets, atlas JSON/SQLite, atlas diffs, and reviewer cards are
  optional multi-report review projections.
- Theorem capsules are optional packaging and clean-room replay machinery.
- ProofIR bridge adapters and external snapshot importers are compatibility
  edges, not the native-v3 semantic core.
- Benchmark, calibration, review-packet, and governance commands are maintainer
  workflows rather than the primary user product.

Optional layers may have narrower portability or stronger environment needs.
They must not weaken the three core workflows, become implicit dependencies of
them, or redefine their authority boundaries.

The generated [supported-feature matrix](SUPPORTED_FEATURE_MATRIX.md) records
the executable tests that gate each supported or optional workflow.
