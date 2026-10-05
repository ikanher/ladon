# Why the general participation limit gives the fixed-epoch offset

This companion explains the offset part of the fixed-epoch exposition's
“Sparse transcript calibration” theorem, and why shrinking noise per release
can coexist with diverging variance of the final estimate. It specializes an
existing general limit rather than replacing that limit's analytical proof.

Fix a positive integer epoch budget $E$. With $T\ge E$ releases, sampling each
contribution independently at rate $q=E/T$ keeps its expected total participation
equal to $E$. Increasing $T$ therefore makes selection rarer at each release,
while preserving the expected participation budget. We calibrate independent
Gaussian noise for the **entire transcript of individual releases**. Write
$\sigma_{E,T}$ for the calibrated raw, per-release standard deviation, with
sensitivity $\Delta>0$, fixed $\varepsilon\ge0$, and target
$0<\delta<1-e^{-E}$. It is the infimum of nonnegative standard deviations whose
two-sided transcript privacy profile is at most $\delta$.

The surrounding theorem also states that the privacy variance of the normalized
estimate diverges. Why is that worth proving? This estimator divides the sum of
releases by $E$, not by $T$: $Tq=E$ makes it an unbiased estimate of the full
query sum. Its transcript-calibrated Gaussian variance is

$$
v_{E,T}=\frac{T\sigma_{E,T}^{2}}{E^{2}}.
$$

If the per-release noise were fixed, divergence would be immediate. But it is
recalibrated for each horizon and tends to zero. Growing $T$ alone therefore
does not settle the product: the hypothetical noise choice $\sigma_T=c/\sqrt T$
would give $T\sigma_T^2/E^2=c^2/E^2$. This is an algebraic example, not a
feasible transcript calibration under the stated privacy conditions.

The theorem proves substantially more than divergence. Writing
$b_T=\sqrt{2\log T}$, its finite offset limit gives
$\Delta/\sigma_{E,T}=b_T+s_{E,\delta}+o(1)$. Dividing by $b_T\to\infty$
and taking reciprocals gives $\sigma_{E,T}\sim\Delta/\sqrt{2\log T}$.
Therefore $v_{E,T}\sim\Delta^2T/(2E^2\log T)\to\infty$. The divergence is
an elementary consequence once the calibrated scale is known; the offset
additionally identifies the finite correction to the standardized shift.

Divergence alone also has a shorter argument. If the normalized variance were
bounded by a fixed $M>0$, the raw noise would be at most $E\sqrt{M/T}$.
In the canonical transcript, the event that some release exceeds $\Delta/2$
would then have vanishing probability without the differing record, but
probability tending to $1-e^{-E}$ when the record can be sampled. The latter
is the limiting probability of at least one selection. Gaussian tail bounds
make the noise errors vanish even across all $T$ coordinates. Since
$\delta<1-e^{-E}$ and $\varepsilon$ is fixed, for every $M>0$ all variances
at most $M$ are infeasible once $T$ is sufficiently large. This proves divergence,
but not its sharp rate or the offset constant.

This explains the divergence statement's place in a full-batch comparison.
The full-batch variance $v_{\mathrm{FB}}$ is fixed and finite, so the transcript
privacy variance alone eventually exceeds it. The sampling contribution
$(1-E/T)S/E$ is nonnegative. Thus one sufficiently large horizon cutoff works
for every $S\ge0$. This is not a claim of full-batch optimality at every
non-full horizon.

Public outputs must remain distinct. If only the final average is disclosed
and noise is calibrated for that output, the exposition gives
$\overline v_{E,T}\le\Delta^2/(2\pi\delta^2)$ uniformly in $T$. This is a
feasibility bound, not a limit formula or a comparison with full batch. It
provides no guarantee for additionally disclosed individual releases. The
variance and divergence arguments here are conventional mathematical reasoning;
they do not update separate formal-coverage assessments.

The result describes the offset after subtracting the Gaussian critical scale:

$$
\frac{\Delta}{\sigma_{E,T}}-\sqrt{2\log T}
\longrightarrow
s_{E,\delta}:=\Phi^{-1}\!\left(-\frac{\log(1-\delta)}E\right),
\qquad T\to\infty\text{ through integers }T\ge E.
$$

Here $\Phi$ is the standard normal distribution function. The strict condition
on $\delta$ puts $-\log(1-\delta)/E$ in $(0,1)$, so the displayed quantile is
finite. All parameters are fixed in this limit. In particular, the theorem does
not allow $E$, $\varepsilon$, or $\delta$ to vary with $T$.

The underlying fixed-participation theorem explains the constant. For a schedule with
$Tq_T\to\rho>0$, a standardized shift of the form
$\Delta/\sigma_T=\sqrt{2\log T}+s+o(1)$ has limiting transcript privacy profile

$$
L_\rho(s)=1-e^{-\rho\Phi(s)}.
$$

This function is continuous and strictly increasing, with range
$(0,1-e^{-\rho})$. Setting $L_\rho(s)=\delta$ gives the quantile above.
To pass from profile convergence to calibration, bracket this solution by
$s-\eta$ and $s+\eta$. The former gives more noise and is eventually feasible;
the latter gives less noise and is eventually infeasible. Monotonicity and the
finite calibration properties trap the calibrated offset between these values.
Letting $\eta$ decrease to zero yields its limit. This uses the general theorem's
analytical proof; the specialization below does not reprove that analysis.
The constant is independent of fixed $\varepsilon$, even though finite-horizon
calibration depends on it. This is a conclusion of that profile-limit theorem,
not permission to vary $\varepsilon$ along the sequence.

To obtain the fixed-epoch statement, take $\rho=E$ and use the capped schedule
$q_T=\min(1,E/T)$ for positive horizons. For every admissible horizon $T\ge E$,
this is **exactly** $E/T$. More is needed than an asymptotic agreement of rates:
the general and fixed-epoch calibrated noises must denote the same quantity.
Unfolding their definitions shows the same transcript calibration expression,
at the same horizon and rate, with the same $\Delta$, $\varepsilon$, and $\delta$.
Thus their calibrated standard deviations agree on this tail. No new
calibration-equality hypothesis is assumed.

Finally put $T=E+k$, $k\in\mathbb N$. The general limit composed with this shift,
and rewritten using the calibration identity, is precisely the displayed
fixed-epoch limit. This indexing covers every admissible integer horizon, rather
than selecting a sparse subsequence. The Lean adapter performs those same steps:
instantiate the capped schedule, compose the general limit, and rewrite the
calibration and critical-scale definitions.

This is an offset result for transcript calibration. It is not an average-only
release theorem, a finite-horizon inequality, or a full-batch optimality theorem.
The surrounding exposition also derives leading-order and variance conclusions;
the separate checked adapter and its assessment support the offset component.
They do not by themselves promote formal coverage of those other components.

The mathematical source is the exposition's sparse-limit appendix, especially
its fixed-participation calibration theorem and the proof of `thm:smallbatch`.
Its bibliography cites Balle and Wang (2018) for analytical Gaussian calibration,
and Räisä, Jälkö and Honkela (2024) for a related fixed-rate comparison. A fixed
rate $q>0$ is a different limit from $q=E/T$; that comparison cannot be substituted
here without additional uniformity. These are the manuscript's attributions,
not an independent exhaustive priority assessment.

[Exact source/support and ordinary checking route](SOURCE_SUPPORT.md) accompany
this draft. A reader can question any step above directly; no model account or
Ladon command is required to read it or propose a correction.

## Status of this explanation

This revision incorporates the r09 reviewer’s editorial proposal and responds
to the recorded divergence question. The shorter divergence argument above is
conventional reasoning supplied by that reviewer, not a new Lean-checked result
or a claim of novelty.
The user's earlier acknowledgment authorized continuation; it does not establish
understanding of the full argument or adoption of this new text. The historical
compilation and assessment concern their named sources and manuscript version,
not this Markdown companion. No new Lean run or formal binding accompanies the
additional conventional divergence argument.
