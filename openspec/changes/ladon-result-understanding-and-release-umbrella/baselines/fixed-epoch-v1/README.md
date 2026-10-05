# Fixed-epoch exposition baseline v1

Completed on 2026-10-02 against installed Ladon candidate
`a31a6d64d4017abd72be0ba6983462f88a37ed37`. This baseline records what an LLM
could learn from the exposition using today's Ladon, what required manual
reading, and what the current product cannot do. No production code was changed
during this baseline. The author and reviewer are the same Codex agent.

The result is a **completed qualitative baseline**, not a proof audit, held-out
evaluation, or completion of the planned dossier/guide/bundle capability.

## What the exposition says

The benchmark holds clipped gradients fixed, uses independent Poisson
participation, and compares variance at a fixed expected participation budget.
It does not compare trained models or optimizer trajectories.

- **Full batch is conditionally optimal.** For the all-horizon result, the
  calibrated signal satisfies `a² ≤ 6Eε/(3E+2)`. The conclusion holds at every
  finite `T > E` and every nonnegative energy. It is not an unconditional claim
  that larger batches always win.
- **The finite counterexample matters.** At sensitivity 1, `E=2`, `T=3`,
  `ε=1/4`, `δ=3/4`, the sampled privacy variance is at most `5/32`, below
  `4/25`, which is below the full-batch variance. The reversal holds throughout
  `0 ≤ S ≤ 9/400`. We retained the separate lower-bracket and full-batch
  comparator declarations; the final comparison theorem alone does not state
  every rational bound in the article.
- **Transcript and average-only release differ.** Transcript-calibrated
  variance diverges in the strictly subcritical sparse regime, despite raw
  noise tending to zero. The average-only variance has a uniform feasibility
  bound. Those conclusions concern different released observations and are
  not contradictory.
- **The article is broader than the pinned formal claims.** Its average-only
  conclusions and the pointwise equality endpoint `T=2E, a²=2ε` are conventional
  additions according to the coverage addendum. The pinned pointwise transcript
  condition is strict at that endpoint.
- **Sparse statements require translations.** The addendum relates the general
  offset theorem to a capped fixed-budget schedule and translates
  `log(1/q)=log(T/E)` into the displayed leading equivalents. These are recorded
  as attributed correspondence reasoning, not checked Lean adapters.

These answers came from manual reading assisted by Ladon navigation. They are
not answers generated or certified by `ladon result validate`.

## Frozen inputs and scope

[inputs/exposition.tex](inputs/exposition.tex) is the exact captured manuscript;
[inputs/formal-coverage.md](inputs/formal-coverage.md) is its current coverage
addendum. [inputs/identity.json](inputs/identity.json) records the source paths,
content hashes, dirty working-tree status and installed candidate identity.

The source supplement is r05, SHA-256
`f8e2839b485b073353df435dd3a9ea3f7d53abb48b14b99f55f3238e0096327b`.
Its archive hash was verified. Every selected target's source-file bytes were
compared with the corresponding archive member and matched. Twenty exact name
queries through the installed CLI returned the selected declarations, with
verified-fresh lexical evidence. Their complete signatures, paths and hashes
are in [inputs/target-signatures.json](inputs/target-signatures.json).

The target environment digest hashes [inputs/environment.json](inputs/environment.json):
an explicitly declared archive/toolchain/Lake-metadata descriptor. It is **not**
a canonical Lean environment receipt. No `subjectRef` or successful checker
reference has been invented. This baseline does not replay r05.

The inventory includes **all 18 labelled theorem, lemma, proposition and
corollary environments** in this captured TeX. It excludes unboxed assertions,
individual proof steps, figure/numerical validation and citation review.
`claimInventory.coverage=complete` refers only to that syntactic inventory.
Component boundaries and mappings are model-authored. Nothing here asserts
independently observed completeness of mathematical formalization.

[claim-matrix.json](claim-matrix.json) contains the per-statement decisions:

| Component assessment | Count | Meaning |
| --- | ---: | --- |
| Declared mapped | 11 | Components of eight statements linked to 20 supplied declarations |
| Conventional-only | 8 | The coverage addendum explicitly places these exact components outside its pinned formal claims |
| Not assessed | 10 | No individual correspondence assessment in this baseline; not evidence of absent formalization |
| Reported implication, unmapped | 1 | Closed secant cases described by the addendum via the pointwise domain; no checked adapter supplied |

These counts describe a chosen inventory; **11/30 is not a proof-coverage or
understanding score**. The offline validator reports 19 unmapped components
without distinguishing their reasons. That distinction requires the authored
claim matrix and coverage addendum.

## Workflow results

| Question/task | Result with today's Ladon | Manual work or limitation |
| --- | --- | --- |
| Start from the paper's terminology and find its main result | Earlier conceptual query returned no results; exact/refined navigation worked | Coverage addendum supplied formal names; there is no TeX ingestion |
| Locate the mapped targets | All 20 exact-name queries found their intended declaration | Source/archive comparison performed outside Ladon |
| Distinguish the manuscript from the pinned formal claim | Differences and partial components can be represented in the manifest | Agent supplied all mappings and review rationale; validator does not establish correspondence |
| Identify which claims remain uncovered and why | Validator returns aggregate unmapped count | No per-claim decision card; read the manifest and claim matrix |
| Inspect dependencies/trust | Prior compiled lineage succeeded and cached successfully | External frontier remains; lineage is not theorem replay or exposition correspondence |
| Check a reusable lemma | Prior direct check reached the 10,500-versus-10,000 imported-module limit | No acceptance observed; no new Lean attempt in this baseline |
| Preserve review history after an edit | Both claim and target edits make the old review historical | Tracks declared revisions; does not monitor external TeX files automatically |
| Get a reading guide or integrated dossier | `result guide` and `result inspect` reject invocation | These operations are unimplemented |

The earlier navigation/resource experiments are retained in the
[field report](../../field-feedback-matrix-fixed-epoch.md). Selected historical
outputs are copied into `observations/prior-field/` with their original command
and candidate identities; they are not new runs of this baseline.

## Replayed CLI scenarios

[manifest.json](manifest.json) contains the exact supplied statements, partial
component mappings, pinned-source target metadata and 11 revision-bound model
reviews. All reviews explicitly retain differences or scope limitations.

Nine scenarios passed their expected outcomes on installed Python 3.11 and
3.12 distributions:

| Scenario | Expected and observed result |
| --- | --- |
| Original manifest, JSON | Valid offline integrity; 11 current reviews; canonical resolution not assessed |
| Original manifest, text | All represented fields equal the JSON result |
| Synthetic claim edit with recomputed revisions | One review becomes historical; ten remain current |
| Synthetic target edit with recomputed revisions | One review becomes historical; ten remain current |
| Deliberately nonexistent declaration name | Still valid metadata, one historical review; canonical resolution remains not assessed |
| Link to an undeclared component | Rejected, exit 2, structured diagnostic, no success output |
| Changed statement without its new revision | Rejected, exit 2, structured diagnostic, no success output |
| `result inspect` | Unavailable command, exit 2 |
| `result guide` | Unavailable command, exit 2 |

The nonexistent-target case is particularly important: successful validation
cannot be presented as declaration existence, applicability or proof checking.
The synthetic edits test declared revision binding; they are not changes to the
real exposition or Lean sources. Expected unavailable outcomes count as a
successful baseline capture, not successful feature implementation.

## Reproduce and compare later

Use an installed Ladon environment with the experimental manifest command:

```bash
/path/to/installed/bin/python -I /path/to/fixed-epoch-v1/replay.py \
  --output-dir /tmp/fixed-epoch-baseline-new-run
```

The output directory must not already exist. The runner derives the console
path from that Python interpreter, with optional `--ladon` override, and stores
exact commands, synthetic inputs, stdout, stderr, exit status and elapsed time.
It starts no Lean process and needs neither the external repository nor an
index. Version identity and content hashes for the recorded runs are in
[verification.json](verification.json); [inventory.json](inventory.json) binds
the frozen files and captured outputs. This is a local baseline fixture, not
Ladon's future portable-release bundle format.

For a later comparison, retain v1 inputs and outcomes, install the new candidate
separately, and replay into a new directory. A changed result, including newly
implemented dossier/guide behavior, should produce an explicit baseline delta.
Do not silently rewrite the expectations to make the new candidate pass.
The live name queries additionally require the external repository and index;
their exact argument vectors are recorded in `observations/search-commands.json`.

## Concrete next improvements

1. Expose component-level mapping and omission reasons in a result dossier,
   with a direct route back to the precise paper statement and target.
2. Resolve supplied target identities against canonical evidence while
   retaining article/archive/working-tree revision differences.
3. Present correspondence differences such as strict versus closed endpoints
   and transcript versus average-only claims in compact output.
4. Add a reading guide that explains the conditional theorem, counterexample
   and sparse-limit distinction before presenting the dependency graph.

The baseline can be completed while those features remain absent. The result
umbrella's broader alpha scenario and prerequisite exits remain open.
