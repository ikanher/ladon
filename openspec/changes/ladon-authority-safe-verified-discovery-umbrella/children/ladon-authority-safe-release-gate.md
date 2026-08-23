# `ladon-authority-safe-release-gate`

Integrates the two repair children without merging their implementation ownership.

- **Owns:** conjunctive release policy; explicit-candidate gate; generated authority-safe receipt; expansion-freeze validation; documentation/skill/readiness synchronization.
- **Starts after:** `ladon-proof-discovery-correctness-repairs` and `ladon-execution-authority-integrity` have independently exited.
- **Integration owners:** clean-candidate gate, installed-distribution smoke, supported-feature/readiness generator, release evidence, OpenSpec governance.
- **Enables:** `ladon-verified-discovery-loop`.
- **Excludes:** implementing child repairs, public package publication, external repository promotion evidence.
- **Exit:** one tracked candidate passes both child suites plus strict quality and installed gates; no required input is borrowed from the worktree or another revision; all maintained surfaces agree on authority-safe state; a machine-readable integration receipt is published.
