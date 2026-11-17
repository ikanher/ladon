# f-DP subsampling source interpretation

## Disposition

The selected source leaves the map from a uniformly selected subset of records to the ordered tuple supplied to the mechanism unspecified. Therefore the manuscript does not establish which tuple-order policy is intended in the inspected passage. The Lean-checked countermodel refutes the classical amplification claim under the explicit inherited/increasing-order interpretation. It does not, by itself, establish an unconditional error in the manuscript.

## Source inspected

Read-only donor: `/home/codex/projects/lean/matrix-factorization`.

| File and lines | Source statement | Relevance |
| --- | --- | --- |
| `paper/theory/mu-dp/fDP/fDP.tex:32` | Defines a dataset as a collection, formally written `S=(x_1,...,x_n)`, and defines neighbors by changing exactly one coordinate. | The formal representation and adjacency are ordered-tuple based. |
| `paper/theory/mu-dp/fDP/fDP.tex:34` | A commented editorial note says “Removed ‘by appropriate permuting’” and explains that permutation invariance is not explicitly assumed or required. | It is not an active definition. It shows that permutation handling was considered, but does not specify the replacement rule. |
| `paper/theory/mu-dp/subsample.tex:37` | Selects uniformly an m-sized subset of the dataset; M is defined on `X^m`; the intermediate sample is hidden. | Specifies the subset law and output secrecy, but not an ordering map from the selected set to `X^m`. |
| `paper/theory/mu-dp/appendices/property.tex:228-230` | Assumes neighbors differ in the first individual, defines `x_I` as the m individuals indexed by I, and identifies `M(x_I)` with the subsampled mechanism. | Does not state whether indices are inherited in increasing order, uniformly permuted, or treated through some other canonical encoding. |
| `paper/theory/mu-dp/appendices/property.tex:286-299` | Replaces selected index 1 by an index outside I and asserts the corresponding selected inputs are neighboring. | This requires a tuple representation under which the replacement preserves all but one coordinate. Subset counting alone does not state that representation. |

SHA-256 of the inspected donor files at this review:

- `fDP/fDP.tex`: `b587a49ef48e282c1cc228b5fbc5955cf136519c8734b2ae1c2bf7a843657eb7`
- `subsample.tex`: `11223a25e22c97b4c57dd08fd231d53da8c1664430c40cecb97a8e0c6eb561bb`
- `appendices/property.tex`: `38885bdbeee87a8e6a8725cc622e13d9e926225b66070022cbd75ec077857c88`

## Mathematical consequence

For inherited increasing-index order, the checked finite example in [the countermodel report](../fdp-ordering-privacy-20261115T072023Z/REPORT.md) satisfies the stated coordinate replace-one privacy assumption for every finite input pair and binary output event, yet violates the claimed hidden-subsample factor-5/3 event bound by exactly 1/54. A uniformly shuffled-order control passes for the same input pair only. The control does not prove the general shuffled theorem.

The appendix's replacement argument is valid for an in-place ordered replacement map, but the source does not expressly attach that map to its uniform-subset definition. Consequently the strongest supported disposition is conditional refutation under inherited order plus an unresolved source-to-tuple map. Establishing a repaired or alternative theorem would require a separately specified sampler/assumption and its own proof.

## Limits

This is an informed source interpretation by the current auditor, not an independent review or a newly discovered Ladon result. It does not infer author intent from the commented edit note, establish a permutation-invariant mechanism, or prove a general shuffled-order amplification theorem. The matrix-factorization checkout was read only. The countermodel, checking authority and execution limits are documented in its linked report and manifest.
