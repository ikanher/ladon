# Evidence v2

Inputs: unchanged ../pld-core-r01/inputs/MANIFEST.json and its 15 frozen files. Historical raw Lean query: ../pld-core-r01/work/AuditCheck.lean and audit-check.log. New work is source reasoning; zero new Lean/extraction invocations. The historical query observed imported theorem signatures and three axiom lists; it did not establish compiled-source freshness, rebuild owners, prove a new source correspondence or replay a capsule. The reproduction path from the math checkout would be ../../ladon/openspec/changes/ladon-pld-core-source-audit/evidence/pld-core-r01/work/AuditCheck.lean; this is a corrected reproduction instruction, not a receipt for the historical invocation.

## Exact law orientation for P2/P4

Use paper probability densities pP and qQ on a common sigma-finite base μ, measurable, pointwise positive and normalized to integrate to one. Lean arguments are f=qQ and g=pP, not f=pP,g=qQ.

Frozen PLDRandomAllocation.lean:1642–1668 defines forwardLossValue f g=log(f/g), forwardLossLaw as its pushforward under densityMeasure μ f, reverseLossLaw as log(g/f) under densityMeasure μ g, and concretePLDPair as this pair. Hence for L=concretePLDPair μ qQ pP:

- L.forward is law(log(qQ/pP) under Q), the paper's law(Y).
- L.reverse is law(log(pP/qQ) under P), the law(−X). Thus law(X)=Measure.map Neg.neg L.reverse, using strict positivity for log inversion. It is NOT simply L.reverse.

This follows by the definitions and real log inversion under positivity. It is a mathematical object map, not a newly kernel-checked map-pushforward theorem. PLDPair itself stores two measures on R, without enforcing the paper's PRV normalization, size-bias identity or extended-real endpoints. General singular/discrete/support-at-infinity representation is unresolved.

Frozen Profile/ConcretePLDPair.lean:27–65 proves a profile identity for f,g. Setting f=qQ,g=pP makes the sampled loss Y, and the right integrand max(qQ−exp(ε)pP,0). The proof explicitly rewrites exp(−log(f/g))=g/f. PrivacyLossCore's event iff relates the positive-region gap bound to every measurable-event inequality for measurable integrable f,g. Probability densities provide integrability, but the broad source's singular/zero-density cases are not covered by the pointwise-positive bridge. No missing counterpart is inferred merely from a lexical search.

## P4: independent product specialization

Source prelims.tex:23–25 defines composition by independent X-side samples and independent Y-side samples; PRV.tex:73–82 factors those two product densities. Independence is therefore supplied in context.

Frozen PLDCompositionApproxDP.lean:901–936 identifies a concrete finite product-density pair with compFamily. With f_i=qQ_i,g_i=pP_i, common sigma-finite base μ, measurable strictly positive normalized coordinate densities and finite measure instances, its forward component is law(sum Y_i). Its reverse component is law(sum (−X_i)); applying negation produces law(sum X_i). Finite product measures encode independence within each side; no independence between X and Y on a joint space is required. The theorem permits finite nonnormalized measures too, so probability normalization is part of the source specialization, not a conclusion of the theorem.

The resulting paired-law realization is useful support. A full source composition claim additionally needs profile/curve preservation, source PRV size-bias/endpoints and representation independence. Those steps were not kernel-checked in this audit, and the arbitrary-law version remains unresolved. The original proof's displayed product/log calculation was read; no actual-use extraction or full proof-method certification was performed.

## P3.d: decisive smooth witness

See ../pld-core-r01/REVIEW-REVISION-r02.md and its separate prompted independent verification. Explicitly let p(t)=φ(t+1/2),q(t)=φ(t−1/2) be normalized N(−1/2,1), N(1/2,1) densities. Their ratio q/p=exp(t), so L(t)=t, paper X has density p, Y density q, and all source PRV identities hold with no endpoint mass. The source privacy curve is

δ(s)=∫_s^∞q(t)dt−exp(s)∫_s^∞p(t)dt.

The strictly positive smooth normal densities justify differentiating these tails. δ′(s)=−exp(s)∫_s^∞p(t)dt; δ″(s)−δ′(s)=exp(s)p(s)=q(s). PRV.tex:53 prints x(s)=exp(s)(δ″−δ′), which at s=1 gives exp(2)p(1) ≠ p(1). It is false even in a smooth normalized example. Repair P3.d-repaired: x(s)=exp(−s)(δ″−δ′), with adequate regularity. This is a distinct expression and no claim is made that this alone proves general reconstruction, endpoint recovery or uniqueness. The finding concerns an exposition formula, plausibly a sign typo; it does not refute a Lean theorem or the PRV composition method.

## Gaussian scope and restricted support S1

G1.a/G1.b ask for the extremal-event equality, halfspace, projection law and positive-radius CDF reduction, for arbitrary real ε. G2.a/G2.b ask for the radial identity, zero-radius convention and envelope. The historical query did not check those equalities. Their exact formal support remains unresolved; the scalar condition alone is not an equality of event supremums.

The separate S1 theorem gaussianPair_eventApproxDP_centered_of_analyticCondition_lt_one supplies, for all finite dimensions, means d and −d, σ>0, ε≥0, Δ≥0, ||d||²≤(Δ/2)², analyticGaussianCondition Δ σ ε δ and δ<1, the directed all-measurable-events bound. The source H(Δ), for Δ>0, uses the exact same analytic CDF arguments as GaussianPrivacyLoss.lean:78–87. Setting Δ=2√r for r>0 matches the source scalar profile. However S1 is only a sufficient bound, restricts ε and δ, and neither recovers the full original control nor treats the paper's only-positive-Δ H as defined at zero. The theorem uses ENNReal.ofReal δ; the equivalent ordinary real statement requires nonnegative δ, as is standard for privacy parameters. It is not a counterexample to the unrestricted source statement.

## Authority, effort and deviations

No new raw proof-search failure, memory measurement or cap-enforcement receipt was produced. Historical r01 declared 12 GiB but the available command does not establish enforcement or measured RSS. The 192-second checking entry is an estimate without raw timing receipts. Complete r01 evidence/effort manifest was created after review; only the first findings/inventory had earlier freeze records. Raw output of the initial incorrect theorem-name query is unavailable. These historical omissions remain deviations; current hashes cannot retroactively supply them. r03 freezes the complete revised package before its new reviewer sees the sources/obligations/raw log. Source and formal support, original method and coverage remain distinct throughout.
