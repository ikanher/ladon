# Initial artifact-validator usage feedback

Date: 2026-10-02. Reviewer: the implementation-session LLM, not an independent
reviewer. Scope: qualitative development feedback on the offline validator.
Base source commit: `d64f475e23a7339c91aa280ff6e6679c27607875` plus this working
change. The fixture is illustrative and supplies no real Lean acceptance.

## Scenario 1: Interpret a valid manifest

Command:

```bash
.venv/bin/ladon result validate tests/fixtures/result_manifest/finite-map.json
```

Observed exit: 0. Relevant output:

```json
{
  "status": "valid",
  "validationScope": "offline-manifest-integrity",
  "canonicalResolution": {
    "status": "not-assessed",
    "unresolvedLinks": 1,
    "reason": "canonical-evidence-not-loaded"
  },
  "reviewSummary": {
    "current": 1,
    "historical": 0,
    "correspondenceStatuses": {"reviewed-with-differences": 1},
    "authority": "attributed-review-assertions",
    "reviewerAuthentication": "not-assessed"
  }
}
```

The mapping section reports one unmapped component. The correct interpretation
is that the manifest is structurally consistent; the supplied model review
identifies an extra assumption, and no theorem or correspondence was checked.
The explicit validation scope is necessary context for `valid`.

## Scenario 2: Edit a claim without re-approving the review

Create `temp/result-claim-correspondence-usage/changed-claim.json` by copying the
example, appending ` (revised)` to the claim statement, recomputing that claim's
revision and the manifest revision using `content_revision`, and leaving the
review's subject bindings unchanged. Run:

```bash
.venv/bin/ladon result validate temp/result-claim-correspondence-usage/changed-claim.json
```

Observed exit: 0; `current: 0`, `historical: 1`, and correspondence status
`not-reviewed`. This distinguishes a valid historical record from current
approval. Omitting the claim revision update instead gives an invalid-input
diagnostic; that behavior is covered by the regression suite.

## Scenario 3: Reject ambiguous JSON

Input `temp/result-claim-correspondence-usage/duplicate-keys.json` contains
`{"schema":"one","schema":"two"}`. Run:

```bash
.venv/bin/ladon result validate temp/result-claim-correspondence-usage/duplicate-keys.json
```

Observed exit: 2, empty stdout, and a `manifest-invalid` stderr diagnostic
requiring strict UTF-8 JSON with unique keys.

## Findings and follow-up

- Revision creation was not obvious from the schema alone. The new
  `docs/RESULT_MANIFEST.md` documents exact canonicalization and the producer
  helper. Validation does not silently rewrite review bindings.
- The compact validator reports review statuses and IDs but does not show the
  full assumption explanation. Inspecting the input manifest is the current
  workaround. The planned dossier should provide exact drill-down references
  and the relevant statement/differences; that remains future integration.
- Canonical evidence resolution is explicitly unavailable. No workaround was
  used to present schema validation as a Lean check.

All three command observations were reproduced in the implementation session;
corresponding regression tests cover the behaviors. Full captured command logs
are in ignored `temp/result-claim-correspondence-usage/commands.json` and are
optional local evidence, not a test dependency. No comparative metric,
independent comprehension judgment, or human-review claim follows from this
report.
