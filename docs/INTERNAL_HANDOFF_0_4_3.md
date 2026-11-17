# Internal Ladon 0.4.3 handoff

From `lean/matrix-factorization`, use the current Ladon source checkout at
`../../ladon`, rather than a potentially older pip-installed executable:

```bash
uv run --project ../../ladon --locked python -m ladon.entrypoint version --json
git -C ../../ladon rev-parse HEAD
git -C ../../ladon status --short
git rev-parse HEAD
git status --short
```

For another layout, replace `../../ladon` with the selected checkout path.
Read [the release notes](RELEASE_0_4_3.md) for exact qualification and limits.
Use `--help` on the chosen command when its syntax is unfamiliar.

## Use existing evidence when it answers the question

```bash
uv run --project ../../ladon --locked python -m ladon.entrypoint \
  investigation inspect --plan /path/to/checked.json \
  --context-max-bytes 8388608 --output /path/to/new-inspection.json
```

Keep new outputs outside frozen evidence directories. This reads stored context
and bindings without replaying Lean. Complete coverage means all requested
stored evidence was retrieved. `matched-stored-records` does not establish fresh
replay or certify the passage's interpretation. Inspect omission reasons and
exact source, formal objects, goals, polarity and receipt identities.

Read structured argument definitions and named conclusion predicates. A
`premiseScope` with zero direct obligations does not mean the source assumptions
were reconciled. New `checkRoleCounts` separate the two typing roles from
mathematical attempts; historical counters retain their old meaning.

Before inspecting a candidate theorem, record the actual passage's objects,
assumptions, quantifiers, desired conclusion and ambiguous readings. Reconcile
later additions explicitly. Check one consistent application under that source
context and its conclusion transfer. A missing premise or changed parameter
schedule blocks that route; another route may still prove the claim. Refutation
needs separate evidence satisfying all original assumptions.

Follow [the application recipe](PROOF_CORRESPONDENCE_AUDIT.md#check-a-complete-application-under-the-source-assumptions)
and [the native MF example guide](PROOF_CORRESPONDENCE_AUDIT.md#read-the-native-mf-examples).
A per-input common limiting law does not provide finite-run equality, a uniform
rate or finite privacy accounting. Previously checked evidence must be compared
with the current passage before reuse. Obtain fresh replay when the task needs
current proof assurance; retain replay and trust outcomes and resource failures.

## Return actionable feedback

Preserve the exact command, runtime version/identity, Ladon and target revisions,
dirty state, selected source span/theorem, input evidence identities, resource
limits, JSON output and stderr. Describe the expected result and the actual
support or unresolved obligations. Distinguish tool failure, missing bridge,
interpretation disagreement and mathematical discrepancy. Include time to a
useful query and a justified result, preparation/review effort when known, and
any manual workaround. Do not substitute counts of proofs or tool calls for
reader benefit. New diagnostic work should answer a demonstrated need.
