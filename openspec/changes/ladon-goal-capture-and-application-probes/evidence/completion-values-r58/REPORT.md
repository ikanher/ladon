# Used local values: completion feasibility supplement r58

The bounded continuation demonstrates one imported-context route that preserves used local definition values and their dependencies. It is supporting evidence for tasks1.3/2.3, not qualified production completion. Historical [initial r58](../application-completion-r58/REPORT.md) remains unchanged.

In the positive control the submitted term is the actual local `z`, where `have z : x=x := h`. Lean marks this definition nondependent. Generalizing it into a fresh premise drops its value. With `generalizeNondepLet := false`, typechecking actual used values and tracing their type/value dependencies, the closed term preserves `z := h` and an independent ordinary compiler reports no axioms.

In the admitted-value control `z := sorry`, generalization produces a successful replay without `sorryAx`; this is an unsafe trust route. Preserving the value plus controlled `pp.all` printing and empty-context roundtrip retains the dependency; independent compilation reports `[sorryAx]`. Ordinary printing abbreviates the value with `⋯` and fails roundtrip; that failed attempt is retained. A used value referring to internal `_example` is rejected by the transitive local dependency guard.

All17 manifest-listed source/helper/receipt files were independently hash/length checked by root before copying here. [Manifest](used-local-value-feasibility-manifest.json) retains original absolute paths, exact hashes and recorded results. Baseline HEAD d64f475e23a7339c91aa280ff6e6679c27607875. The worker's observation is recorded on the canonical board in posts778/780; root checked the compiler receipts and all listed bytes.

Cumulative feasibility charge is62.76706126118353/120 supervised Lean seconds, leaving57.23293873881647. Each continuation process was bounded to30seconds,32GiB process-tree RSS and8MiB output. The faithful admitted-value check used3,733,094,400 RSS bytes; its normal compiler replay used1,583,923,200 bytes. These are observed peaks, not allocation requirements. No production sources or neighbor project builds were changed.

Remaining acceptance: the ordinary completion API/CLI, closed versioned helper framing, exact captured source/context/environment revalidation, independent replay/trust policy, real residual and negative controls, installed qualification and the eventual exposition handoff. These results establish neither theorem discovery nor reader usefulness.
