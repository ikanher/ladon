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
