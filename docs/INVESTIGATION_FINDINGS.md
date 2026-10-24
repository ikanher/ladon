# Source observations and findings

Use the current checkout through `uv run --locked python -m ladon.entrypoint`
from its directory. Alternatively set `PYTHONPATH=/absolute/ladon/src` and use
that checkout's `.venv/bin/python`. This avoids accidentally invoking an older
pip-installed version. Initialize the investigation once at its actual start;
these operations preserve its scope, clock and budget.

## Capture before formal extraction succeeds

An observation records a candidate difference without requiring a Lean formula
or extracted application. Save a record with these exact keys:

```json
{
  "schema": "ladon-investigation-observation-v1",
  "id": "local-comparison-1",
  "source": {
    "path": "runs/current/exposition.txt",
    "sha256": "actual SHA-256 of complete file bytes",
    "startLine": 10,
    "endLine": 12,
    "quote": "exact complete lines 10 through 12, without trailing newline"
  },
  "author": "source-reader",
  "assertion": "Original assertion, domain, quantifiers and uniformity.",
  "comparison": "Candidate difference with a selected formal guarantee.",
  "evidence": "Exact observations and the remaining implication to check.",
  "formalSources": [],
  "dependencies": "Available premises and any unestablished bridge."
}
```

Each optional `formalSources` entry has `path`, `sha256`, `startLine`, `endLine`
and `statement`, with the exact-source rules of legacy formal references. Keep
quantitative contracts and proof-origin qualifications in the record. Capturing
it establishes no mathematical proposition. Source spans must lie in the original
scope. The CLI record bound is 1 MiB, with at most 64 formal-source references;
existing plan byte/population bounds still apply.

```sh
uv run --locked python -m ladon.entrypoint investigation observe \
  --plan runs/current/plan.json --root . --record observation.json \
  --output runs/current/plan-observed.json
uv run --locked python -m ladon.entrypoint investigation inspect-observations \
  --plan runs/current/plan-observed.json --root .
uv run --locked python -m ladon.entrypoint investigation challenge \
  --plan runs/current/plan-observed.json --root . --claim OBSERVATION_ID \
  --output runs/current/observation-challenge.json
```

Inspection supplies the `observationId`. A challenge contains the source,
assertion, formal sources and dependencies, and omits the author's comparison,
evidence and review labels. Give it and sufficient primary context to an independent
reviewer. Use response fields `reviewer`, `subject`, `challengeDigest`,
`classification`, `method`, `sourceFidelity`, `evidence` as in native review.
The subject/digest must match the challenge. The reviewer label must differ from
the author's; this checks attribution, without authenticating identity.

```sh
uv run --locked python -m ladon.entrypoint investigation ingest \
  --plan runs/current/plan-observed.json --root . \
  --packet runs/current/observation-challenge.json --response response.json \
  --output runs/current/plan-reviewed.json
```

Use unique output filenames: transitions never overwrite their inputs. Pending
or conflicting observations remain in `next` as `independent-observation-review`.
`reconcile` references the exact first response ID and retains its reviewer label
and original bytes. Resolved observation-only work can finish when its authored
survey and reviews are complete, while v3 `formalCorrespondence` remains
`incomplete-no-counterpart`. Each observation's `formalSupport` remains
`not-established` in all plan versions. A separate proof does not erase a
correspondence finding.

## Report supplementary evidence

```sh
uv run --locked python -m ladon.entrypoint investigation report \
  --plan runs/current/plan-reviewed.json --plan runs/current/plan-supplement.json \
  --root . --output runs/current/report.json
```

`report` accepts 1–16 plans with the identical original scope, `startedAt` and
budget. It permits at most 128 MiB canonical combined input/output and at most
4096 union observations or findings. It is a read-only view, not a merged mutable
plan or terminal receipt. Identical repeated plans deduplicate. A changed scope,
clock or budget, or a forked immutable first response, rejects.

The report retains plan IDs, each branch's queue and coverage, original and
corrected reviews, findings and observation records. `pendingPlanIds` follows
the actual queues across statement, method and fidelity review. Conflicting
reviews remain visible. Recorded local support, method difference, unestablished
formal bridges and `mathematicalFalsity: not-established` are separate dimensions.
Native review histories remain visible after a corrected discrepancy is aligned.

Plain-observation checkpoint/finalization receipts use
`ladon-investigation-progress-v2` and retain findings. The validator reads
historical progress-v1 and progress-v2 receipts against their original
projection and exact source/plan/time. Receipt bytes are never upgraded in
place. Observation-bearing plans require the current reader.
Neither status, report nor receipt validation replays Lean or certifies the paper.

## Attach native contract analysis

A `ladon-investigation-observation-v2` record has exactly the v1 fields above
plus `contractAnalysis`. That attachment has exactly `artifact` and `context`;
`artifact` is a native `proofir.contract-analysis` envelope, and `context` has
exactly an `artifacts` array containing its native dependencies. The target
envelope can be supplied separately from that array. Ordinary native limits
apply: 8 MiB per envelope and 32 MiB per batch, within the investigation's
existing plan limits. The ordinary `observe` CLI retains its 1 MiB record cap.

For example, prepare a new record from an authored observation and saved
native outputs, preserving the original files:

```python
import json
from pathlib import Path

record = json.loads(Path("observation.json").read_text())
record["schema"] = "ladon-investigation-observation-v2"
record["contractAnalysis"] = {
    "artifact": json.loads(Path("analysis.json").read_text()),
    "context": json.loads(Path("analysis-context.json").read_text()),
}
Path("contract-observation.json").write_text(json.dumps(record, indent=2) + "\n")
```

Use the same `observe`, `inspect-observations`, `challenge`, `ingest`,
`reconcile`, `report` and `finalize` commands above. The observation identity
binds the complete record. Its version-2 challenge includes the native
attachment under the challenge digest while omitting the proposed comparison,
evidence and review labels. Selected `formalSources`, source locations,
original responses and reconciliations remain in contract findings and final
receipts, including when the plan's `claims` array is empty.

Native validation checks content identities, reference closure and deterministic
conditional results against the supplied inputs. It does not launch a fresh
Lean check, interpret prose, or establish that the attached graph represents
the quoted source. Source binding and attributed review remain separate.

Contract findings retain the full attachment and expose these independent
`contractDimensions`:

| Dimension | Meaning |
| --- | --- |
| `sourceFidelity` | Attributed effective fidelity review, including unresolved or conflicting reviews |
| `extractionCompleteness` | `not-established`; child coverage does not certify the whole source |
| `routeSupport` | `not-established`; narrower native authority remains in the attachment |
| `methodCorrespondence` | Attributed effective method review, separate from endpoint agreement |
| `mathematicalFalsity` | `not-established`; a reviewed mismatch does not prove the proposition false |
| `exploredPopulation` | Exact native coverage with `declared-child-coverage-only` authority |

Aggregation retains each investigation branch's plan ID, reviews and pending
work; it does not sum overlapping native coverage or infer an upstream audit
plan identity. A stronger endpoint or an aligned branch does not remove the
other branches' method differences or unresolved work.

When a contract observation is present, inspection uses
`ladon-investigation-observations-v2`, reports use
`ladon-investigation-report-v2`, and new progress receipts use
`ladon-investigation-progress-v3`. Plain observations keep their existing
versions and projections. The receipt validator preserves historical v1/v2
semantics and rejects a new contract receipt relabeled as an old version.

The portable CLI contract is exercised by
`tests/test_investigation_observation_cli.py`. No model service or target research
checkout is needed for that test. Known answer-informed development replay is
recorded separately in the owning OpenSpec change; it is not a blind evaluation.
