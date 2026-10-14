# Actual applications and premise producers

This is an answer-informed source review. Owner files are frozen under formal-sources; checks of selected estimates are separately recorded in runs/target-01.

1. **Inverse:** SmoothFamilyTorusInverse.inverse_finiteJets (865) invokes applyMultiplier_finiteJets with loss parameter 1. UniformFourierAlias.realInverse_finiteJets (616) supplies smooth complexification, periodicity and the input jet bounds to that theorem. GaugeAliasDecay.familyInverse_finiteJets_fiber (34) converts a finite jet bound on a fiber shell into the premise on a product set. These actual consumers explicitly request m+5. A class allowing every fixed derivative order can use them without supplying the precise four-loss statement. That is a distinction between a downstream class argument and the particular quantitative estimate; no full downstream chain is certified here.

2. **Pressure:** R3/WholeSpaceUniqueness.classical_uniqueness_on_Icc first constructs PressureRecovery.Hypotheses from compactness, smoothness, divergence and the same equation; it obtains uniform L2, L3 and L1 tensor bounds from their producers. It then invokes exists_uniform_actual_pressure_flux_bound at line 60 and feeds that A-dependent bound to WholeSpaceComparisonClosure.eq_of_pressure_flux_bound. The estimates are supplied from hypotheses already in the formal uniqueness theorem. This is an actual alternative proof route, not a record that the paper's exact intermediate flux statement was checked.

3. **Construction invariant:** ActualCyclePreservation.particularData invokes ActualParticularCycleData.actual_data from the current analytic invariant, periodicity and fixed geometry. next_runInvariant uses that concrete data in next_runInvariant_of_particular. Inspecting only a generic StepData interface would miss these producers. The historical endpoint checks remain scoped endpoint checks and do not supply correspondence for the new source inventory.

4. **Small producer control:** Controls.lean defines PremiseData, a generic consumer and a producer of the needed premise for squares. The fresh actual_consumer check demonstrates that the premise is derived for this concrete application, independently of any argument about the research construction.

Unexamined hypotheses, other branches and the full transitive proof closure remain outside these source-local findings. Lexical edges are not treated as elaborated dependencies.
