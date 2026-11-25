# Overlapping Lake source roots abort lexical index creation

## Reproduce

From the Ladon repository root, run:

```bash
python openspec/changes/ladon-overlapping-lake-source-roots/evidence/reproduce.py
```

The fixture contains two Lean files and a Lakefile. `Challenges/Preserved/HodgeHelpers/Shared.lean` is discovered as both `HodgeHelpers.Shared` and `Challenges.Preserved.HodgeHelpers.Shared`. `Challenges/Ordinary.lean` supplies an unaffected module. The reproducer calls the installed `ladon` by default and accepts `--ladon PATH` to select another executable. It uses a disposable index directory and needs no Lean build or package fetch. The fixture exercises Ladon's static discovery and storage. It does not reproduce the OAI custom Lake facet.

## Observed and expected behavior

On Ladon 0.5.1, the reproducer exits 2 with diagnostic code `invalid-invocation` and message `SQLite index build failed: UNIQUE constraint failed: modules.path`. No index is published. The [captured output](evidence/repro-output.txt) and [installed version receipt](evidence/ladon-version.json) record this execution.

Where canonical ownership is established, the expected result is a searchable index with the confirmed helper module name and the unaffected module. If ownership cannot be established from the available layout, the expected result is a diagnostic naming the path and both candidates and explaining how to resolve them. See the [spec delta](specs/ladon-index-source-layout/spec.md) for the build and update contract.

## Field case

The same error occurred on `matrix-factorization/src/math/lean`, OAI revision `3344da599`, while running `ladon proof-search index build` against its project root. See the [production terminal record](evidence/oai-build-progress.jsonl). The discovery collision was confirmed on the following file:

```text
ComparatorChallenges/HodgeConjectureCMAbelianVarieties/HodgeConjecture/Variants.lean
```

Ladon derived the two names `HodgeConjecture.Variants` and `ComparatorChallenges.HodgeConjectureCMAbelianVarieties.HodgeConjecture.Variants`. The Lakefile declares a nested `HodgeConjecture` library and defines `comparatorSourceModules` to filter the broader aliases before restoring the original helper module names. Ladon's static discovery reads both library roots and does not evaluate that filter. Both mappings reach the index with the same resolved path. The duplicate module path error is separate from the index size limit.

A local source view covering `OAI.Analysis`, `OAI.MeasureTheory`, `OAI.Probability`, `OAI.Optimization`, and `OAI.InformationTheory` avoided the overlapping challenge roots. Its independent index was verified fresh and supported exact declaration lookup. That workaround covers 47,207 modules and does not establish coverage of the full OAI checkout.
