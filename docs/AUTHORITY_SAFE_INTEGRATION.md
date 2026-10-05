# Authority-safe integration qualification

Maintainers qualify one explicit tracked candidate before recording an
integration exit. Passing correctness and authority receipts is necessary;
the complete installed test population, clean build, generated contracts,
required Lean fixture, benchmarks and governance checks must also pass on that
candidate. A two-child conjunction alone is not the integration exit.

The acceptance inventory in
`openspec/changes/ladon-authority-safe-verified-discovery-umbrella/children/integration-acceptance-inventory.json`
names every maintained test file and both supported Python runtimes. The
installed runner rejects source-tree imports, altered package bytes, missing
selected tests, skips, failures and incomplete collection. Evidence records
exact commands, working directories, candidate/source/wheel identities,
platform posture, logs, omissions and prerequisite outcomes.
`scripts/authority_safe_integration.py` validates the correctness, authority and
integration receipts against three independently selected inventories and an
evidence root. It checks all content-addressed bytes and rejects partial or
mismatched prerequisites. Local digest and coverage verification does not
authenticate the producer.

OpenSpec backlog validation enforces the closed dependency ledger and wave
order. New ProofIR families, Rust parity owners, daemons, broad service
refactors and optional product layers cannot enter the prerequisite graph.
Scoped correctness or security maintenance stays with the existing owners.
A completion flag cannot unlock expansion; changing this policy requires a
separate reviewed contract change. The freeze remains through the verified
discovery exit, as required by the umbrella's stronger freeze invariant.

Qualification is candidate-specific. It does not establish operating-system
isolation, secrecy against arbitrary trusted target code, held-out mathematical
benefit, a verified-discovery vertical-slice exit, or public distribution
authority. Verified proposition discovery remains experimental until its
ordinary installed, network-disabled vertical-slice acceptance passes. The documented
primary workflow is declaration discovery; architecture review is secondary
and evidence/lineage supply its audit layer. Readiness still depends on exact
candidate evidence, including the separate discovery exit.

See [Reproducibility](REPRODUCIBILITY.md) for tracked inputs, runtime and Lean
pins, package gates and the owner-granted license prerequisite. Packaged
schemas are maintained source contracts; their tests and installed resource
checks detect drift. The supported-feature matrix has its own generator and
check mode. Historical exposition snapshots remain immutable comparisons,
not regenerated proof evidence.
