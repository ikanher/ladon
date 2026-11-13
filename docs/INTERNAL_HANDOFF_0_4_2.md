# Internal Ladon handoff for matrix-factorization audits

Use the Ladon source checkout at `../ladon` from the `matrix-factorization`
repository. Do not rely on a globally installed `ladon` command: the commands
below run the selected checkout directly.

From the matrix-factorization root:

```bash
uv run --project ../ladon --locked python -m ladon.entrypoint --version
uv run --project ../ladon --locked python -m ladon.entrypoint \
  proof-search index status --repo-root "$PWD" --changed
```

Before reporting evidence, record the Ladon checkout identity and target
revision:

```bash
git -C ../ladon rev-parse HEAD
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
focused completion tests passed; the full strict quality gate and isolated
distribution gates have not passed on this shared research worktree. This
handoff is for internal use and makes no claim of autonomous exposition-error
detection or measured incremental detection benefit.
