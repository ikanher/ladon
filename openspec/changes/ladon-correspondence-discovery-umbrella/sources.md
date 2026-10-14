# Source basis and planning observations

The user requested this umbrella after revealing a local critique of the Navier–Stokes exposition. This plan was informed by both the failed blind audit and the disclosed answers. It is not a new blind detection result. All planning inspection was local; no online criticism was searched.

## Original evidence locations

The following digests were read during planning on 2026-10-10. Paths are relative to the common projects directory, one level above the Ladon repository. External scratch paths are provenance locators, not portable runtime dependencies. Task 1.1 freezes the minimal required evidence under this change and records its original identity; do not modify or rebind the original Quux manifest.

| Original path | SHA-256 |
| --- | --- |
| `quux/temp/navier-stokes-blind-audit/backward-audit.md` | `f106e990f5a1cb67b6579dd60377e960d9952ed94f1dc7b887e1f2b6cc9f0641` |
| `quux/temp/navier-stokes-blind-audit/backward-observations.json` | `94723275645ea26f1d07f337296f7ccac88c13ad68d5a0f3f68957fdb22333d7` |
| `quux/temp/navier-stokes-blind-audit/backward.result.json` | `da8067933442530da3da4310fb7e67b7674d887d0b7081f05cb74ec5e14b4d0c` |
| `quux/temp/navier-stokes-blind-audit/backward-capture.json` | `e695e06120c9533f28757a3622adf90651b714ace931112d25b305164cfbe212` |
| `quux/temp/navier-stokes-blind-audit/post-reveal-observations.json` | `9c8c29c430bb54f0f5fd7658c58691a32af75bf1a7fe059a06a9eb8d198bdeeb` |
| `quux/temp/navier-stokes-blind-audit/navier-stokes.pdf` | `0e779481c4da40bd28d1e642e1d8ca57447d129610df28dfa5a11e9af8ae228f` |
| `quux/paper/navier-stokes-exposition-faults/NavierStokes_LostInTranslation_ArXiv.tex` | `67b27489185bf10baa92192a47ca25d51ecd4ed320b51374b5571a9cba13c084` |
| `quux/src/NavierStokesAndEuler/NavierStokes/SmoothFamilyTorusInverse.lean` | `165c097077dc3687fd1d6f93c356059e5254be17c799950873f54d91a71e90c8` |
| `quux/src/NavierStokesAndEuler/NavierStokes/R3/PressureFlux.lean` | `0adffc7879e8e5e226e5d4b2d721139a4ff12a04b4c9b4ebc12cf0d0f597fc2a` |
| `ladon/openspec/changes/ladon-proof-correspondence-audit-umbrella/evidence/r70/README.md` | `f1562de870c1c427885df9a3cb937a6cbeaf644220b7e73e8b42b388e951aa37` |
| `ladon/openspec/changes/ladon-proof-correspondence-audit-umbrella/evidence/r70/PUBLISHED_COMPARISON.md` | `368addd354745c6fcf3e6da62aa2de6f56b60dece07308e50704cc14e7e1436b` |

## Exact comparison targets

- Target repository commit: `f9e8bc5b38b6e212696e8a30e3e91517af887bbd`; Lean `leanprover/lean4:v4.34.0-rc2`.
- Original exposition: Lemma 8.6, equation (8.19), pages 95–96; Lemma 10.5, equation (10.19), pages 122–123.
- Inverse counterpart: `NavierStokes/SmoothFamilyTorusInverse.lean:1059`, `norm_derivativeWord_inverse_le`; producer `SmoothFourierData.coefficient_seminorm_bound` at line 368 in its owner.
- Pressure counterpart: `NavierStokes/R3/PressureFlux.lean:576`, `exists_uniform_actual_pressure_flux_bound`; the Riesz/Sobolev step appears at line 289, `riesz_rTest_bound`, and in `R3/RieszTestOperators.lean:223`, `lpNorm_six_rieszTest_le`.
- Critique: Bastounis, Circelli and Hansen, *Navier–Stokes lost in translation*. Local TeX labels `ex:Navier_strong` and `ex:Navier_weak`. The text expressly disclaims deciding whether the original informal proof is correct. This plan uses its concrete local comparisons and does not adopt its broader complexity claims as engineering conclusions.
- The Quux record includes actual endpoint checks and user-reported full-build evidence; those provenance classes remain separate. Neither establishes correspondence of the two estimates.

## Existing Ladon owners inspected

- [Known-case audit documentation](../../../docs/PROOF_CORRESPONDENCE_AUDIT.md).
- [Existing exposition views](../../../docs/RESULT_EXPOSITION.md).
- [Result manifest contract](../../../docs/RESULT_MANIFEST.md).
- [Mapping summary implementation](../../../src/ladon/result_manifest_summary.py).
- [Manifest integrity implementation](../../../src/ladon/result_manifest.py).
- [Assessment regression tests](../../../tests/test_result_assessments.py).
- [Completed r70 recipe](../ladon-proof-correspondence-audit-umbrella/evidence/r70/AUDIT_RECIPE.md).
- [Completed r70 findings](../ladon-proof-correspondence-audit-umbrella/evidence/r70/README.md).
- Existing specifications `proofir-observation-authority-and-coverage-core` and `proofir-attachment-and-link-observations`, read including their scenarios.

The r70 investigation already reproduces the derivative discrepancy with disclosed knowledge. Its completion is not evidence that Ladon discovers unknown discrepancies. Existing result commands explicitly preserve that distinction; the present umbrella adds an operational discovery workflow and a bounded evaluation, not a retroactive change to their authority.
