# Signal Correctness Benchmark Handoff

The signal-correctness child supplies two installed-CLI regression sources in
`tests/test_installed_cli_contract.py`. The benchmark child may materialize
equivalent static sources under `tests/fixtures/benchmark_harness/`; that child
owns the benchmark manifest, labels, resource measurements, and live-drift
policy.

## Text signal case

Source oracle:
`test_installed_text_signal_contract_preserves_raw_populations_and_authority`.

| Label | Class | Expected evidence | Rationale |
| --- | --- | --- | --- |
| `missing_internal.pkg_missing` | positive | Exactly one `Pkg.Missing` row with source location and `lexical_text` authority | `Pkg` is a discovered project namespace even though the importing owner is `Pkg.Owner0`. |
| `missing_internal.external_missing` | intentional negative | No internal-missing row for `External.Missing` | The external top namespace is not owned by the fixture. |
| `fan_in.mixed_importers` | boundary | `Pkg.CoreMixed` has generic 6, handwritten 1, and generated-importer 5 | Counts must match the population named by each raw table. |
| `fan_in.equivalent_tables` | boundary | Generic and handwritten raw rows for `Pkg.CoreShared` each remain visible at 5, with one promoted finding | Measurement is preserved while equivalent promotion is deduplicated by stable semantic key. |
| `declaration.supported_forms` | positive | Modified theorem/def plus `opaque`, `axiom`, and `constant` names, kinds, and offsets are present | These are the bounded forms promised by the text scanner. |
| `declaration.masked_examples` | intentional negative | `BlockFake`, `StringFake`, and `LineFake` are absent | Comment and string examples cannot alter the declaration inventory or facade classification. |
| `trust.lexical_axiom_sorry` | positive raw evidence | Non-comment axiom and `sorry` rows carry `lexical_text` authority and nonclaim wording | Text evidence is review input, not an elaborated theorem verdict or a new default finding. |

## Lean declaration signal case

Source oracle:
`test_installed_lean_signal_contract_caps_coarse_similarity_and_namespace_drift`.

| Label | Class | Expected evidence | Rationale |
| --- | --- | --- | --- |
| `namespace.parent_layout` | intentional negative | `Pkg.parentValue` in module `Pkg.Surface.Deep` produces no drift row | A conventional parent namespace is compatible with the module path. |
| `namespace.unrelated_layout` | positive | Two `Other.Space` declarations aggregate into one source-authority row | Unrelated declarations are source organization evidence, not one finding per declaration. |
| `similarity.coarse_only` | boundary | `ge_one` is retained at score 0.5, marked coarse-only, and not promoted | Equal unresolved classes without concrete identifier overlap cannot reach the high-confidence band. |
| `similarity.concrete_identifiers` | positive | `eq_zero` exposes normalized concrete overlap 1.0 and may be promoted | Concrete normalized identifiers are admissible high-confidence evidence. |

The required benchmark command must invoke the ordinary installed `ladon`
console and use its public options. It must not introduce alternate thresholds
or caller-specific analysis behavior.
