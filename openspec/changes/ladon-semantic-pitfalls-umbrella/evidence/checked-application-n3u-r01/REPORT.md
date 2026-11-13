# N.3u — usable checked-application path

N.3u is complete for the two concrete source-goal wrappers retained here. This is exposed development with a fresh invocation user, not fresh mathematical discovery or independent mathematical review.

## Result and reader consequence

| Route | Result | Authority |
| --- | --- | --- |
| Faithful source context plus rearranged conclusion | `completed`, zero residuals | Whole term checked at captured source goal; independent compiler replay accepted; complete trust evidence contains only Classical.choice, Quot.sound and propext. |
| Same application after removing source state nonnegativity, expression-form hole | `incomplete`, one residual | Actual obligation: `∀ᵐ (ω : Ω) ∂μ, ∀ (n : ℕ), 0 ≤ X n ω`. Replay not run and trust unavailable for this unfinished term. This blocks support by this route, but is not proof of source falsity. |
| Omission with a tactic `?_` hole | `trust-rejected` | Lean's tactic elaboration admitted the hole as sorry; replay saw sorryAx. Its empty residual list cannot establish support. Keep this failed attempt as evidence and use expression-form terms when residual diagnosis is needed. |
| Fresh Luna-medium invocation of faithful wrapper | `completed` | Fresh-context user reproduced capture and completion with replay and trust accepted using documented arguments. Exact timings/argv are in FRESH-USER.json. |

The faithful wrapper's source goal moves the limit existential before the B-summability conclusion. The term must apply the owner and transfer that conjunction/existential structure. It is not a theorem checked against its own retrieved type. The omission wrapper differs only by the missing source premise. No original Lean theorem or proof was changed.

No counterexample realization or seven-case certification is claimed. The complete source interpretation is attributed, including real Summable/absolute-summability correspondence. A measurable-random-variable assertion is not substituted for the wrapper's explicit samplewise limit statement. Residual context includes an implementation-detail current-example local; it must not be promoted into a usable assumption, as required by existing capture/completion policy.

## Exact delivered environment and commands

Working project: `/home/codex/projects/ladon/temp/checked-application-n3u-r01/project`. Original five Mf source modules, compiled project libraries and root Lake metadata were copied from the retained local evaluation project. `.lake/packages` links to that local project's dependency cache; no path depends on the live matrix-factorization donor. This is cache reuse, not an offline standalone distribution. The original capsule archive remains separate and untouched. No capsule replay was needed for this source-goal route.

`INPUTS.json` records exact source file/module/positions and digests. N3Faithful.lean uses line 20, column 2; N3Omission.lean uses line 19, column 2. `N3OmissionExplicit` aliases the same unchanged omission source and capture, using a different term only. The wrapper's `skip` exposes an unfinished goal; it is not proof authority. Completed results independently check the submitted term without using an enclosing admitted proof.

Run from the Ladon root with `PYTHONPATH=src .venv/bin/python`:

```
openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/checked-application-n3u-r01/RUN.py capture N3Faithful
openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/checked-application-n3u-r01/RUN.py complete N3Faithful
openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/checked-application-n3u-r01/RUN.py capture N3Omission
openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/checked-application-n3u-r01/RUN.py complete N3OmissionExplicit
```

The runner refuses output collisions. These are the recorded invocations, not permission to overwrite saved evidence. For a new user, use fresh output filenames, as demonstrated by FRESH-USER.json. Every `*.request.json` records the expanded direct CLI argv, with source, module, exact term, pinned executable paths and output location. No long owner type was manually transcribed as a query.

## Bounds and limits

SESSION.json records the fixed 3600-second stage deadline. Root RUN.py caps each supervised operation at min(600 seconds, remaining stage time), 12 GiB process-tree RSS and 16 MiB output, retaining process results and streams. The fresh user used the same per-operation bounds and completed within the stage deadline. Observe complete reports' semantic status; CLI exit zero occurred for completed, incomplete and trust-rejected results.

Root operations took approximately 20.55s and 27.98s for faithful capture/completion, 13.99s and 26.41s for omission capture/tactic-hole completion, and 21.90s for the expression-form incomplete result. The fresh invocation user recorded 13.45s and 25.62s. These are observed invocation times, not complete preparation, mathematical review or token costs. Root receipt peak sampled RSS is recorded in RESULT.json. No production code or frozen N.3b input was changed, and no performance optimization is justified by this qualification alone.

Existing capture/completion is sufficient to show the selected premise gap and accept the complete faithful route. The difference between tactic admission and expression residuals is a concrete recipe instruction. It does not establish a need for another checker. N.3c still owns the remaining controls, source-setting counterexamples, consolidation decision and verified guide/skill updates.
