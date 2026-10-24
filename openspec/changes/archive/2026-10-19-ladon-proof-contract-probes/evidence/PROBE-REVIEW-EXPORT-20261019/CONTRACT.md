# Probe reviewer-export contract

Frontier: `ladon-proof-contract-probes`, task 2.2.

## Objective

Export a source-bound, sanitized input for independent review of application
probes. The export must preserve original interpretation/source evidence,
exact generated goals, checker receipts, and every supplied attempt, while
omitting Ladon's proposed semantic conclusion and authority labels.

## Accepted interface

Python API: `review_application_probe(artifact, context, attempts, repo_root)`.
CLI: `ladon investigation contract review-probe --input REQUEST --artifact PLAN
--attempt RESULT... [--output PATH]`.

`attempts` is an explicitly ordered list of complete result envelopes from
separate `check-probe` runs. Order and duplicates are preserved. The export
cannot reconstruct results the caller does not supply because the checker has
no persistent cross-invocation attempt ledger. At most 64 attempts and 32 MiB
of input/output are accepted.

## Reviewer-input content

The export replays the native probe artifact against its exact context, resolves
the original contract and correspondence owners, validates both prose quotes
against their original source files, and includes source-map references and
anchors, interpretation/contract records, formal application context, the
probe template and exact goals. Every attempt remains visible. Semantic
application outcomes are mapped to neutral execution observations; low-level
goal checker outcomes remain evidence. Content-addressed raw checker receipts
are embedded when their references verify. Missing, changed or unbound
references remain visible with a load/binding observation and confer no
checker authority.

The packet has no top-level status, proposed implication/nonimplication result,
source-fidelity/falsity/authority label, diagnostic-derived conclusion or
candidate-analysis wrapper. Preparation/supervision statuses and diagnostics
are whitelisted as execution observations; unknown values are normalized.
`checks-completed` additionally requires one exact row per generated goal,
completed execution receipts, and supported raw receipts whose accepted replay
and trust states and term digests match the supplied checker terms. Missing or
inconsistent evidence is labeled partial or unverified, not completed.

## Limits

The local evidence store is trusted input. Hash checks detect modification and
context mismatch but do not authenticate a malicious writer with access to the
same repository. The export does not replay Lean proofs, establish current
formal-source freshness, assess natural-language fidelity, or infer a manuscript
error. A failed checker search remains unresolved evidence, not mathematical
non-implication.
