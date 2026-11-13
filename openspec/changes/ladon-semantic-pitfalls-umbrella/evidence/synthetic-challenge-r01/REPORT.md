# N.2p — local conditional-descent capsule

The selected original proof was extracted and successfully replayed independently of the live matrix-factorization checkout. N.2p is complete. The synthetic challenge is still in preparation: no evaluation mutations, auditor inputs or comparison run have been created.

## Retained input and scope

The target is `Mf.Optimization.StochasticApproximation.almost_supermartingale_converges` under Lean 4.33.0. It supports the main conditional-descent claim in `historical_conditional_descent.tex`. The capsule includes five project modules: EnergyBalance, AlmostSupermartingale, StoppedDescent, AdditiveDescent and the selected prefix of MultiplicativeDescent.

The original note is retained as `original.tex`. The selected scope is lines 24–178, covering the conditional-descent principle, finite normalized account and supporting proof. The note's later initialized-root and coordinate claims are outside this capsule's qualification. Neither successful extraction nor replay certifies the prose/formal interpretation; that remains a source-review obligation.

The public replay was run on the directory materialization. The separately materialized archive has byte-identical payload files and plan; its manifest differs in `outputKind` and the resulting capsule identity. Both inventories were validated. The archive was not separately replayed; the reproducibility command below would create that additional receipt.

`original-capsule.tar.gz` is the recoverable local input. Its SHA-256 and the target identity are in [EXTRACTION.json](EXTRACTION.json). The working materialization is under `temp/pitfalls-synthetic-r01/original-capsule/` in Ladon. The retained archive can reconstruct it without reading the donor's project sources. `plan.json`, the materialization receipts and the archive preserve the original formal target and its checking inputs.

## Native dependency evidence

The plan contains a complete repository-scoped semantic graph with 27 declarations and 3,313 recorded dependency edges. It retains 3,277 external declaration frontiers. The separate build graph records project imports and locked external dependencies. This is native Lean-environment evidence, rather than a lexical dependency estimate.

No additional lineage extraction is needed to duplicate this selected declaration closure. Scoped local-premise observations may still be needed by N.2b; the declaration graph alone does not establish which local premise supplies a proof step or whether the exposition justifies it.

The replay matched the recorded trust frontier at the capsule's external boundary. The recorded axiom-reference row names `propext`; this is not a claim that the entire transitive external library depends on that axiom alone. External declarations retain explicit frontiers rather than acquiring a new independent audit.

## Replay results

| Attempt | Result | Meaning |
| --- | --- | --- |
| Network denied | `dependency-unavailable` | Content/isolation checks passed, but the fresh repository lacked vendored external packages. Retained as `replay-network-deny.json`. |
| Locked dependency acquisition enabled | `verified` | Dependencies were acquired in a fresh temporary repository, project modules rebuilt, and native theorem evidence matched. Retained as `replay-network-allow.json`. |

The successful replay matched exact name, declaration kind, Lean version, type fingerprint, proof-value fingerprint, repository semantic closure and recorded trust frontier. Isolation checks report no donor checkout referenced by commands or environment. The replay repository was temporary and cleaned up by Ladon; no donor build products were used as project outputs.

Dependencies were acquired from the locked Git URLs/revisions. Mathlib's dependency setup decompressed 8,689 already-cached files from its cache; this is disclosed reuse of external compiled artifacts, not a source rebuild of Mathlib. The capsule is locked and rebuildable with external package/cache access; it is not an offline-vendored or system-hermetic package. Its source graph and exact external pins are retained in `plan.json` and the capsule lock file.

Both attempts used a 3,600-second deadline per stage, a 12 GiB process-tree RSS limit and the existing 16 MiB process-output ceiling. Successful dependency resolution, project build and final query peaked at approximately 1.83, 6.05 and 5.75 GiB sampled process-tree RSS respectively. No memory, timeout or output limit was reached. Total preparation and phase durations were not independently instrumented; tokens are unavailable.

The target prefix produced a missing-namespace-end style warning. Compilation succeeded and the exact target/semantic comparisons matched. The original theorem/proof was not edited to suppress that warning.

## Reproduction

Use Ladon from this checkout. From the Ladon root:

```bash
PYTHONPATH="$PWD/src" .venv/bin/python -m ladon.entrypoint theorem replay \
  openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/synthetic-challenge-r01/original-capsule.tar.gz \
  --timeout 3600 --max-rss-mib 12288 --network allow \
  --format json --output /tmp/conditional-descent-replay.json
```

The pinned toolchain and locked external Git repositories/cache must be available. Run inputs and receipts have hashes in `SHA256SUMS`; from this evidence directory use `sha256sum -c SHA256SUMS`. Artifact hash verification is separate from rerunning Lean. `VERIFICATION.json` records the root checks and donor-source comparison.

## Next work

N.2b qualifies a useful source-audit workflow on this local proof and separate development material. It must preserve the difference between original-proof observation, independently checked terms and source interpretation, and freeze before evaluation answers are disclosed. N.2m owns independent validation of the later synthetic cases; N.2c owns registration. Successful replay alone establishes neither exposition-fault detection nor comparative benefit.
