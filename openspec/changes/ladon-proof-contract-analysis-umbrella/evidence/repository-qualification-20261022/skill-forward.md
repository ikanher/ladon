# Assignment 1340: blind skill-forward evaluation

## Scope and actual actions

Loaded `/home/codex/projects/codex-skills/ladon/SKILL.md` as the current Ladon skill. Followed only its linked material relevant to an exposition audit and saved rational-witness refinement: `references/contract-analysis.md`, `docs/NL_LEAN_CORRESPONDENCE.md`, `docs/INVESTIGATION_LOOP.md`, `docs/CONTRACT_REFINEMENT.md`, and `docs/REPORT_CONTRACT_V3.md`.

The user scenario was treated as a request for next commands and a bounded interpretation of an archived refinement record. I did not open the supplied/archive artifact, any source file, target-specific example, prior finding, or answer key. I did not run native Lean, mutate the plan, or produce a report. This keeps the evaluation blind and within the requested inputs.

Selected runtime commands actually run from `/home/codex/projects/ladon`:

```bash
PYTHONPATH=src python -m ladon.entrypoint version --json
PYTHONPATH=src python -m ladon.entrypoint investigation contract --help
PYTHONPATH=src python -m ladon.entrypoint investigation contract refine --help
PYTHONPATH=src python -m ladon.entrypoint investigation contract inspect --help
PYTHONPATH=src python -m ladon.entrypoint investigation report --help
```

Runtime output identified package version `0.3.0`, observed source commit `9695596ed9db287076251649ae57051331f83775`, dirty checkout, and Python `/home/codex/miniconda3/bin/python`. The source revision is provenance, not installed-byte equality. Help confirms `contract inspect --input ... --root ... --output ...` and `investigation report --plan ... --root ... --refinement ... --output ...`.

## Recommended next commands

Use new output paths and the actual source root. First inspect the archived refinement against current source bytes and citations:

```bash
LADON_CHECKOUT=/home/codex/projects/ladon
PYTHONPATH="$LADON_CHECKOUT/src" python -m ladon.entrypoint investigation contract inspect \
  --input /path/to/archived-refinement.json \
  --root /path/to/source-root \
  --output /path/to/new-run/refinement-inspection.json
```

Then attach the refinement supplement to a report built from the current authored plan:

```bash
PYTHONPATH="$LADON_CHECKOUT/src" python -m ladon.entrypoint investigation report \
  --plan /path/to/current-plan.json \
  --root /path/to/source-root \
  --refinement /path/to/archived-refinement.json \
  --output /path/to/new-run/report.json
```

Before relying on the association, ensure the supplement's `originalFinding.id` matches a finding in the report plan; if the report target is an observation, use its `observationId`, not a short author label. This attachment is by ID and does not establish semantic correspondence.

If fresh lift authority is needed, the guide's command is a new `contract refine` invocation on the original request with a new output file. It performs Lean work. I did not execute it under this blind task's explicit prohibition. Do not treat a saved `spurious-countermodel` field as current checker authority.

## What the evidence can support

`contract inspect` recomputes the bounded rational checks and checks current source hashes/quotations. A saved refinement is reported as `validated-historical`, `leanReplayed: false`, and `liftAuthority: unverified-saved-result`; nested positive flags and a digest do not authenticate the old Lean producer or prove fresh replay. The report preserves the original finding plus the refinement observation/branches, but association by ID does not certify translation to the prose.

A source-cited branch that excludes the old rational assignment establishes only that this assignment violates the added predicate (`outside-assumptions`). It does not establish the universal claim, and a repair branch is a separate proposed claim. Preserve the original finding, witness, and goal unchanged; keep source fidelity, formal support, and mathematical falsity as separate review dimensions. Even a fresh successful lift is scoped to the selected formal interpretation and does not certify that interpretation's fidelity to the exposition.

## Configured memory-cap response

The skill gives a 12 GiB default process-tree RSS cap, with operation-specific caps separate. If a diagnostic says `Stop progress and report back to user:`, stop dependent work, preserve the JSON and terminal diagnostic, and report the configured cap, observed peak when available, exact command, and preserved evidence. Do not automatically retry with a higher cap or reset the deadline. A memory stop is an operational limitation, not a counterexample or evidence of mathematical falsity.

## Decision defects / blockers

No blocking skill decision defect was found for this scenario: the refinement guide directly covers saved inspection, source citation currency, report association, authority limits, and bounded stops. The concrete command still depends on caller-supplied paths and a matching finding/observation ID; those are absent by design in this blind prompt, so no command was executed against target artifacts. Minor usability ambiguity: “archived refinement-workflow-v1 JSON” is not a schema name defined in the current guide; confirm it is an input accepted by current `contract inspect` before treating it as the current refinement artifact. If not, preserve it as historical evidence and do not convert it by guessing fields.
