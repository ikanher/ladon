# Bounded source reading before formal-owner inspection

User question: does the MF extension of Malladi-style sqrt(batch) Adam scaling to DP-Adam have mathematical support, particularly with newer SDE machinery?

Read the complete scalar natural-language note and local Malladi sqrt_scaling.tex before reading the Lean owner. The precise MF report passage is not yet identified; clarification is pending. The source note itself supplies crosswalk information, so this is informed source review, not blind discovery.

Scalar note claims: kappa>0; eta'=eta sqrt(kappa), s'=s/sqrt(kappa), Adam epsilon'=epsilon/sqrt(kappa), beta'=1-kappa(1-beta). Product/time-constant identities require stated nonzero assumptions; beta validity needs 0<=kappa(1-beta)<=1. DP profile B'=kappa B, q'=kappa q, T'=T/kappa, sigma'=sqrt(kappa) sigma preserves T q^2/sigma^2 and eta sigma C/B at fixed C. Physical q and step-count guards are separate. It explicitly excludes SDE approximation, exact accounting, convergence and transfer.

Stronger potential reading to investigate, not attributed to the scalar note: these transformations preserve the actual DP-Adam trajectory law or finite-test expectation up to a controlled error at comparable training time and privacy budget. Need original mechanism, sampling convention, adjacency, clipped signal and covariance, adaptive denominator, memory regime, time change, and conclusion transfer. Equal scalar proxies alone do not provide this.

Malladi local text uses simultaneous beta and epsilon changes and a weak-approximation bound, including a warm-start condition. New fixed-beta high-noise diffusion may describe a distinct asymptotic family; inspect exact owners before inferring compatibility.

Bounds: read-only donor; current Ladon source checkout; no shared builds/index updates; default 12 GiB RSS and finite CLI deadlines for checks. This is a bounded source/owner assessment, not whole-paper certification or a comparative pilot.
