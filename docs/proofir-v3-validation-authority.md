# ProofIR v3 validation authority

`ladon.proofir_v3.validate_envelope` owns only common envelope shape, canonical
identity, bounds, and reference dispatch. It delegates the complete payload to the
single `validate_kind_payload` dispatch table in `ladon.proofir_v3_payloads`.

| Artifact kind | Authoritative payload validator | Reference families owned |
| --- | --- | --- |
| `proofir.environment` | `_validate_environment` | environment digest |
| `proofir.claim` | `_validate_claim` | statement |
| `proofir.derivation` | `_validate_derivation` | rule, premises, conclusion, context, checker |
| `proofir.plan` | `_validate_plan` | goals, steps, rules, premises, context |
| `proofir.attempt-log` | `_validate_attempt` | goal, attempts, residuals, checker |
| `proofir.check-run` | `_validate_check` | input subjects and result subjects |
| `proofir.source-map` | `_validate_source` | anchored subject |
| `proofir.attachment-set` | `_validate_attachment` | subject, source, candidate |
| `proofir.governance-observation` | `_validate_governance` | observed subject |

No consumer may infer a stronger payload status from envelope shape, source
attachment, process exit, or producer text. Adding a kind requires adding one
entry, one validator, valid/adversarial corpus rows, and a projection/query decision.

Compiled environments may contain up to **32,768** distinct module names.
Canonicalization permits this larger array only at `compiledModules` in a root
environment payload (for its digest) or at `payload.compiledModules` in a root
native environment envelope (including its detached-ID form). Nested lookalikes,
extensions and all other collections retain the 10,000-item bound. Every module
row still receives ordinary descendant validation; duplicate names are rejected
by the environment payload validator. Artifact and batch byte limits remain
8 MiB and 32 MiB. Producers also retain their compiled-file byte limits.

This is a capacity extension with unchanged v3 payload shape and canonical
spelling: existing accepted bytes and IDs are stable. Earlier readers can reject
environments above 10,000 modules; use a reader with this capacity support for
such artifacts. Stored environments that repeat a module name now fail payload
validation. Increasing process RSS alone does not change an installed
reader's supported evidence limits.
