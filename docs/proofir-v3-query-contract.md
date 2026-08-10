# ProofIR v3 query contract

Public query limits are positive integers in `1..10000`. Invalid limits fail
before SQL execution. Each dossier section reports `matchedExact`; when a bounded
`limit + 1` probe detects truncation, `matched` is a lower bound equal to the cap,
not a fabricated total.

Navigation is a bounded route/index view. It is explicitly not a complete
conjunctive derivation slice and does not turn checker evidence into a premise.
Derivation rows include ordered premises, conclusion, rule, local context,
substitutions, and checker relationship. External `checkRunRef` and support or
attachment links are evidence references; only premise/conclusion edges define
derivation topology.

Incremental projection resolves references over validated persisted artifacts plus
the current artifact. Failed resolution happens before writes, and a failed
artifact leaves no new projection rows.
# Fingerprint admission

Semantic candidate joins use the single `ladon.proofir_fingerprint_registry`
registry. A scheme is searchable only when registered as exact; worker-emitted
`lean-expr-structural/v2` and native `lean-expr/v1` remain distinct schemes.
