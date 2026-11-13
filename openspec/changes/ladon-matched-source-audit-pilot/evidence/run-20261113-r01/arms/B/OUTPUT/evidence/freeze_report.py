from pathlib import Path
import datetime,json,hashlib,os
out=Path(__file__).parent.parent
ack=json.loads((out/'ROLE-ACK.json').read_text())
end=datetime.datetime.now(datetime.timezone.utc)
start=datetime.datetime.fromisoformat(ack['start_time_utc'])
rows=[json.loads(s) for s in (out/'evidence/commands.jsonl').read_text().splitlines()]
count=sum(r.get('lean_lake_invocations',0) for r in rows)
summary={'arm':'B','start_time_utc':ack['start_time_utc'],'end_time_utc':end.isoformat(),'elapsed_seconds_since_ack':(end-start).total_seconds(),'lean_lake_invocations':count,'lean_lake_limit':30,'wall_time_limit_minutes':90,'wall_time_ceiling_reached':False,'invocation_ceiling_reached':False,'token_telemetry':'unavailable','source_modifications':False,'ladon_invoked':False,'network_used':False,'other_arm_or_registration_files_inspected':False}
(out/'RUN-SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
report=r"""# First report — arm B

This is a fresh source-first audit of the two supplied TeX notes and their supplied Lean capsule. I found faithful, checked support for the Poisson finite-bracket theorem and its infimum calibration consequence, and for the fixed-cardinality hidden-schedule training mechanism definition. I did not substantiate a false mathematical claim. I abstain from certifying the training note's complete accountant, signed adaptive reduction, and global threshold theorems: their cited proof owners are absent from this capsule. Absence here is a coverage limitation, not a counterexample or a claim that those results are absent from the parent project.

This report is frozen on first save. No whole-note certification is claimed.

## Procedure and inventory

The role acknowledgment was written before source inspection. Only the assigned PROMPT, INPUT, installed tooling, and this arm's OUTPUT were accessed. No Ladon, network, project history, sibling arm, registration directory, prior review, or external diagnosis was used. The supplied capsule README/readiness metadata were inspected for environment context; their prior replay claims were not treated as independent audit evidence.

Both complete notes were read, including the appendices and crosswalks. The notes are:

| Source alias | Relative path below INPUT/capsule/sources/latex/natural-language | Lines | SHA-256 |
| --- | --- | ---: | --- |
| D | deterministic_koutoft_training_accountant_proof.tex | 502 | c3481d0da86418b2c880b79b66abdbc4bf684e7a1b3edcdf03fc3014ba514602 |
| P | poisson_fixed_participation_finite_bracket_proof.tex | 720 | 7c82e6719baf1857b6e71691b8257292c42c20b914f5d3f70fe9fc49412a364b |

The input contains 63 local Lean source files. Their paths, line counts, and hashes are in `evidence/source-inventory.json`. The capsule is a restricted transitive import closure, not all proof owners mentioned by the notes. Raw inventories and numbered TeX are in `inventory.txt`, `notes.txt`, `poisson_first.txt`, `poisson_rest.txt`, and `deterministic_tail.txt`. The initial combined display was truncated by the interface; subsequent separate reads covered the omitted text, and the full combined output was preserved on disk.

The claim inventory below covers every mathematical section, major displayed definition/formula, named lemma/theorem, parameter restriction, and proof dependency. Grouped spans are not an assertion that every sentence received an independent formal proof.

## Source coverage and claim inventory

Legend: M = examined and mapped to supplied definitions/theorems; E = examined mathematically; U = examined but formal support or a remaining proof obligation is unresolved. No TeX span was left unread. Preamble/layout and bibliography were read but are not mathematical verification targets.

| Span | Claims, formulas, assumptions, or dependency | Status |
| --- | --- | --- |
| D:35–49 | Three outputs; finite add/remove calibration versus noncomputable exact global thresholds; schedules remain randomized | E/U for full endpoints |
| D:53–86 | Finite datasets with decidable equality; T>0, 0≤k≤T, dimension d; measurable history-dependent queries; independent per-user uniform k-subsets; clipping; Gaussian releases; zero history; add/remove and direct replacement adjacency; hockey-stick tests | M for mechanism and adjacency; E for test/event equivalence |
| D:88–126 | Rational request, ε≥0, δ>0; terminating positive rational grid-relative calibration; global positive attained AR/RO thresholds additionally require k>0 and δ<1, uniformly over record type/d/oracle | E/U; full endpoints unavailable |
| D:128–138 | Common schedule-blind decoder, lower projections, signed replacement, degradation/continuity/attainment route | E/U |
| D:142–161 | Data processing and common-weight mixture inequality for hockey-stick divergence | E; conventional test pullback argument is valid |
| D:163–189 | Bounded-vector adaptive Gaussian channel; padded unit vector, measurable Householder map, recursion | E; covariance/mean argument checked, measurable recursive owner unavailable |
| D:191–224 | Exact k-subset Gaussian mixture versus centered Gaussian; condition on common schedules and use one decoder before averaging | E/U; no substitution by Bernoulli sampling or average fixed-S divergence |
| D:226–251 | Conservative μ=k/σ; rational checker; fallback σ=(k+1)/δ; GDP≤μ/2; finite fold leastness | E/U; fallback algebra checked, checker and its soundness owner unavailable |
| D:253–284 | Signed family norm bound, common sign of c_h a_h, interpolation quadratic form; positive future factors and backward adaptive comparison | E/U; see abstention A2 |
| D:286–323 | Constant +1 and +1/−1 lower realizations by projection; nonincreasing continuous exact profiles; feasible fallback; small-noise separation; truncated closed feasible set and attained infimum | E/U; order/topology argument examined; exact formal profiles and realizations unavailable |
| D:327–377 | Assembly of main clauses; independent replacement schedules; normalized amplitudes ±1/σ; two signed directions; common decoder | E/U; main theorem cannot be replayed from capsule |
| D:379–407 | k=0 or δ≥1 gives all positive scales, infimum 0 and no least positive member; δ=0 excluded; ideal-real implementation scope; prior replay/axiom provenance | E; provenance not independently confirmed for absent endpoints |
| D:409–502 | Declaration/file crosswalk and audit modules | M for 3 cited declarations; U for 35 other cited declaration references |
| P:41–132 | Finite supplied-threshold bracket, box/complement split; no optimizer authority; cited related work | E; external literature claims not verified |
| P:133–191 | T∈N, q∈[0,1], Δ and ε arbitrary real, σ>0; independent source/reference product laws; event profiles; zero-noise law definition; direct x/σ standardization | M |
| P:192–223 | p_P=((1−q)Φ(a)+qΦ(a−μ))^T; p_Q=Φ(a)^T; m₂ with exp(μ²)Φ(a−2μ); centered moment v; residual R; capped U_F; reverse dual/floor/min; positive-part L | M; formulas compared term by term |
| P:224–259 | L≤two-sided profile≤max(U_F,U_R), three independently supplied thresholds; no optimality; includes T=0 and q endpoints | M |
| P:260–339 | ℓ=1−q+q exp(μz−μ²/2); product Λ; positivity/integrability/mean one; box and complement; four exact moments; Gaussian tilt; square expansion and nonnegativity | M |
| P:343–362 | Exact event probabilities 1−p_P,1−p_Q and lower witness from event supremum | M |
| P:364–405 | Forward profile positive-part integral; outside source mass; finite-measure Cauchy–Schwarz retaining p_Q; minimum with p_P | M; method corresponds |
| P:407–459 | Real signed coefficient duality at −ε, then positive embedding; Λ≥(1−q)^T; minimum of reverse bounds; maximum of directions | M; method corresponds |
| P:461–470 | T=0 and q=0/1 edge cases, only division by σ | E/M for theorem parameter domain |
| P:472–542 | σ≥0 feasible set, infimum; strict lower and non-strict upper certificates; upper certificate supplies nonemptiness; Gaussian residual gives upward closure; no attainment assumption | M |
| P:544–590 | Numerical row, thresholds, relative width and PLD diagnostic; ideal independent Poisson product scope and no tightness/optimizer/runtime claim | E; arithmetic diagnostic reproduced, PLD and formal rational certificate not replayed |
| P:592–644 | Bibliography and notation | E; citations themselves not externally checked |
| P:646–669 | Outward rational enclosures, squared rational root bounds, finite certificate comparisons; external optimizer has no proof authority | E/U for actual executable replay certificate |
| P:671–720 | Formal crosswalk | M for 12 cited declarations; U for 1 replay declaration |

## Findings and faithful controls

### F1. The training mechanism retains exactly one independent fixed-cardinality schedule per user

**Source:** D:54–71, D:207–224. **Formal:** `Mf.DP.Training.KOutOfT.fixedCardinalityScheduleMass`, `fixedCardinalityScheduleMass_sum_eq_one`, `fixedCardinalityScheduleMass_eq_zero_of_card_ne`, `UserScheduleAssignment`, `userScheduleAssignmentMass`, `userScheduleAssignmentMass_sum_eq_one`, `transcriptGivenScheduleAssignment`, and `kOutOfTTrainingTranscript`, in `Mf/DP/Training/KOutOfT/TrainingMechanism.lean:13–130`.

The underlying `bisFixedCardUniformMass` is 1/choose(T,k) on the k-subsets and zero elsewhere (`OptimalSubsamplingBISLR.lean:1541–1543`). The normalization theorem retains k≤T. The user assignment weight is a product over users. The recursive bind chain receives one unchanged assignment argument, and the sum over assignments is outside the entire T-step conditional transcript. This matches the note's hidden fixed-cardinality construction and independence across users. A check at T=2,k=1 proves singleton schedule mass 1/2 and empty/full schedule mass zero; thus this is not the independent-coordinate q=k/T experiment.

The formal mechanism has extra clipping and initial-history parameters. Its correspondence to D uses clippingNorm=1 and zero initial history. `AdaptiveTrainingOracle.measurable_history` supplies the source measurability assumption; `UserDataset` is a finite set; `UserReplaceOneAdj` requires distinct absent replacement records. The raw history type is N→R^d, with one coordinate overwritten at each step; at zero initial history, unwritten coordinates are public zero. This explains the different transcript representation without identifying it with a raw finite vector.

**Consequence:** the provided definition faithfully models the source mechanism's schedule semantics. It does not itself establish a privacy theorem or the claimed projected lower realization. **Confidence:** high for this definition-level correspondence.

### F2. Euclidean clipping and standard-deviation units match the sources

**Source:** D:65–69; P:135–191. **Formal:** `l2Norm`, `l2VectorClip`, `l2VectorClip_norm_le` in `EuclideanVectorClipping.lean:19–109`; `bsrGaussianMeasure` in `BSRGaussianCore.lean:292`; `FiniteGaussian.measure` in `FiniteGaussianDensity.lean:425–433`; `FiniteProductGaussian.variance/law`; `sampledGaussianProductProfileStddev` in `SampledGaussianCalibratedStddev.lean:17–23`.

The clipping norm uses `EuclideanSpace` with L2, not the ambient function-space supremum norm. The vector Gaussian uses coordinate variance σ². The Poisson public wrapper also passes noiseStddev² to the variance-based law constructors. Its standardization equivalence is division by positive σ and sends the reference to N(0,1), and the source to the uncentered mixture with mean μ=Δ/σ (`SparseGaussianLikelihoodRatio.lean:178–240`, `SparseGaussianProductLikelihoodRatio.lean:139–198`). This is the direct privacy reference at zero, not a mean-centered matched Gaussian comparison.

**Consequence:** no factor-of-square or norm mismatch was found. **Confidence:** high.

### F3. The Poisson moment formulas and forward bound preserve the restricted reference mass

**Source:** P:192–209, P:260–405. **Formal:** `integral_sparseGaussianProductLikelihoodRatio_belowBox`, `integral_sparseGaussianProductLikelihoodRatio_sq_belowBox`, `integral_sparseGaussianProductLikelihoodRatio_sub_const_sq_belowBox_eq`, and `sparseGaussianProductLikelihoodRatio_closedCenteredSquare_nonneg` in `SparseGaussianTruncatedLikelihoodMoments.lean`; `integral_positivePart_le_of_integrable_sq` in `FiniteMeasurePositivePartSecondMoment.lean:47–93`; `sparseGaussianProductForwardProfile_le_cappedRestrictedSecondMomentUpperBound` and the named formula definitions in `SparseGaussianProductForwardUpperBound.lean`.

The exact second moment includes q² exp(μ²)Φ(a−2μ). Expanding the centered square retains α² p_Q, and Cauchy–Schwarz retains the factor p_Q under the root. The formal generic inequality uses the restricted finite measure, decomposes the positive-part integral into the retained set and its complement, and caps the inside by its source mass. These proof bodies follow the note's method, as well as proving its conclusion. The moment and positive-part declarations' axiom audits contain only propext, Classical.choice, and Quot.sound.

**Consequence:** the source's upper expression is supported under the original q∈[0,1], arbitrary real Δ/ξ, arbitrary finite T and threshold; no hidden positivity restriction on Δ or ξ was introduced. **Confidence:** high.

### F4. Lower and reverse directions are separately supported, including signed real duality

**Source:** P:343–362, P:407–459. **Formal:** `standardGaussianProductLaw_maximumEvent_probability`, `sparseGaussianProductLaw_maximumEvent_probability`, `sparseGaussianProductMaximumEventForwardLowerBound_le_profile`, `eventHockeyStickProfile_withDensity_reverse_duality`, `sparseGaussianProductReverseProfile_le_likelihoodFloorUpperBound`, and `sparseGaussianProductReverseProfile_le_bestUpperBound`.

The event is explicitly ∃i, a<x_i, whose complement is the all-coordinates ≤a box, so the source's strict maximum-event convention matches. The lower expression is a witness, not an asserted optimum. Reverse duality evaluates 1−exp(ε)+exp(ε)H_(−ε) in Real before embedding into ENNReal; it does not use truncated ENNReal subtraction for the signed constant. The likelihood-floor bound uses the product floor (1−q)^T. The final public upper theorem takes the maximum of the two directed estimates and keeps separate forward/reverse thresholds.

**Consequence:** neither privacy direction is silently discarded, and the potential signed-subtraction issue is handled correctly by the supplied proof. **Confidence:** high.

### F5. The calibration interval proves bounds on an infimum without assuming attainment

**Source:** P:472–535. **Formal:** `sampledGaussian_calibration_interval_of_finiteBracketWithThresholds_certificates` in `SampledGaussianFiniteBracketCalibration.lean:171–208`, using `sampledGaussian_feasibleSet_nonempty_of_upper_profile_certificate`, `le_sampledGaussianCalibratedStddev_of_not_feasible`, and `sampledGaussianProductProfileStddev_antitone`.

The formal feasible set is a subset of NNReal and includes zero. The calibrated quantity is its sInf. The upper certificate supplies a concrete feasible candidate and therefore nonemptiness. The lower proof uses a strict violation and upward closure to bound every feasible scale below by the lower candidate. The noise monotonicity proof adds a common residual Gaussian vector and remains valid at zero variance. Thus the theorem does not infer an infimum lower bound merely from one infeasible point without the needed order and nonemptiness facts. Its printed statement and proof body are preserved in `lean_controls.txt`.

**Consequence:** the source corollary and its no-attainment qualification are supported. The formal theorem actually allows more real ε/δ parameters through ENNReal.ofReal; restricting to the source's ε≥0, δ∈[0,1] gives the stated interpretation. **Confidence:** high.

### F6. Diagnostic arithmetic agrees with the stated numerical illustration

**Source:** P:544–580. At 80-digit mpmath working precision, direct substitution gives L=0.100028827432029808..., U_F=0.099452497237256984..., reverse dual upper=0.052593966541175706..., and reverse floor upper=0. The minimum reverse upper is therefore 0, and the forward expression is active. The displayed relative width evaluates to 6.4614544770...%. These match the note's rounded values.

**Evidence:** `numeric_control.py` and `numeric_control.txt`. **Consequence:** this arithmetic control found no numerical transcription error. It is not an outward rational certificate and does not validate the separately supplied PLD value. **Confidence:** high for the reproduced arithmetic; no formal numerical certification claimed.

## Abstentions and unresolved matters

**A1 — Full training-accountant endpoints are unavailable in the supplied proof closure.** The original obligation is D:88–126: a total executable exact-rational add/remove calibrator, finite-family minimality, and attained positive least scales for privacy uniformly over all record types, dimensions, and measurable adaptive oracles, for the exact specified mechanism. I did not replace that obligation with privacy of a fixed oracle or with a looser sensitivity accountant. The capsule has `TrainingMechanism.lean` but not the cited GenericRequest, CandidateChecker, RequestOnlyUpperCalibration, TrainingReduction, ExactSigmaThreshold, or global-optimality owners. Their declarations are not present in the environment imported by the supplied endpoints. I abstain from a formal verdict on those full assertions. Confidence in this coverage limitation: high; confidence in their ultimate truth is not assigned here.

**A2 — Signed adaptive domination and direct replacement are not fully verified.** Original obligation: D:253–284 and D:346–375 compare both directed stop losses of the adaptive clipped replacement mechanism to the exact ±k-subset scalar experiments, under the stated norm and sign alignment hypotheses. I checked the displayed algebra: from |<m_h,m_g>|≤|a_h a_g| and common sign of W_h a_h, each W_h W_g(a_h a_g−<m_h,m_g>) is nonnegative; multiplying by positive factors preserves that sign alignment. This supports the local sign argument. It is not a complete derivation of the integration-by-parts identity, measurable interpolation, smoothing limit, or backward adaptive path comparison. The two signed interpolation declarations and the uniform replacement upper theorem are not supplied. No counterexample or failed tactic is offered as evidence against the claim. I abstain on the complete sequential theorem.

**A3 — Lower realizations and positive attained training thresholds remain partly conventional.** Original obligation: D:286–323 and D:334–376 identify uniform privacy with exact formal-profile feasibility, recover laws by measurable projection, and prove the closed positive upper ray under 0<k≤T and 0<δ<1. The note's truncated-set infimum argument is coherent given continuity, monotonicity, nonempty feasibility, and a small-noise separating scale. The exclusions k=0 and δ≥1 are appropriate: then every positive scale can be feasible while no least positive scale exists. I did not independently formalize all analytic prerequisites or projected law identities; the named owners are absent. In particular, the available generic Poisson infimum theorem is not a substitute for the training fixed-cardinality attained-threshold theorem.

**A4 — Actual rational replay and full prior replay/axiom provenance are not certified here.** P:715–716 names `Mf.DP.sampledGaussian_calibration_interval_of_finiteBracket_replayCertificate`, which is not in this capsule's environment or local source inventory. P:646–669 describes a valid certificate scheme conditional on verified interval containments; no concrete outward rational certificate was supplied or reconstructed in this audit. D:403–407 and P:673–674 make prior replay/provenance claims beyond what this restricted run can establish. Only the ten explicitly audited supplied declarations receive the axiom observations reported here. This limitation is not an assertion that the named replay declaration does not exist elsewhere.

**A5 — External and runtime scope.** The bibliography, exact PLD diagnostic, external optimizer behavior, finite-precision samplers, application implementations, and broad benchmark claims were not verified. No claim is made about them. The note itself correctly distinguishes ideal mathematical laws from runtime conformance and diagnostic decimals from proof authority.

## Exact checks, evidence, and limits

All five top-level Lean/Lake invocations ran from `INPUT/capsule/lean` using pinned `leanprover/lean4:v4.33.0` and exited 0. No broad build was launched. Custom Lean files live only in OUTPUT/evidence.

| # | Command | Result / saved transcript |
| --- | --- | --- |
| 1 | lake env lean Mf/DP/Training/KOutOfT/TrainingMechanism.lean | Exit 0, no diagnostics; `lean_training.txt` |
| 2 | lake env lean Mf/DP/SampledGaussianProductFiniteProfileBounds.lean | Exit 0, no diagnostics; `lean_bracket.txt` |
| 3 | lake env lean Mf/DP/SampledGaussianFiniteBracketCalibration.lean | Exit 0, no diagnostics; `lean_calibration.txt` |
| 4 | lake env lean OUTPUT/evidence/CrosswalkAudit.lean (absolute path in ledger) | Exit 0; 51 crosswalk presence queries and 10 axiom audits; `lean_crosswalk.txt` |
| 5 | lake env lean OUTPUT/evidence/Controls.lean (absolute path in ledger) | Exit 0; exact T=2,k=1 schedule controls, arbitrary-q zero-horizon negative-shift/negative-ε instance of original upper theorem, printed calibration theorem/proof and transcript definition; `lean_controls.txt` |

The crosswalk audit found 3/38 training references and 12/13 Poisson references present. Presence is not by itself statement equivalence; the substantive present correspondences above additionally compare definitions, hypotheses, quantifier domains, conclusions, and proof bodies. `crosswalk-requests.json` preserves every queried exact name and source line. The ten `#print axioms` results all list only propext, Classical.choice, and Quot.sound; none lists sorryAx or a custom axiom. Owner-file replay uses the capsule's matching imported OLean environment and is not a clean rebuild of all dependencies.

Every audit subprocess, its exit status, timing, and output path is recorded in `evidence/commands.jsonl`, with complete captured stdout/stderr under `evidence/`. Bootstrap and artifact-writing operations are recorded in `evidence/setup-actions.json`; executable audit/control/report-generation scripts are retained. TeX and Lean source files were not changed.

Start (acknowledgment, before source reading): **START_TIME**. End / first-report freeze: **END_TIME**. Elapsed from acknowledgment: **ELAPSED_SECONDS** seconds. The initial PROMPT read and acknowledgment setup immediately preceded this timestamp and were not separately timed. Neither the 90-minute wall ceiling nor the 30-invocation ceiling was reached; invocation count **LEAN_COUNT**. Token telemetry: **unavailable**. `RUN-SUMMARY.json` stores these facts in machine-readable form.

Unexamined material: most unrelated local Lean dependency bodies were not read in full; only the relevant slices or full owners named in the transcripts were examined. No missing training proof owner, external dependency source, cited publication, parent project, prior audit, or other arm was inspected. Full TeX reading plus these focused checks support the claim-specific observations above, not certification of every informal assertion or all formal dependencies.
"""
report=report.replace('START_TIME',ack['start_time_utc']).replace('END_TIME',end.isoformat()).replace('ELAPSED_SECONDS',f"{summary['elapsed_seconds_since_ack']:.3f}").replace('LEAN_COUNT',str(count))
with (out/'FIRST-REPORT.md').open('x') as f:f.write(report)
os.chmod(out/'FIRST-REPORT.md',0o444)
hashrow={'path':'FIRST-REPORT.md','sha256':hashlib.sha256((out/'FIRST-REPORT.md').read_bytes()).hexdigest(),'frozen_utc':end.isoformat()}
(out/'evidence'/'first-report-sha256.json').write_text(json.dumps(hashrow,indent=2)+'\n')
print(json.dumps(summary,indent=2));print(json.dumps(hashrow,indent=2))
