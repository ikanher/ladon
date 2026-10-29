---
name: ladon
description: Find reusable Lean theorems from hypotheses and desired conclusions, check candidate applications or source goals, and inspect proof dependencies, architecture, and prose/formal correspondence with Ladon.
---

# Ladon

Use the installed `ladon` CLI. Maintain this skill in `codex-skills/ladon/`;
consuming repositories should symlink to it. Resolve the symlink before reading
references. Read only the reference for the operation being performed.

## Start from the mathematical obligation

For proof assistance, theorem reuse comes before writing new infrastructure.

1. **State the inputs and wanted output.** Record the types, hypotheses,
   quantifiers and exact conclusion. Preserve the underlying laws, reference
   measure, normalization, parameter domain and inequality direction. For an
   existing source goal, prefer capture over reconstructing its context.
2. **Search proposition types.** Query distinctive definitions or expressions
   in both the hypotheses and conclusion. Use `search type-text` for a cheap
   shortlist; use name search when a declaration or owner is known. Broad topic
   words such as `Gaussian` or `GDP` are poor substitutes for a typed target.
3. **Inspect equivalent formulations and adapters.** Read candidate statements,
   protected definitions and relevant proof bodies. Search their consumers with
   `rg`: normalization, translation, scaling, product and postprocessing lemmas
   may already connect them to the target. A result under a historical method
   namespace may be generic; inspect its assumptions before rejecting reuse.
4. **Check the actual application.** Use the smallest compiled owner context
   that contains the candidate and the goal's definitions. Supply dependent
   hypotheses with `discover --local`, or capture the actual source goal. Keep
   the residual propositions; a stronger theorem may require algebra or a
   change of variables that one-step application does not solve.
5. **Classify the remaining work precisely.** Distinguish a checked direct
   application, existing ingredients needing an adapter, a new argument, and
   an unresolved search. Give the exact declarations and remaining premises.
   An unchecked task box is not evidence that all its ingredients are missing.

Before calling a proof missing, inspect plausible owners and their consumers.
Before calling it complete, check that the target produces every premise and
uses the result on the actual mechanism. A wrapper assuming the desired bound
is not its producer. Keep the intended theorem unchanged during certification.

```bash
ladon proof-search search type-text \
  --repo-root "$PWD" --pattern 'DistinctiveDefinition' \
  --scope namespace --root Project.Namespace --limit 20 \
  --diagnostic-limit 10 --freshness verify --format json --output -
```

This searches stored type **text**, not arbitrary logically equivalent
propositions. `discover --pattern` also starts with a lexical shortlist; only
its subsequent Lean checks assess applications. Search input predicates and
output expressions separately when a whole formula is too restrictive. Never
infer semantic absence from an empty or bounded lexical result.

Use exact module names for `module`, `imports`, `closure` and `neighborhood`
scopes, and repository-relative Lean paths for `file`. Inspect exact matches
separately from suggestions, along with scope, omissions and truncation. If
results are noisy or truncated, refine the pattern or owner scope before
requesting a larger output. Use `rg` for bodies and references absent from the
index; inspect the actual source before reuse.

## Check the installation and index

Use `ladon -h` for common workflows, `ladon -h --verbose` for the full command
catalog and analyzer options, and `ladon COMMAND --help` for exact arguments.
Check installed help before using unfamiliar options. Record `ladon version
--json` for field tests and authority-sensitive checks; a release number or
observed checkout commit alone does not identify installed bytes. Installation
and capability details are in
[navigation-and-checks.md](references/navigation-and-checks.md#invoke-ladon).

```bash
ladon proof-search index status \
  --repo-root "$PWD" --changed --format json --output -
```

The default disposable index is `.ladon/index/proof-search.sqlite`. For stale
supported sources, use `index update`; for an absent index, use `index build`.
Follow a `full-build-required` diagnostic instead of repeating update. Keep one
writer and preserve other workers' state. Read
[index lifecycle guidance](references/navigation-and-checks.md#build-the-project-local-index)
when creating, recovering, pruning or changing storage limits.

Check freshness once for a query batch, then use `--freshness stored` against
that recorded generation when inputs have not changed. Stored searches do not
check freshness themselves. Recheck after edits or suspected concurrent changes.
A lexical refresh does not refresh compiled lineage or make imports current.
Build changed owners before asking Lean to check their applications.

For 0.4.0, explicit `index update` recovers indexes from lexical extractors
v3/v4/v5 to v6 without source edits, preserving retained evidence. It repairs
scope naming and signature boundaries. A qualified-name miss can still reflect
compiler-generated declarations outside the lexical population; lexical headers
also omit elaborated section variables and inferred instances. Inspect the
pinned Lean type before constructing an application.

## Choose the appropriate check

| Need | Operation and required reference |
| --- | --- |
| One candidate for a closed proposition | `proof-search check candidate`; [candidate checks](references/navigation-and-checks.md#check-one-candidate-explicitly) |
| Candidates for a proposition with supplied hypotheses | `proof-search discover --goal ... --local NAME:TYPE`; [verified discovery](references/verified-discovery.md), read before running |
| Application or proof term in an actual file context | `proof-search goal capture`, then `goal complete`; [source goals](references/source-goals.md) |
| Existing proof's compiled dependency closure | `theorem lineage`; [lineage](references/navigation-and-checks.md#query-exact-compiled-lineage) |
| Module ownership, imports or architecture | Analyzer, starting with `preview` if scope is uncertain; [architecture](references/navigation-and-checks.md#run-architecture-analysis) |

`check candidate` does not accept `--local`; discovery accepts ordered dependent
locals and proposition goals, not arbitrary `Type`-valued goals. `--module`
selects the checking environment; `--scope` and `--root` restrict discovery's
shortlist. Neither is a recursive proof search that automatically discharges
all residuals. Use ordinary Lean composition when several ingredients must be
combined, and label that evidence separately from Ladon observations.

Live checks require a trusted repository and existing compiled dependencies.
Verify direct-Lean execution before using the shared checkout; older or
unverified Lake-backed checkers belong in a disposable worktree. Current
checkers must not reconcile, delete or fetch packages. Use the repository's
explicit pinned executables for authority-eligible checks, with finite time,
output and RSS bounds. Coordinate Lean execution with other builds. Missing
compiled inputs require an explicit repository build, not a hidden repair.

## Interpret evidence and resource limits

- Lexical matches and text-resolved import edges are navigation evidence.
  A source match, hash, successful command exit or artifact attachment does not
  establish an application or correspondence claim.
- A closed accepted application checks the recorded route. An application with
  residuals leaves obligations. Rejection concerns that application; it does
  not refute the goal. Read authority, freshness, coverage and completeness
  separately; omitted evidence is not complete evidence.
- Preserve rejected, provisional, failed and unassessed rows. A timeout or
  memory limit is an operational failure, not a negative theorem result.
- Compact results may omit canonical detail. Expand registered evidence in
  the same evidence store when requested by the result, or when limitations
  are missing; rerunning a check creates a new observation.

Choose the smallest useful checking context and a bounded candidate population.
A small shortlist does not guarantee low memory use: environment loading and
semantic evidence extraction can dominate. Do not assume reducing batch size
will resolve a failure that occurred before any candidate was assessed.

Honor the task's existing resource limits; example budgets are not permission
to increase them. If a diagnostic says `Stop progress and report back to user:`,
stop dependent checks and report the command, configured limit, observed peak
and retained evidence. Do not silently raise the cap, reset the deadline, or
repeat the same failing check. Read-only source/type searches can still narrow
the mathematical gap. A focused ordinary Lean check may provide separate
validation when feasible within the authorized budget and workspace policy;
it does not repair the failed Ladon observation or bypass the resource limit.

## Other workflows: load details only when needed

- For a conventional explanation review, start with
  [proof explanations](references/proof-explanations.md). Actual formal
  correspondence checks use
  [ProofIR and correspondence operations](references/proofir-and-correspondence.md).
  Ladon does not automatically certify an entire prose proof.
- For native ProofIR validation, stored routes, derivation slices and artifact
  identities, use [ProofIR operations](references/proofir-and-correspondence.md#query-native-proofir-v3).
  Only native v3 is supported; stored evidence does not become fresh checking.
- For supplied result manifests and exact target association, use
  [result manifests](references/result-manifests.md). Offline integrity and
  target resolution are separate from Lean checking and source fidelity.
- For opt-in source snapshots, typed Real-bound observations, native predicate/scalar
  admission, attributed Real prose readings and exact conditional connections,
  propagation, application probes and countermodel refinement, read
  [contract analysis](references/contract-analysis.md).
  Authored inputs and independent source-fidelity review remain necessary.
- For naming reviews, read [naming audits](references/naming-audits.md).
- For evaluating Ladon or preparing field feedback, read
  [testing](references/testing.md) before running tests. Its protocol is not
  required for ordinary navigation. Use the reuse scenario there when testing
  whether proposition search prevents duplicate proof work.

Lineage describes the stored proof's dependencies, not every possible proof.
Use `--refresh never` for stored-only lineage; supervised refresh can run Lean.
Architecture is text-backed by default and does not build unless `--build`
is explicitly requested. Keep expensive scopes and limits explicit. Report
coverage and omissions beside conclusions, rather than treating a clean bounded
report as complete proof closure.
