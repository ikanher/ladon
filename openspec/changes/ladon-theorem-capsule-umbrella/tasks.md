## 1. Contract And Dependency Governance

- [x] 1.1 Parse and validate `children/dependency-ledger.json`, including the planning → materialization → replay order, existing capability owners, guarantee invariant, and retained future lanes.
- [x] 1.2 Keep each standalone child capability spec byte-identical to its umbrella copy and reject owner-change/capability-name confusion.
- [x] 1.3 Preserve the caller-neutral CLI invariant: people, scripts, editors, and models use the same theorem phase and combined extraction commands.

## 2. Phase A: Exact Theorem Planning

- [x] 2.1 Apply `ladon-theorem-capsule-planning` before either byte-producing child.
- [x] 2.2 Land Lean-authoritative exact target selection and a complete typed dependency stream that is independent of report caps.
- [x] 2.3 Produce deterministic semantic/build closure plans with source/configuration fingerprints, trust frontiers, unsupported facets, and no target writes.
- [x] 2.4 Pass planning's portable exact-name, large-closure, ambiguity, drift, unsupported-facet, process-limit, installed-CLI, and determinism exits.

## 3. Phase B: Deterministic Materialization

- [x] 3.1 Apply `ladon-theorem-capsule-materialization` only after the planning capability and plan fixtures pass.
- [x] 3.2 Materialize the exact owner prefix, whole imported module closure, source-root layout, pinned toolchain, supported Lake configuration, and lock frontier from a validated plan.
- [x] 3.3 Publish only path-safe, fully inventoried, transactional, reproducible directory/archive output outside the target repository.
- [x] 3.4 Pass materialization's prefix, multi-root, drift, traversal/link/collision, interrupted-copy, target-no-write, installed-CLI, and reproducibility exits.

## 4. Phase C: Independent Lean Replay

- [x] 4.1 Apply `ladon-theorem-capsule-replay` only after materialized capsule fixtures and manifests are stable.
- [x] 4.2 Replay from a fresh root with the original checkout unavailable, pinned and supervised Lean/Lake execution, and explicit dependency/isolation policy.
- [x] 4.3 Compare the exact theorem's toolchain-scoped structural, dependency, and trust evidence and emit a canonical bounded receipt.
- [x] 4.4 Pass replay's mutation, missing-input, checkout-leak, toolchain/lock, dependency, Lean rejection, identity/trust mismatch, resource-limit, redaction, installed-CLI, and clean-room exits.

## 5. Combined Product And Acceptance

- [x] 5.1 Wire `ladon theorem extract <fully-qualified-name> --output <path> --verify` through the same three services without a caller-specific or hidden execution path.
- [x] 5.2 Run installed-wheel help, text/JSON parity, clean stdout/stderr, exit taxonomy, backward-compatible analyzer, process-tree, and clean-checkout gates.
- [x] 5.3 Run the full supported-Python test suite, strict Python quality, compile/build checks, and deterministic fixture gates.
- [x] 5.4 Strictly validate the umbrella and all three children, validate the global OpenSpec inventory, parse the ledger/automation JSON, run `git diff --check`, and compare child/umbrella specs.
- [x] 5.5 Audit code, schemas, help, and docs for bounded-report misuse, target-specific assumptions, unsafe path behavior, hidden target execution, proof/minimality/hermeticity overclaims, or duplicate source/module/snapshot/process authorities.
- [x] 5.6 Optionally exercise a fully qualified theorem in Matrix-Factorization as fingerprinted read-only observational evidence; portable fixtures remain the acceptance authority.
- [x] 5.7 Close the umbrella only when all three child exit classes pass and a capsule verifies with the original checkout unavailable.
