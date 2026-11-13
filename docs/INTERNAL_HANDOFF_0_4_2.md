# Internal Ladon handoff for matrix-factorization audits

Use the Ladon source checkout at `../../ladon` from the `matrix-factorization`
repository. Do not rely on a globally installed `ladon` command: the commands
below run the selected checkout directly.

From the matrix-factorization root:

```bash
uv run --project ../../ladon --locked python -m ladon.entrypoint --version
uv run --project ../../ladon --locked python -m ladon.entrypoint \
  theorem lineage Fully.Qualified.theorem --repo-root "$PWD" \
  --refresh never --view summary --format json --output -
```

Replace `Fully.Qualified.theorem` with the declaration being inspected.
Stored lineage performs its own source validation. Use `proof-search index
status --changed` for comprehensive diagnostics when needed; it can also verify
large retained history archives and is unnecessary before each lineage query.

Before reporting evidence, record the Ladon checkout identity and target
revision:

```bash
git -C ../../ladon rev-parse HEAD
git rev-parse HEAD
git status --short
```

For a proposed theorem application, first record the source claim, objects,
assumptions, quantifiers, conclusion and uncertain readings. Capture the
source-context goal, inspect the selected theorem application and its residual
obligations, then use `goal complete` when a concrete checked term is available.
Require accepted compiler replay and trust evidence before calling that route
completed. Preserve ordinary Lean evidence separately if native completion
rejects a valid term. The complete recipe is in
[`PROOF_CORRESPONDENCE_AUDIT.md`](PROOF_CORRESPONDENCE_AUDIT.md#check-a-complete-application-under-the-source-assumptions)
and the bundled
[`Ladon skill`](../skills/ladon/SKILL.md).

For formula or object-map questions, substitute proposed expressions into the
source definitions and retain exact signs, domains, laws and pushforwards. A
matching theorem name, dependency lineage, complete premise table, or successful
Lean build does not by itself establish that the source statement was mapped
correctly. Report unresolved interpretation or provider frontiers explicitly.

Ladon 0.4.2 provides bounded proof extraction (default depth 128, configurable
with `--max-depth`) and a closed-proof printer budget of 200,000 steps. Large
expressions may receive an explicit bounded failure. The printer regression and
focused completion tests, 41 isolated installed-CLI contracts, and pinned Lean
integration passed.
The full strict quality gate remains open due to existing complexity findings. This
handoff is for internal use and makes no claim of autonomous exposition-error
detection or measured incremental detection benefit.

## Feedback from internal use

Save the exact command, Ladon revision and version, target revision, selected
source/theorem, resource limits, expected result, and actual result. Retain the
JSON response and stderr. Distinguish a mathematical discrepancy, an incorrect
source interpretation, a missing formal bridge, and a tool failure. A small
reproducible example is more useful than only a final verdict. Record any
manual workaround so the next release can address the failed operation.
