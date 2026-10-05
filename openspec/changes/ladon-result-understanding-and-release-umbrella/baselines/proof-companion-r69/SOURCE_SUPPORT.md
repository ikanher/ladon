# Draft scope and exact supporting sources

For this companion’s offline supporting-source copies, start with the
[archive-local supporting sources](SOURCE_SUPPORT_PACKET.md). The absolute
workspace links below identify the originating files; they are not portable
archive links. The build commands require the external full mathematical project,
including the audit module and imports omitted from this archive.

The user selected the fixed-epoch material after r08. This companion focuses on
its offset specialization; it is a new model-authored explanation, not an
adopted manuscript revision or a human review. The user supplied a divergence question; the response and proposed revision
are preserved in READER_QUESTION_AND_RESPONSE.md. The reader acknowledged the response and authorized continuation; editorial adoption remains pending. The original passage is retained in ORIGINAL_PASSAGE.tex.

The mathematical project is read-only during this preparation. No build was
rerun, no canonical capture or review was renewed, and no existing assessment
was made current against this new Markdown document. The historical proposed
assessment concerns its own manuscript revision, not this companion.

The following identities were read during draft preparation:

| Source | SHA-256 |
| --- | --- |
| [Exposition](/home/codex/projects/lean/matrix-factorization/latex/natural-language/poisson_fixed_epoch_large_batch_optimality_exposition.tex) | `sha256:d3b6b9dceb8dc3465120abbc6c89133ad5f754eb13c4918d3a10e8cc9d28f583` |
| [Adapter](/home/codex/projects/lean/matrix-factorization/Mf/DP/PoissonFixedEpochOffset.lean) | `sha256:859e9694147bd05203feca6241ad9ce388f2016f24e4576285c3279a30ca2993` |
| [Historical compilation receipt](/home/codex/projects/lean/matrix-factorization/latex/lean/poisson_fixed_epoch_offset_handoff_r64/compilation-final.json) | `sha256:d0d7578b682586c8bce071bd0b168e3d0f2b6657525f4819fec65dd0fd83c363` |
| [Proposed offset assessment](/home/codex/projects/lean/matrix-factorization/latex/lean/poisson_fixed_epoch_offset_handoff_r64/assessment-offset-proposed.json) | `sha256:557844e0de8961e365b853acc3da3c071495b9427db8872f72009a1058ab35c2` |

The adapter's current source digest matches the historical compilation receipt.
That receipt records the normal pinned build and ordinary compiler/axiom recipe,
with `propext`, `Classical.choice`, and `Quot.sound`. Matching bytes do not renew
checking of current imported dependencies. See the mathematical project's
[correspondence note](/home/codex/projects/lean/matrix-factorization/docs/POISSON-FIXED-EPOCH-OFFSET-CORRESPONDENCE.md) for the full historical scope and proposed adoption.

For a fresh check, work from the real matrix-factorization repository root with
its pinned toolchain and dependencies:

```bash
lake build Mf.DP.PoissonFixedEpochOffset Mf.DP.PoissonFixedEpochOffsetAudit
lake env lean Mf/DP/PoissonFixedEpochOffsetAudit.lean
```

Compare the printed declaration and its definitions with the offset statement,
and inspect transitive axioms. Ordinary Lean suffices; these instructions do not
promise the current build will pass. Verification needs the project and its
imports, not merely this companion. No private model access is required.

The recorded reader follow-up is acknowledgment and authorization to continue. Preserve any further feedback,
the author's response, any fresh obligation check, and the proposed/adopted or
unresolved revision. Do not substitute a generated question for the reader round.
Adding premises would narrow a statement; no coverage of leading/variance/average
components is promoted by this draft. Mathematical explanation quality and
Ladon software value remain separate questions.
