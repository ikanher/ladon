# Tasks

Implementation was authorized after the reporting session and measured hypothesis check.
Current result: ordered scheduling and small verified replay pass; the authorized
12 GiB default-cap follow-up completed 19 modules before its shared build deadline. Tests and the remaining
large-case gate are recorded in [the implementation report](evidence/implementation/REPORT.md).

## 1. Establish the resource-control mechanism on a small fixture

- [x] 1.1 Add a deterministic multi-module replay fixture and bounded process instrumentation that separates setup, compiler fan-out and per-child cost; verify the trace identifies which mechanism exhausts the cap without the research checkout.
- [x] 1.2 Identify and test a supported scheduling mechanism under the pinned toolchain; demonstrate its effective expensive-build concurrency bound, or record the exact unsupported gap. Do not assume a jobs flag or environment variable works.
- [x] 1.3 Write and freeze failing tests for the new policy/observability contract; retain and run RSS exhaustion, timeout and descendant-cleanup regressions for the reused supervisor, including observation-enabled execution. Record which checks were red before implementation.

## 2. Expose and enforce bounded replay execution

- [x] 2.1 Add the explicit CLI/service build policy through the existing replay pipeline; verify help, default compatibility and early validation with focused CLI/service tests.
- [x] 2.2 Enforce the selected strategy inside the fresh replay root with one finite build-stage deadline and existing RSS/output/cancellation supervision; verify observed concurrency and no per-module deadline reset.
- [x] 2.3 Retain capsule validation, locked dependencies, original-path isolation and structural/trust comparison; verify mutated-source, renamed-checkout, identity-mismatch and unsupported-toolchain regressions.
- [x] 2.4 Document the supported mechanism, limits and failure behavior in the existing CLI/capsule docs; verify every documented option against installed help and a small fixture run.

## 3. Make resource outcomes actionable

- [x] 3.1 Extend/version replay receipts with requested/effective policy and bounded stage/child/fan-out evidence; verify deterministic classification, unavailable-measurement handling and redaction tests.
- [x] 3.2 Preserve the meaning of aggregate process-tree RSS and historical receipts; verify any added memory metric is separately labelled and cannot silently turn a prior cap failure into verified status.

## 4. Validate integration and hand back evidence

- [x] 4.1 Run the existing capsule replay suite plus the new small policy fixture; retain exact commands, installed identity and test results showing no verification weakening.
- [x] 4.2 After the small gate passes, run one explicitly budgeted actual-capsule integration attempt using [REPRODUCTION.md](REPRODUCTION.md); retain dependency/build/helper stages and report the achieved outcome, including any new bottleneck. Do not claim success from build completion alone.

## Workflow follow-up

- Hand the result back to the historical proof-lineage owner; that owner alone updates mathematical/capsule acceptance in the proof project.
- Archive only after the owning Ladon review and implementation acceptance gates pass.

## Full research-capsule field result, R05

All434project modules and868ordered build steps now pass within4636seconds
and10.067GiB. The separate final theorem query hits the16MiB output cap; its
comparisons remain empty. See [documentation-only owner handoff](FIELD-OUTPUT-LIMIT-R05.md).
This is a new transport gate, not a failure of ordered build scheduling or a
verified whole replay. No implementation or cap change was made by the caller.
