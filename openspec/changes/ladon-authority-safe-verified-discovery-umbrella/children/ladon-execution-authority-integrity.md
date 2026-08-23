# `ladon-execution-authority-integrity`

Makes execution binding and evidence projection match the operation that actually ran.

- **Owns:** sanitized immutable execution context; identical preflight/worker environment; context fingerprint and redaction; explicit evidence axes; total transition table; compact receipt; persistence/dossier/render propagation; `ladon doctor --json`; dead recursive slicer removal.
- **Starts after:** umbrella evidence capture; may run in parallel with correctness repairs.
- **Integration owners:** semantic candidate worker, process supervision, ProofIR observations, SQLite v3, dossiers, renderers, installed CLI, derivation queries.
- **Enables:** `ladon-authority-safe-release-gate` after all transition and installed execution gates pass.
- **Excludes:** a general sandbox implementation, kernel-authority claims, new ProofIR families, new Rust ownership, discovery ranking.
- **Red evidence:** executable whose version depends on a discarded secret; ambient/absent-to-explicit promotions; live-to-stored reload; stale/mismatched projection; secret-leak scan; recursive slicer inventory.
- **Exit:** preflight and worker share one context identity; invalid transitions fail exhaustively; every reader weakens live evidence to stored; doctor is read-only; secrets are absent; only one slice traversal remains; isolated-wheel adversarial tests pass.
