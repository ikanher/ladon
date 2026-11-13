# Registration review — synthetic comparison r01

**Scope:** Reviewed `REGISTRATION.md`, `HANDOFF.md`, and `ARM-PROMPT.md` against umbrella task N.2c only. This is a registration review, not a review of case mathematics or answers.

**Disposition: revise before launch.** The design substantially addresses N.2c: it labels the study as controlled exposition-fault detection; binds five paired units and one variant per context; discloses supplied-owner/crosswalk scope; gives both arms the same source, Lean project, recipe, model settings, and numerical budgets; registers Ladon's extra access; separates preparation and arm work; and requires first-report preservation, blinded review, and resource/exposure incident handling. No mathematical arm is authorized to start until the identified items are resolved in the registration and prelaunch manifest.

## Required clarifications

1. **Make the exact delivered-file allowlist auditable.** The handoff asks the custodian to verify `registration SHA256SUMS` and “all referenced allowlist hashes,” but the handoff does not identify where those files live or require them to be created before launch. The prompt's “registered tool/runtime files” also leaves auditors with a wider and less precise read scope than the registration's declared common inputs. Before launch, name the checksum/allowlist artifacts and bind them in the prelaunch manifest; enumerate which tool/runtime files each arm may read. Keep the registration, freeze, and other cases outside auditor workspaces as already intended.

2. **Operationalize the adjudication gate.** The primary gate depends on a finding being “useful,” “independently upheld,” or a “serious false accusation,” but the packet does not give reviewers a per-finding rubric or say who resolves reviewer disagreement. Define the evidence checklist and decision categories for each claim, how omissions/ambiguous readings are scored, and the fixed reconciliation authority/process before launch. Preserve both first ratings as specified. This is needed to apply the paired additional-finding/no-new-serious-false-accusation criterion consistently.

3. **Specify the invocation accounting rule.** The budget counts “Lean invocations,” including underlying Ladon checker/extractor invocations, while costs separately request ordinary and underlying Lean attempts and process-level limits. State whether a Ladon command and each Lean process it starts each consume a slot, and how retries/failures and concurrent child processes are counted. Record command and process identifiers in the run log. This prevents arm-specific interpretation of the 20-invocation cap.

## Readiness assessment

The arms are credibly matched on mathematical inputs and recipe, with the registered treatment being additional native Ladon access. The 20-minute wall clock, 20-invocation cap, 12 GiB RSS, output cap, and non-escalation rule are explicit. Runtime freeze, prepared-copy provenance, no-live-sibling restriction, and sequential alternating launch order are good controls. The stated endpoint and cost fields are useful, and five related units are correctly kept descriptive rather than treated as an inferential sample.

After the three clarifications are frozen and the required checksums/manifest are actually present and verified, this registration is suitable to hand to a separate execution packet. This review does not authorize or report execution.
