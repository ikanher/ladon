# Matched source-audit pilot — r01 results

## Decision

The preregistered primary gate was **not met**. Neither arm produced an independently upheld, reader-useful discrepancy among the six selected claims:

| Arm | Upheld useful discrepancies | Serious false accusations | Adjudicated faithful correspondences |
|---|---:|---:|---:|
| Ordinary Lean + recipe | 0 | 0 | 6/6 |
| Ladon + same recipe | 0 | 0 | 6/6 |

Two fresh blind reviewers independently rated all twelve report/claim pairs. They agreed on all twelve: each report accurately treated the six selected claims as supported correspondences. Neither report made a false accusation. The reports also contained cautious out-of-sample abstentions about larger training-accountant claims whose proof owners were absent from the capsule; those remain unresolved and are not evidence that the claims are false.

| Registered claim | Ordinary Lean | Ladon | Reviewer disagreement |
|---|---|---|---|
| KOut transcript release | Faithful control | Faithful control | None |
| KOut fixed-cardinality schedule mass | Faithful control | Faithful control | None |
| Poisson maximum-event lower witness | Faithful control | Faithful control | None |
| Poisson forward capped second-moment bound | Faithful control | Faithful control | None |
| Poisson reverse likelihood-floor bound | Faithful control | Faithful control | None |
| Poisson calibration interval | Faithful control | Faithful control | None |

For all six, adjudicators found no source/formal discrepancy, no unsupported allegation, and no unresolved registered judgment. Neither arm abstained on a selected claim. No genuinely ambiguous source passage was adjudicated in this sample.

This is a negative result for the frozen sample, and it does **not** establish that Ladon detects exposition faults. The sample contained no adjudicated faulty claim, so it offered no sensitivity test against a real fault. It also did not include a preselected genuinely ambiguous source passage. The result does show that, on these six controls, the ordinary recipe reached the same conclusions with fewer observed Lean/Lake invocations and less audit time.

## Registered comparison

The run used `gpt-6.1-sol` at high reasoning effort in two fresh contexts, the same pinned Lean v4.33.0 capsule, the same source-first recipe, a 90-minute wall-time ceiling and a 30 Lean/Lake invocation ceiling. The only intended treatment difference was access to the current working-tree Ladon executable at `/home/codex/projects/ladon/.venv/bin/ladon`. Token telemetry was unavailable. The exact registration and its hash are in `RUN-REGISTRATION.json` and `RUN-REGISTRATION.sha256`.

The six score claims comprise two claims from the deterministic KOut-of-T accountant note and four from the Poisson finite-bracket note. They form two source clusters, not six independent papers. Both original TeX notes include formal crosswalks that name Lean declarations. Therefore the comparison tests source-claim verification and proof correspondence with those mappings available; it does not isolate unaided discovery of the source-to-Lean map.

The selected claims were frozen without correctness labels. After blind adjudication, all six proved to be controls. The broad KOut-of-T accountant, adaptive signed-replacement argument, global positive threshold claims, and a named finite replay certificate remain outside the verified scope. Both arms were instructed to abstain where their capsule did not support those larger claims. They did so; a missing capsule owner was not treated as a counterexample.

The unresolved wider-scope claims are: the total exact-rational training accountant and universal add/remove theorem; the full adaptive signed-replacement reduction; projected lower realizations and global positive attained thresholds; and the concrete outward-rational replay certificate and historical replay provenance. These receive neither positive-finding nor false-accusation credit.

## Arm reports and observed cost

| Measure | Ordinary Lean | Ladon |
|---|---:|---:|
| Elapsed audit time | 479.409 s (7m 59s) | 567.788 s (9m 28s) |
| Lean/Lake invocations | 5 | 7 |
| Budget exhausted | No | No |
| Token telemetry | Unavailable | Unavailable |

Ladon took 88.379 seconds longer (18.4% relative to the ordinary run) and used two more Lean/Lake invocations. This is descriptive run-phase cost only: registration/capsule preparation and adjudication time were not instrumented, so no full-cost or cost-at-matched-quality claim is made.

The ordinary report and all supporting artifacts are under `arms/B/OUTPUT/`; the Ladon report and evidence are under `arms/A/OUTPUT/`. Their first-report SHA-256 values and complete per-file manifests are frozen in `ARM-ARTIFACT-MANIFEST.json`. The unblinding and gate calculation are recorded in `UNBLINDING-RECEIPT.json`.

Ladon ran its text extraction backend in owner scope. The report says it helped with source inventory/navigation, but it did not run Lean-backed extraction, ProofIR, or proof-xray and did not produce a mathematical discrepancy finding. This limits what the pilot says about Ladon's broader evidence workflows.

## Blind review and integrity

The two adjudicators received the same 151-entry input tree: the source/Lean capsule, the six-claim scoring population, and dossiers X/Y derived from the mathematical inventory, findings, and abstention sections of the frozen first reports. Process, command, timing, and budget sections were withheld to reduce arm-identity cues; originals remain unchanged. Both reviewers attested that they did not infer arm identity. Each rated all six claims in both dossiers. The reviewer files, acknowledgments, checksums, and agreement summary are in `adjudication/`.

The reviewers used different granularities for exploratory claims outside the six-claim scoring population (17 versus 24 records). Those raw counts are not comparable rates. Their registered-population decisions agree completely; the larger KOut-of-T theorem and other source assertions that lack adequate formal support in the supplied capsule remain unresolved. Reviewer 1 ran a bounded declaration/axiom check; Reviewer 2 performed source and proof-body inspection with a bounded static/numerical check but no independent kernel replay. Neither replayed the complete run command logs or rebuilt the full 63-module local dependency closure.

There was one procedural deviation in the Ladon arm: an early output path put one generated artifact in a run-level scratch directory under `arms/`, rather than the assigned arm output. The arm reported this during the run, preserved the artifact and hash in its own evidence folder, and removed only empty folders it had created. It analyzed only its assigned capsule; no other arm output or registration material was accessed. The exact incident is retained in `custodian-only/DEVIATIONS.md` and the arm's `output-path-incident.json`. Both copied input capsules remained unchanged, and the prompt difference was exactly one tool-access paragraph; see `INTEGRITY-VERIFICATION.json`.

## What this changes

The study does not justify integrating all three proposed diagnostics or claiming an advantage over ordinary source-first review. Keep the existing recipe and make no detector expansion based on this run. To test mathematical detection rather than correspondence verification, the next pilot should use a fresh source/Lean pair with at least one independently verified natural exposition fault held by a separate custodian, plus faithful controls and a real ambiguity/abstention case. Prefer a source whose exposition does not supply its Lean crosswalk if the intended question is unaided mapping. Keep the fault location and answer out of both audit contexts, freeze the input and rubric first, and report the result as a bounded challenge study rather than a reliability estimate.

## Evidence index

- `RUN-REGISTRATION.json`, `RUN-REGISTRATION.sha256` — preregistered conditions, budgets, model, gate and prompt hashes.
- `INTEGRITY-VERIFICATION.json` — prompt diff and identical capsule check.
- `ARM-ARTIFACT-MANIFEST.json` — frozen first-report and evidence hashes.
- `adjudication/ANONYMIZATION-RECEIPT.json` — reviewer packet derivation and redactions.
- `adjudication/ADJUDICATION-MANIFEST.json` — blinded reviewer identities, registered agreement and limits.
- `UNBLINDING-RECEIPT.json` — randomized labels, primary gate scores and result.
- `COST-LEDGER.csv` — available time/invocation observations and unavailable cost fields.

