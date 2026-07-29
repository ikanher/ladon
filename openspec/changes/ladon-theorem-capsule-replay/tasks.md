## 1. Replay Contract And Content Preflight

- [x] 1.1 Depend on the completed materialization contract and add replay receipt, stage, comparison, isolation, failure-taxonomy, and final-status models.
- [x] 1.2 Validate capsule/plan schemas, normalized paths, complete inventory, hashes, modes, toolchain/lock compatibility, guarantee level, and undeclared resolution-affecting files before process launch.
- [x] 1.3 Add backward-compatible `ladon theorem replay` and extract `--verify` CLI integration with canonical JSON, clean channels, and documented exit classifications.

## 2. Clean-Room And Supervised Execution

- [x] 2.1 Create a fresh replay root and sanitize working directory, Lean/Lake paths, environment, generated configuration, arguments, caches, and allowed roots so the original checkout is unavailable.
- [x] 2.2 Add portable isolation probes plus optional stronger platform isolation, record the achieved level, and make any original-path or undeclared-input resolution a terminal violation.
- [x] 2.3 Resolve the pinned toolchain and locked dependencies under explicit network/cache policy while distinguishing environment-unavailable and dependency-unavailable outcomes.
- [x] 2.4 Run Lake, Lean, and helper descendants through the existing time, memory, process-tree, and bounded-output supervisor with deterministic cleanup.

## 3. Lean Verification And Receipts

- [x] 3.1 Compile the materialized target prefix and query the exact fully qualified theorem with the compatible Lean helper protocol.
- [x] 3.2 Compare declaration kind, toolchain-scoped type fingerprint, value fingerprint when required/supported, semantic dependency closure, and trust frontier against the plan.
- [x] 3.3 Emit canonical receipts with sanitized stage commands, bounded output digests/excerpts, exit classes, dependency facts, isolation evidence, structural comparisons, trust facts, nonclaims, and stable identity.
- [x] 3.4 Ensure verified means only that every recorded Lean replay check passed and never implies Ladon proof authority, global minimality, offline vendoring, system hermeticity, or axiom freedom beyond observed trust evidence.

## 4. Failure And Security Coverage

- [x] 4.1 Implement content-invalid, environment-unavailable, dependency-unavailable, unsupported-facet, resource-limit, Lean-rejected, identity-mismatch, isolation-violation, and verified classifications.
- [x] 4.2 Redact host paths, credentials, tokens, and uncontrolled environment content from receipts while retaining role-based diagnostics and hashes.
- [x] 4.3 Prevent a failed replay or helper from mutating capsule evidence, the original checkout, or a previously published successful receipt.

## 5. Portable Acceptance

- [x] 5.1 Add positive fixtures that replay after the source checkout is renamed/unreadable and prove identical standalone and extract-with-verify behavior.
- [x] 5.2 Add negative fixtures for mutated/missing files, undeclared imports, original-checkout leakage, toolchain/lock mismatch, unavailable dependencies, Lean errors, theorem/type/value/trust changes, resource limits, and secret-bearing environments.
- [x] 5.3 Pass focused replay tests, installed-wheel CLI/help/channel tests, process-tree cleanup, receipt determinism/redaction, clean-checkout gates, strict OpenSpec validation, and Python quality gates.
