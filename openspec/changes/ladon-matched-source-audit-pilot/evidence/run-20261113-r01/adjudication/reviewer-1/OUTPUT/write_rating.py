import json
from pathlib import Path
root=Path('/home/codex/projects/ladon/openspec/changes/ladon-matched-source-audit-pilot/evidence/run-20261113-r01/adjudication/reviewer-1')
claims=json.loads((root/'INPUT/SCORE-POPULATION.json').read_text())['selected_claims']
checks=['evidence/registered_checks.command.txt','evidence/registered_checks.lean','evidence/registered_checks.output.txt','evidence/registered_checks.exit.txt']
base=[
 dict(assertion='With unit Euclidean clipping, zero initial history, measurable adaptive queries, fixed independent user k-subsets, and independent Gaussian releases, the complete conditional history transcript is formed before averaging hidden schedules.',
      assumptions='Record is an arbitrary type with decidable equality; datasets are finite sets. Source T>0, k<=T, arbitrary finite output dimension, positive sigma. Formal definition permits broader T, k, clippingNorm and initialHistory parameters; specialize clippingNorm=1 and initialHistory=zeroAdaptiveReleaseHistory.',
      argument='TrainingMechanism.lean: scheduledClippedAggregate sums only scheduled users after l2VectorClip. transcriptGivenScheduleAssignment keeps the same assignment through its recursive bind chain and writes one release at each step. kOutOfTTrainingTranscript sums assignment-weighted complete T-step laws outside that chain. AdaptiveTrainingOracle requires measurability in history. EuclideanVectorClipping.lean defines l2Norm using EuclideanSpace; FiniteGaussianDensity.lean measure uses coordinate Gaussian variance sigma squared. At zero initial history unwritten slots are public zero, so the infinite-history representation adds no private information or extra future observations.',
      consequence='Confirms the modeled mechanism has retained hidden schedules and the intended clipping/noise units. This does not certify its later privacy reduction, calibration procedure, or threshold theorems.',
      extra=['Mf/DP/Training/Common/AdaptiveTranscript.lean: AdaptiveTrainingOracle, zeroAdaptiveReleaseHistory','Mf/DP/EuclideanVectorClipping.lean: l2Norm, l2VectorClip_norm_le','Mf/Probability/FiniteGaussianDensity.lean: measure, measure_eq_pi'],
      unresolved=[]),
 dict(assertion='Each user independently receives the uniform probability mass on the cardinality-k subsets of Fin T.',
      assumptions='T,k are natural numbers with k<=T. T>0 is imposed by the source but is unnecessary for this normalization theorem. No independent-coordinate Bernoulli assumption is present.',
      argument='fixedCardinalityScheduleMass delegates to bisFixedCardUniformMass on Finset.univ. That definition is inverse choose(T,k) on powersetCard k and zero elsewhere. The registered normalization theorem assumes k<=T and proves the sum on all schedules is one. userScheduleAssignmentMass is the product of these masses over dataset members, and its normalization factors the finite product of sums. These are exact probability weights; ENNReal.ofReal in the transcript does not change nonnegative weights.',
      consequence='Confirms fixed-cardinality uniform schedules and independence across users; prevents substituting a Bernoulli participation law that would change the mechanism.',
      extra=['Mf/DP/OptimalSubsamplingBISLR.lean: bisFixedCardUniformMass','Mf/DP/Training/KOutOfT/TrainingMechanism.lean: userScheduleAssignmentMass, userScheduleAssignmentMass_sum_eq_one'],
      unresolved=[]),
 dict(assertion='The positive part of 1-pP(a)-exp(epsilon)*(1-pQ(a)) is a lower witness for the exact two-sided profile of the sampled Gaussian product.',
      assumptions='Arbitrary horizon Nat including zero; samplingRate NNReal with <=1, so exactly source q in [0,1]; arbitrary real sensitivity, epsilon and threshold; positive NNReal noise standard deviation. Standardized shift is sensitivity/noiseStddev; laws receive noiseStddev squared.',
      argument='SampledGaussianProductMaximumEvent.lean defines the event as existence of a coordinate strictly above threshold and belowBox as the product of closed Iic sets. Exact source/reference probabilities are the displayed complement probabilities. SparseGaussianProductMaximumEventLowerBound.lean proves equivalence to the positive part of the real formula and applies the event-supremum witness theorem. The public facade transports by positive scaling and then bounds by the maximum of directed profiles.',
      consequence='Certifies the stated lower witness with no claim of event optimality. At T=0 the event is empty and its witness is zero; this is compatible with a positive identical-law profile when epsilon<0. The source explicitly defines the event as the complement of the box, which resolves its empty-maximum notation.',
      extra=['Mf/DP/SampledGaussianProductMaximumEvent.lean: sparseGaussianProductMaximumEvent, standardGaussianProductLaw_maximumEvent_probability, sparseGaussianProductLaw_maximumEvent_probability','Mf/DP/SparseGaussianProductMaximumEventLowerBound.lean: ennreal_ofReal_sparseGaussianProductMaximumEventForwardLowerBoundReal, sparseGaussianProductMaximumEventForwardLowerBound_le_profile'],
      unresolved=[]),
 dict(assertion='The forward directed profile is bounded by 1-pP+min(pP,(sqrt(pQ*v)+pP-exp(xi)*pQ)/2), retaining restricted reference mass in both required places.',
      assumptions='Arbitrary finite T, q in [0,1], arbitrary real shift/xi/threshold, and positive noise standard deviation. No positive-shift or nonnegative-xi restriction is added. Generic retained measure is finite and the supplied squared likelihood residual is integrable.',
      argument='SparseGaussianProductForwardUpperBound.lean gives exactly the source formulas: m2 has q^2*exp(mu^2)*Phi(a-2mu); v=m2-2*exp(xi)*pP+exp(2xi)*pQ; residual has sqrt(pQ*v). FiniteMeasurePositivePartSecondMoment.lean obtains the finite-measure inequality via |x|+x and Cauchy-Schwarz with total measure mass. FiniteProfileRestrictedSecondMomentUpperBound.lean splits the positive-part integral on the closed box/complement, bounds the complement by source mass and the inside by the smaller source-mass/residual bound. SparseGaussianTruncatedLikelihoodMoments.lean identifies exact moments using product factorization, tilting and square expansion. The public facade only transports this result under positive scaling.',
      consequence='Supports both the claimed bound and its described proof method, including the pQ factor whose loss would change the numerical bracket.',
      extra=['Mf/DP/FiniteMeasurePositivePartSecondMoment.lean: integral_positivePart_le_of_integrable_sq','Mf/DP/FiniteProfileRestrictedSecondMomentUpperBound.lean: eventHockeyStickProfile_withDensity_forward_le_restrictedSecondMomentCapped','Mf/DP/SparseGaussianProductForwardUpperBound.lean: sparseGaussianProductForwardCappedRestrictedSecondMomentUpperBoundReal','Mf/DP/SparseGaussianTruncatedLikelihoodMoments.lean: integral_sparseGaussianProductLikelihoodRatio_sub_const_sq_belowBox_eq'],
      unresolved=[]),
 dict(assertion='The reverse directed profile is bounded by the positive part of 1-exp(epsilon)*(1-q)^T.',
      assumptions='Arbitrary horizon including zero, q in [0,1] including endpoints, arbitrary real sensitivity/epsilon, positive noise standard deviation. The normalized reference is a probability measure and exp(epsilon)>0.',
      argument='SparseGaussianProductLikelihoodRatio.lean proves the product likelihood floor (1-q)^T from the coordinate floors using nonnegative factors. SparseGaussianProductReverseBounds.lean rewrites the reverse profile as the integral of the positive part of 1-exp(epsilon)*Lambda, applies the pointwise floor, and integrates the resulting constant over the reference probability law. The public facade transports by the same scaling equivalence. There is no division by q or 1-q.',
      consequence='Confirms an independent valid reverse bound, including the endpoint sampling rates and empty horizon. It can safely be combined by a minimum with the reciprocal bound.',
      extra=['Mf/DP/SparseGaussianProductLikelihoodRatio.lean: sparseGaussianProductLikelihoodRatio_ge_floor','Mf/DP/SparseGaussianProductReverseBounds.lean: sparseGaussianProductReverseLikelihoodFloorUpperBound, sparseGaussianProductReverseProfile_le_likelihoodFloorUpperBound'],
      unresolved=[]),
 dict(assertion='A strict lower profile certificate at positive sigmaL and a non-strict upper certificate at positive sigmaU bound the nonnegative feasible-set infimum between sigmaL and sigmaU without assuming attainment.',
      assumptions='Source epsilon>=0 and delta in [0,1], arbitrary T, q in [0,1], real sensitivity; positive lower and upper NNReal candidates; three independent real thresholds. Formal theorem allows arbitrary real epsilon/delta through ENNReal.ofReal; restricting to the source domain gives its exact meaning. No extra admissibility/strict-rate/positive-sensitivity hypothesis is required.',
      argument='SampledGaussianCalibratedStddev.lean defines feasibility over all NNReal, including zero, and calibrated noise as sInf. The adapter first uses the upper certificate to prove feasibility and nonemptiness. Its lower branch proves the lower candidate infeasible, then invokes le_sampledGaussianCalibratedStddev_of_not_feasible. That lemma uses upward closure from profile antitonicity and le_csInf, rather than inferring a lower bound from an isolated infeasible point alone. The antitonicity theorem uses a common residual Gaussian vector and includes zero variance. The final conjunction is non-strict at both interval endpoints.',
      consequence='Confirms the infimum interval exactly as stated, while preserving the distinction between a certified interval and an attained or executable optimum.',
      extra=['Mf/DP/SampledGaussianCalibratedStddev.lean: sampledGaussianFeasibleStddevSet, sampledGaussianCalibratedStddev','Mf/DP/SampledGaussianCalibrationThresholds.lean: sampledGaussianFeasibleStddevSet_upward_closed, le_sampledGaussianCalibratedStddev_of_not_feasible','Mf/DP/SampledGaussianProductNoiseMonotonicity.lean: sampledGaussianProductProfileStddev_antitone'],
      unresolved=[])
]
refs={'X':[['Finding 1'],['Finding 1'],['Finding 4'],['Finding 3'],['Finding 3'],['Finding 5']],
      'Y':[['Findings 1 and 2'],['Finding 1'],['Finding 4'],['Finding 3'],['Finding 4'],['Finding 5']]}
records=[]
for report in ['X','Y']:
 for i,(claim,r) in enumerate(zip(claims,base),1):
  records.append({'record_id':f'{report}-C{i}', 'report':report, 'registered_claim_index':i,
   'report_locations':refs[report][i-1], 'identity':dict(claim,interpreted_assertion=r['assertion']),
   'judgment':'supported/faithful correspondence', 'treatment':'correct correspondence/control',
   'source_to_formal_correspondence':r['argument'], 'assumptions_domains_quantifiers':r['assumptions'],
   'argument_evidence':{'primary_source':'INPUT/capsule/sources/'+claim['source_path'], 'primary_lean':'INPUT/capsule/lean/'+claim['lean_path'], 'additional_directly_inspected_lean':r['extra'], 'bounded_check_artifacts':checks, 'check_result':'Exit 0. The six registered declarations resolve; their axiom lists contain only propext, Classical.choice, Quot.sound. Source bodies and definitions were inspected separately; #check alone is not treated as correspondence evidence.'},
   'reader_usefulness':{'useful':True,'reason':r['consequence'],'upheld_useful_discrepancy':False},
   'false_accusation_severity':{'level':'none','reason':'The report treats this claim as a faithful control and does not allege a false or unsupported source result.'},
   'confidence':{'level':'high','scope':'Source/formal correspondence for this registered claim; no whole-note or runtime certification.'},
   'unresolved_questions':r['unresolved']})

exploratory=[]
def exp(report,key,loc,span,assertion,judgment,treatment,evidence,reason,questions=None,confidence='high'):
 exploratory.append({'record_id':f'{report}-E{key}','report':report,'report_locations':loc,'population_status':'outside the registered six-unit population; exploratory only','source_span':span,'interpreted_assertion':assertion,'judgment':judgment,'treatment':treatment,'source_formal_evidence':evidence,'reader_usefulness':{'useful':True,'reason':reason,'upheld_useful_discrepancy':False},'false_accusation_severity':{'level':'none','reason':'No false mathematical accusation is made; coverage limits and conditional reasoning are explicitly separated from falsity.'},'confidence':{'level':confidence,'scope':'Limited to the correspondence, arithmetic, or warranted abstention described here.'},'unresolved_questions':questions or []})
for report in ['X','Y']:
 exp(report,1,['Finding 2' if report=='X' else 'Finding 2; Finding 3'], 'P 135-193, 260-339; K 65-69',
  'Direct scaling, product mixture laws, exact likelihood moments and standard-deviation/Euclidean-norm units match the notes.',
  'supported/faithful correspondence','correct correspondence/control',
  'SampledGaussianOutputLaws.lean constructs Bernoulli-shift-plus-Gaussian coordinates and independent products; SparseGaussianProductLikelihoodRatio.lean transports source/reference by division by positive sigma with standardized shift Delta/sigma. SparseGaussianTruncatedLikelihoodMoments.lean has the displayed first, second and centered square identities with unrestricted real shift and coefficient. EuclideanVectorClipping.lean uses EuclideanSpace and FiniteGaussianDensity.lean uses sigma-squared variance. The parts needed by registered C1/C4 are rated there; this entry retains their other source spans only.',
  'Confirms the exact privacy reference and formulas, rather than a matched-source comparison or a variance/stddev substitution.')
 exp(report,2,['Finding 3' if report=='X' else 'Finding 4'], 'P 407-434, 456-459; P 224-236',
  'Real-valued reverse duality, min of reverse bounds and max of directed bounds support independent supplied thresholds.',
  'supported/faithful correspondence','correct correspondence/control',
  'FiniteProfileCoefficientDuality.lean eventHockeyStickProfile_withDensity_reverse_duality evaluates 1-exp(epsilon)+exp(epsilon)*H(-epsilon).toReal in Real before ENNReal.ofReal. SparseGaussianProductReverseBounds.lean applies the capped forward bound at -epsilon and uses finiteness for toReal monotonicity. SampledGaussianProductFiniteProfileBounds.lean explicitly takes min for reverse and max for two directions with distinct forward/reverse threshold arguments; lower threshold is independent. All require only the original q domain and positive noise, with arbitrary real epsilon.',
  'Rules out a signed truncated-subtraction error or an omitted privacy direction. This is a faithful control, not an observed defect.')
 exp(report,3,['Finding 6'], 'P 544-580',
  'The diagnostic decimal substitution and reported relative width agree with the displayed formulas.',
  'supported/faithful correspondence','correct correspondence/control',
  'Independent bounded 60-digit mpmath calculation: L=0.1000288274320298083766..., UF=0.0994524972372569846839..., reverse dual=0.0525939665411757068291..., reverse floor=0, relative width=6.4614544770271348825... percent. Exact command, script, output and exit 0 are preserved in evidence/coverage_numeric_check.*. This is approximate numerical evaluation, not outward rational certification.',
  'Confirms rounded arithmetic only. It supplies neither a formal rational certificate nor an independent PLD computation.',
  ['The separate PLD diagnostic value is used as given, not validated.'])
 exp(report,4,['Finding 6' if report=='X' else 'A3; source inventory D:226-251 and D:379-407'], 'K 226-251, 379-400',
  'Fallback arithmetic, finite-family versus global minimum, and k=0/delta>=1 degeneracies are correctly distinguished.',
  'supported/faithful correspondence','correct correspondence/control',
  'Direct source arithmetic: (k+1)/delta>0 for natural k and delta>0, and k*delta/(2*(k+1))<=delta. With k=0 the aggregate is zero and the transcript is data independent; with delta>=1 probability-law hockey-stick profiles at epsilon>=0 are <=1. All positive scales can then be feasible while their infimum zero is not a positive minimum. IsGlobalSigmaThreshold explicitly requires positivity and feasibility at the endpoint. This does not verify the absent checker or its termination.',
  'Prevents treating the finite-grid return value or a zero unattained infimum as an attained positive global threshold.')
 exp(report,5,['Abstention 1' if report=='X' else 'A1'], 'K 88-113, 191-251, 327-344; crosswalk 409-499',
  'Full finite exact-rational accountant and universal add/remove endpoints cannot be certified from the provided capsule.',
  'ambiguous/underspecified (abstention warranted)','warranted abstention',
  'INPUT-only inventory check finds 63 local Lean files. Of 25 unique K cited Lean paths, only TrainingMechanism.lean is present; 24 named owners are absent. Local source searches for the named checker/bridge/reduction endpoints return no match, recorded in evidence/coverage_numeric_check.output.txt. The theorem in K quantifies over every record type with decidable equality, every dimension, every measurable adaptive oracle, and valid rational requests, and promises termination and accepted-family minimality. Mechanism definitions do not imply these conclusions. Source add/remove decoder and fallback explanation are coherent but not a complete supplied formal endpoint.',
  'Makes the capsule coverage limit explicit without claiming a counterexample or absence from a larger project.',
  ['Full checker termination, rational witness soundness, finite-family leastness and universal adaptive add/remove theorem remain unverified here.'])
 exp(report,6,['Abstention 2' if report=='X' else 'A2'], 'K 253-284, 346-376',
  'The local signed compensation argument is plausible; the complete adaptive replacement domination is unresolved in this capsule.',
  'ambiguous/underspecified (abstention warranted)','warranted abstention',
  'Source norm bound and common sign of W_h*a_h imply W_h*W_g*(a_h*a_g-<m_h,m_g>)>=0, including zero amplitudes; multiplying by positive constants preserves sign. This local algebra alone does not establish the integration-by-parts interpolation, smoothing limit or history-dependent backward path comparison. The crosswalk names DirectReplaceSignedGaussianInterpolation.lean and other replacement owners which the input inventory confirms absent. No failed tactic or counterexample is asserted.',
  'Correctly preserves the unresolved sequential theorem instead of accepting local sign algebra as its proof or using missing declarations as refutation.',
  ['A complete derivation handling history dependence and future likelihood factors remains unavailable; mathematical truth of the full statement is not decided.'])
 exp(report,7,['Abstention 3' if report=='X' else 'A3'], 'K 286-323, 334-376',
  'Training lower realizations and positive attained global thresholds are not established by the generic Poisson infimum theorem or generic threshold definition.',
  'ambiguous/underspecified (abstention warranted)','warranted abstention',
  'K requires universal-oracle privacy equivalent to exact fixed-cardinality profile feasibility, with projection realizations and attained positive upper rays when 0<k<=T and 0<delta<1. The source truncated closed-set infimum argument is valid conditional on continuity, degradation, nonempty feasibility and a positive separating scale. Training/Common/GlobalSigmaOptimality.lean contains the generic threshold definition, while input inventory lacks the KOutOfT profile/realization/threshold owners named in the crosswalk. The registered Poisson calibration adapter concludes only an infimum interval.',
  'Avoids substituting a different sampling model or an unattained infimum for the source quantified attainment result.',
  ['Exact projected law identities and domain-specific analytic prerequisites for the claimed thresholds remain unverified.'])
 exp(report,8,['Abstention 4' if report=='X' else 'A4'], 'P 646-669, 673-716; K 402-407',
  'The named concrete replay endpoint and historical replay/provenance assertions are not independently substantiated here.',
  'ambiguous/underspecified (abstention warranted)','warranted abstention',
  'The P source names sampledGaussian_calibration_interval_of_finiteBracket_replayCertificate, but the input-only local Lean source search has no match (evidence/coverage_numeric_check.output.txt). The mathematical interval recipe is conditional on proved transcendental containments and verified rational root bounds. No concrete certificate is supplied. Independent registered endpoint axiom checks pass with only the three standard listed axioms, but these do not substantiate historical full-note replay or claims about absent endpoints.',
  'Separates abstract real-valued interval bounds, approximate decimals, concrete exact-rational replay, and historical provenance.',
  ['Whether the named declaration exists elsewhere, and the historical replay assertions, cannot be determined within this blinded input.'])
 if report=='Y':
  exp(report,9,['A5'], 'P bibliography and P 544-590; K 391-407',
   'External literature, optimizer/runtime behavior and separately supplied PLD values are outside this verification.',
   'ambiguous/underspecified (abstention warranted)','warranted abstention',
   'Both sources delimit their mathematics to ideal laws and distinguish diagnostic decimals from theorem authority. No application implementation, finite-precision sampler or independent PLD computation is in the supplied source obligations being verified. No outside sources were accessed.',
   'Prevents mathematical correspondence from being read as implementation or literature certification.',
   ['External and runtime assertions remain unverified by design.'])

out={'schema_version':1,'reviewer':'reviewer-1','packet_identities':['X','Y'],'signed_by':'pilot_blind_adjudicator_1','signed_date':'2026-11-13',
 'independence_statement':'Fresh independent blinded review; ROLE-ACK.json was saved before dossiers were read. Only this reviewer INPUT and OUTPUT were inspected or written, with the provided pinned Lean environment used for bounded local checks. No arm identity was inferred or sought and no answer key or other reviewer findings were consulted.',
 'method':'Read the rubric, registered score population, both anonymized dossiers, relevant TeX statements/proofs/crosswalks and Lean definitions/types/proof bodies directly. Ran one bounded Lean declaration/axiom check and one bounded input-only coverage/numerical check. Source/formal correspondences are supported by direct inspection as described per record, not by successful tactic execution alone.',
 'registered_report_claim_ratings':records,'exploratory_ratings':exploratory,
 'summary_by_report':{r:{'registered_claim_count':6,'correct_correspondence_controls':6,'warranted_abstentions_in_registered_population':0,'no_treatment_in_registered_population':0,'upheld_useful_discrepancies_in_registered_population':0,'unsupported_accusations_in_registered_population':0,'unresolved_registered_items':0,'false_accusation_severity':'none','note':'The report labels several faithful controls as Findings. They are not discrepancy findings. Its larger-note abstentions are exploratory relative to the six registered claims.'} for r in ['X','Y']},
 'unresolved_internal_disagreements':[],
 'limits':['This adjudication establishes neither whole-note certification nor runtime conformance.','Reports historical actions and withheld original command artifacts were not independently inspected; only bounded checks recorded here were run.','Unresolved exploratory full-training and replay claims receive no discrepancy or false-accusation credit.','No inferred arm/tool identity or comparison based on identity is included.'],
 'signature':{'name':'pilot_blind_adjudicator_1','attestation':'I independently applied the supplied rubric to X/Y and submit these ratings as my signed blinded adjudication.'}}
(root/'OUTPUT/RATING.json').write_text(json.dumps(out,indent=2)+'\n')
assert len(records)==12
assert {x['report'] for x in records}=={'X','Y'}
for r in ['X','Y']:
 assert sorted(x['registered_claim_index'] for x in records if x['report']==r)==[1,2,3,4,5,6]
print(json.dumps({'rating_written':str(root/'OUTPUT/RATING.json'),'registered_records':len(records),'exploratory_records':len(exploratory),'json_valid':True}))
