# First interpretation — frozen before Lean-owner search

Source: `latex/natural-language/finite_initialized_clipped_adam_rate.tex`, read directly as supplied in the exercise directory. Target claim: lemma “Actual update energy”, label `lem:energy`, including the definitions required by its statement and the appendix “Logarithmic update energy”.

## Mathematical reading

The process is the stated scaled initialized Adam process: dimension `d=100000`, `beta1=0.9`, `beta2=0.999`, fixed positive `epsilon=sqrt(d)*zeta=10^-11`, the corrected first and second moments formed from the same scaled releases `Y_t`, and direction `D_t = corrected_first/(sqrt(corrected_second)+epsilon)`. The releases arise under the stated global objective, record, sampling, and Gaussian-noise assumptions; importantly, the appended energy argument appears to use only the conditional second-moment bound on `Y_t` and the finite corrected-memory/logarithmic argument.

For every integer horizon `T >= 16384` and every constant step `gamma>0`, the average over all scaled coordinates and the first `T` updates of expected squared actual Adam directions satisfies

`J_T = (1/(T*d)) * sum_{t=1}^T sum_{i=1}^d E[D_{t,i}^2] <= 63*K^2/T + 1011*(26/T + 1/999) <= 2.9`,

where `K=73/10`. Expectations are over masks and Gaussian releases in the initialized run. The claim is a finite-horizon average bound, not a bound on each update or coordinate. Step size does not occur in the numerical upper bound; its quantifier is universal and its presence affects positions/release distributions through the process.

The appendix provides a per-coordinate pathwise bound with startup parameter `r>=1`, using raw second moment `v_t`, `S_t=v_t+epsilon^2`, a logarithmic telescoping inequality, corrected first-memory weights and direction cap `K`; it then bounds `E[v_T] <= 1.005`, applies a log tangent bound `E log(S_T/epsilon^2) < 26`, takes `r=64`, and averages coordinates. The positive stabilizer is essential to the stated log ratio.

## Assumptions and dependencies as read

- Earlier corrected-memory lemma supplies `|D_{t,i}| <= K` for all release histories and weights `p_{tj}`.
- Release second moment is bounded conditionally by `(G+b0)^2+V <= 1.004517 < 1.005`; the noise/mask assumptions define this `V`.
- `epsilon=10^-11` is fixed positive; `beta1=0.9`, `beta2=0.999`.
- Finite run starts with zero raw second memory, so `S_0=epsilon^2`.
- No independence across update releases is claimed/needed for the logarithmic energy telescoping step; conditional second moment bounds suffice for the final expected log estimate.

## Uncertain readings to retain

1. The natural-language theorem's phrase “every constant step” is interpreted as every fixed `gamma>0` over the run; no extra step-size restriction is stated.
2. `D_t` denotes the actual bias-corrected Adam direction with epsilon outside the square root, while the appendix's `Y_t` is scaled release and `v_t` its uncorrected EMA of squares. I will check whether the source crosswalk maps those exact objects.
3. The appendix's displayed per-coordinate inequality has no expectation on its left but a log term containing random `S_T`; likely it is intended pathwise. Its subsequent expected form is then taken. Whether a Lean owner encodes pathwise or expected energy is an open mapping question, not a change to this reading.
4. The `T<r` aside is not relevant after choosing `r=64` and requiring `T>=16384`.

This interpretation is frozen before inspecting Lean owners, source-crosswalk comments, or any audit/reference verdict. No repair or alternative claim is included.
