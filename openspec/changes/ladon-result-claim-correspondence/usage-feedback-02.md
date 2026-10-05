# Stored-target resolver usage feedback

Date: 2026-10-03. Reviewer: the implementation-session LLM, not an independent
reviewer. Candidate: `7030ec3aabdd6538b1a6c8782b877076697991b8`.
Scope: qualitative development feedback on explicit stored target association.
The positive fixture is synthetic; no mathematical correctness or human
understanding follows from its successful association.

## Task and exact observations

Decide whether an explicitly supplied formal target has an exact stored canonical
association, then repeat the decision on the unchanged fixed-epoch exposition.
The full command vectors, input paths, output digests, exit codes and runtime
identities are retained in
`/tmp/ladon-prerequisite-finish-37s2vir4/result-usage-r41/commands.json`.
Both scenarios ran through the installed console outside the source checkout on
Python 3.11 and 3.12; each returned 0 and byte-identical JSON across runtimes.

### exact-synthetic-stored-target

```bash
/tmp/ladon-result-resolution-r41-iqb6qd83/py311/bin/ladon result resolve /tmp/ladon-prerequisite-finish-37s2vir4/result-usage-r41/synthetic-manifest.json --artifact /tmp/ladon-prerequisite-finish-37s2vir4/result-usage-r41/artifact-0.json --artifact /tmp/ladon-prerequisite-finish-37s2vir4/result-usage-r41/artifact-1.json
```

Output: `/tmp/ladon-prerequisite-finish-37s2vir4/result-usage-r41/exact-synthetic-stored-target-py311.stdout`; 2237 bytes.

One target and one link resolve with `exact-stored-subject-environment-type-source`. The source anchor retains its artifact ID, index and environment/fingerprint basis. Checking and source freshness remain `not-assessed`; the project revision remains `producer-declared`. This binds supplied stored identities and does not turn the accompanying model review into proof acceptance.

### frozen-exposition-no-canonical-inputs

```bash
/tmp/ladon-result-resolution-r41-iqb6qd83/py311/bin/ladon result resolve /tmp/ladon-result-resolution-r41-iqb6qd83/candidate/openspec/changes/ladon-result-understanding-and-release-umbrella/baselines/fixed-epoch-v1/manifest.json
```

Output: `/tmp/ladon-prerequisite-finish-37s2vir4/result-usage-r41/frozen-exposition-no-canonical-inputs-py311.stdout`; 11187 bytes.

All 20 targets and 11 links remain unresolved with `canonical-subject-reference-absent`. The frozen manifest revision is `sha256:0483362a398ef90f8fea84c8cd442d581f9ec4d6d512f5537e678617970db89b`. Matching declaration names and stored correspondence reviews cannot supply absent canonical subjects. The earlier offline validator outputs remain unchanged.

## Findings and limits

The explicit `resolutionScope`, per-target reason and separate checking/freshness
fields support the intended decision without interpreting `resolved` as theorem
acceptance. This observation was reproduced on both runtimes. It is development
usage by the implementation agent, not a comparative benefit measurement.

The real example produces 11,187 bytes, largely because it repeats the missing
reference explanation for 20 targets. Exact `--target ID` selection provides a
bounded drill-down; the input manifest remains the source for full statements and
assumption differences. The next dossier should place those decision-relevant
statements, differences and component assessment reasons beside the target
association, as already required by parent tasks 3.1–3.6. No new task or scoring
campaign was introduced from this feedback.

The canonical envelopes were created as synthetic test inputs, not extracted
from the real fixed-epoch proof. No Lean run, reviewer authentication, live Git
freshness check, semantic equivalence check or independently measured improvement
was attempted in these two usage scenarios. The frozen baseline's original inputs,
outputs and limits remain immutable. This report does not complete the later
core dossier/guide/bundle usage milestone.
