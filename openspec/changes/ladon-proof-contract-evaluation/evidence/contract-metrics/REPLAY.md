# Contract evaluation replay

This stdlib-only verifier and scorer support future evaluation runs. No real evaluation population or key was used to test the implementation.

1. Keep registration inputs and runtime snapshots beneath one artifact root. Freeze an unlabelled arm report:

```sh
python scripts/freeze_contract_evaluation_report.py \
  --artifact-root ARTIFACT_ROOT --registration registration.json \
  --arm-report arm-report.json --receipt first-report.receipt.json
```

The receipt is created with exclusive file creation and stores the digest of the exact report bytes. Preserve both files unchanged.

2. After independent adjudication binds to that digest, run the scorer:

```sh
python scripts/aggregate_contract_evaluation.py \
  --artifact-root ARTIFACT_ROOT --registration registration.json \
  --first-report arm-report.json --receipt first-report.receipt.json \
  --adjudication adjudication.json --key custodian-key.json --out metrics.json
```

The key loader is invoked only after report digest, registration/runtime identity, exact case bijection, and adjudication identities pass. Output creation also refuses overwrite. For direct Python API calls, wrap `aggregate_evaluation(...)` in `artifact_root_context(ARTIFACT_ROOT)`; without that explicit context, the API uses the current directory and fails closed if the registration files are elsewhere. The CLI sets this context before it reads registration-linked artifacts.

Schemas are closed and bounded. Paths are relative to artifact root, must be regular files, and may not traverse symlink components. Registration is fixed to A=24, B=12, C blocked at zero. Miniature aggregation fixtures are supported only through `aggregate_case_metrics`.

The scored JSON retains all report rows with their expected class, case and finding adjudications, classification outcome, and case-level TP/FP/FN/control/abstention flags. Its top level binds registration identity and ID, run ID, arm, runtime identity, exact first-report digest, and canonical adjudication digest. Track summaries include coverage as cases with a non-null observed class divided by the fixed track denominator; `timeToFirstSupportedFinding` as cumulative case elapsed time through the first supported finding in first-report row order (null if none); and `unresolvedAdjudications` as the count of unresolved case-level plus finding-level judgments. Arm wall time comes from the report-level wall clock. Case elapsed times remain separately summed in `elapsedSeconds`.
