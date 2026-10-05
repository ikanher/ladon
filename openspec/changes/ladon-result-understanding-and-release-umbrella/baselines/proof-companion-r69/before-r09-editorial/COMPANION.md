# Why the general participation limit gives the fixed-epoch offset

This is a draft companion to the offset part of the fixed-epoch exposition's
“Sparse transcript calibration” theorem. It explains the specialization rather
than replacing the proof of the general participation limit. A reader asked why divergence needs to be proved; the explanation below has
been revised in response. The reader acknowledged the response and asked to continue; editorial adoption
and mathematical understanding have not been independently established.

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
estimate diverges. Why is that worth proving? The normalization is by the fixed
participation budget $E$, so the transcript-calibrated contribution is

$$
v_{E,T}=\frac{T\sigma_{E,T}^{2}}{E^{2}}.
$$

If the per-release noise were fixed, divergence would be immediate. But it is
recalibrated for each horizon and actually tends to zero. Growing $T$ alone
therefore does not settle the behavior of this product: a noise scale of order
$T^{-1/2}$ could keep it bounded. The substantive result establishes the calibrated decay
$\sigma_{E,T}\sim\Delta/\sqrt{2\log T}$ under the stated hypotheses. Consequently,
$v_{E,T}\sim\Delta^2T/(2E^2\log T)\to\infty$.

This gives a reason for the divergence statement's place in a full-batch
comparison: the full-batch privacy variance is a fixed finite value, so sufficiently
large transcript horizons eventually exceed it. The conclusion also distinguishes
public outputs. If only the final average is released and noise is calibrated
for that output, the exposition gives the uniform bound
$\overline v_{E,T}\le\Delta^2/(2\pi\delta^2)$. More releases do not by themselves
force that calibrated variance to diverge. These consequences are conventional
explanatory deductions and manuscript claims; this companion does not promote
their separate formal-coverage assessments.

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

The underlying fixed-participation theorem explains the constant. For expected
participation budget $\rho>0$, a standardized shift of the form
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
