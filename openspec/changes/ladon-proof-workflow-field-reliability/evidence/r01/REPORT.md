# Field reliability repairs — Ladon 0.2.1

The three reported R01 failures now pass against the built 0.2.1 wheel:
same-file goal completion, transitivity evidence, and the late large-context
capture. No source or build output in matrix-factorization was modified by
this work. The field harness copies the frozen source into a disposable project
and reads the existing pinned Lean 4.33.0 compiled imports.

## Outcomes

| Case | Installed outcome |
| --- | --- |
| Early goal, earlier `potential` definition | `completed`, separate compiler replay accepted, complete permitted-axiom result |
| `le_trans` and `pow_le_pow_of_le_one` | Available batch; transitivity retains residuals, power lemma closes the goal |
| Late goal at line 236, column 6 | Captured twice with consistent identities; 2,786,774-byte helper frames within 64 MiB |

The former `he.valueStructural` tree was 108,297,084 bytes. Its complete shared
constructor graph is 89,489 bytes. The graph retains names, levels, binder
annotations, metadata, local references and values. Display text remains
separate. Both capture and completion compose the same packaged codec.

The installed late capture used 8,984,768,512 bytes peak process-tree RSS;
early capture used 8,978,059,264 and completion 9,016,504,320. These are about
8.37–8.40 GiB, below the unchanged 32 GiB default. They remain substantial
resource use. These shared-host observations are not a performance comparison.
`installed-field-summary.json` supplies receipts, identities, selected local
sizes, residuals and replay evidence; full raw results are retained locally
under `installed-field/` but omitted from the review ZIP.

Completion now exports a private snapshot of the selected source environment
and imports it in a separate compiler process. It does not compile the
unfinished tail or establish the enclosing declaration. Earlier admitted
dependencies still fail the trust policy. The private context digest/size is
reported and temporary artifacts are removed. Ordinary installed CLI capture
and completion also passed on a same-file witness with an unfinished tail
(`installed-cli-completion.json`).

Substitution identities are `binder:INDEX:NAME`, retaining repeated names as
distinct binders. Canonical contradictory bindings remain rejected. A failing
candidate's artifacts are excluded while independently validated siblings
survive in either order, with candidate-specific diagnostics. Compact summaries
retain the candidate limit and separate closed from residual applications;
the historical aggregate still includes both.

Lexical build progress reports discovery, bounded module counts, validation and
publication through existing stderr events. Quiet mode, busy refusal and failed
publication are covered. Publication failure preserves the old database and
does not emit completion.

## Qualification

- Full strict run: `uv run python scripts/python_quality.py --strict`, exit 0,
  3,254 tests; Ruff, radon, Vulture and compile checks passed. Its collection
  preceded the final two additional graph/limit tests.
- Post-version focused run: 13 passed, recorded separately rather than added
  to the full-run count. Final full-scope Ruff and radon/Vulture checks passed.
- Built wheel: 301 relevant contracts passed on Python 3.11 and 301 on 3.12;
  both import origins are installed virtual environments and both report
  version 0.2.1. `installed-check.json` names the wheel digest and test files.
- Installed Python 3.12 field reproduction and ordinary CLI smoke passed.
- Independent Luna audit: initial 8 + 42 focused tests, followed by a 24-test
  refresh; no actionable runtime defect found. The reported missing progress
  failure controls were added. Board posts 979 and 983 preserve the review.
- OpenSpec strict validation and `git diff --check` passed. Frozen test records
  verify without mismatches. Original tests affected by the new replay contract
  or quality-only organization remain in `historical-tests/` with explicit
  supersession; their assertions were not weakened.

Initial failures are retained: missing size telemetry, the old compact equality
expectation after additive fields, test complexity/import lint, and an incorrect
test expectation for the existing busy-builder exit class. These were repaired
without relaxing production validation or execution bounds. Constructor-test
lint added explicit `check=False`, equal to subprocess's previous default;
the installed test listing retains its former filename, with identical assertions.

`candidate-hashes.json` binds the integrated runtime sources and package/lock
metadata. Source captures bind helper bytes: recapture after upgrading.
Documentation and both maintained Ladon skills describe this boundary.

## R02 and stopping point

R02 separately reports useful lineage views, a correct concurrent-source guard,
the retained-lineage update limitation, and confusing traversal-row budgets.
All 15 supplied hashes and 12 JSON files passed archive checks. See
`FEEDBACK_R02_TRIAGE.md`. The cap's current meaning is documented; a stored
distinct-node count cannot guarantee a sufficient route traversal budget.

Retained-lineage migration is still outside this repair contract. A full build
to a new index path preserves the old evidence-bearing file. Do not silently
rebind old compiled evidence to fresh lexical rows. The delta review should
decide the smallest safe generation-preserving update contract and whether a
focused budget-label repair is useful. No further proof-interface expansion
or new mathematical uptake experiment follows from these fixes.

These are engineering and exact field outcomes, not comparative LLM benefit,
human understanding, prose certification or renewed theorem qualification.
