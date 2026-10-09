# Design

## Context

See proposal.md. The frozen feedback archive is `temp/ladon-adam-energy-field-feedback-r01.zip`; all 186 supplied hashes and 93 JSON files passed integrity checks. Current replay emits only direct imports plus closed expressions. Substitutions use printed binder names as keys. Capture expands every structural expression using tree-shaped `repr`.

## Goals / Non-Goals

Preserve exact original-goal completion and trust policy while repairing supported source contexts. Retain all local definitions and expression information under bounded output. Keep lexical updates with retained lineage under their existing refusal contract.

## Decisions

Replay must reconstruct the selected source environment in a separate compiler operation. Test a private exported snapshot of the selected environment before integration; a same-process axiom check alone does not satisfy independent replay. Source-prefix concatenation is unsuitable inside unfinished declarations. If exporting cannot preserve the checked environment, use an explicit separate replay helper that reprocesses the frozen source and kernel-checks the closed declaration.

Substitution identity combines stable declaration binder position with the displayed name. Canonical conflict validation remains strict. Batch evidence is attributable per candidate; invalid candidate evidence cannot become acceptance or discard valid independent records.

Capture encoding changes must version opaque structural fingerprints and update both capture and completion consumers. Diagnose expression fields first; if repeated expression trees dominate, use deterministic structural sharing rather than truncating local values. Keep public shape and complete local meaning where possible; historical captures need recapture when helper bytes change.

Report request limits as scalars and add explicit closed/residual counts without changing the established meaning of the historical aggregate. Build progress uses existing stderr event contracts.

## Risks / Trade-offs

- Environment snapshots can accidentally include unfinished declarations → verify selected context, independent compiler acceptance, earlier `sorry` rejection, recursive/internal-local controls and exact source/import bindings.
- Shared expression encoding could collapse meaningful distinctions → preserve every constructor, level/name, binder, metadata and local reference, deterministic roundtrip tests and changed-expression controls.
- Real capture may remain large → diagnose with one frozen-copy reproduction at 64 MiB and 32 GiB, retain measured field sizes and failures, then apply only a bounded mechanism demonstrated on a smaller regression.
- Existing dirty index work → preserve its sources and candidate evidence; this change gets separate qualification.

## Migration Plan

Retain historical evidence. Update docs and maintained skills when result meanings change; bump to 0.2.1 after successful qualification. New installed helper identities require fresh source captures. The bulletin board is `.codex/state/ultra-result-evidence.sqlite3`, topic `field-reliability`.
