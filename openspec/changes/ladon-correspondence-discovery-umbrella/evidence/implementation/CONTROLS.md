# Portable mathematical controls

All controls are authored examples, not observed research-paper faults. Controls.lean compiles against the pinned r70 environment; runs/controls-01 records the fresh declaration checks and ten explicit axiom reports. The imports were already compiled and were not independently kernel-rebuilt.

| Question | Control/evidence | Assessment |
| --- | --- | --- |
| Renamed variable | renamed_bound returns exactly its premise | Same claim; naming changes do not establish drift |
| Expanded definition | definition_expansion is reflexivity | Equivalent representation |
| Norm conversion | max_norm_le_sum and sum_norm_le_twice_max prove the two inequalities with constants independent of a,b | Justified equivalent finite-dimensional norms, not literal equality |
| Stronger sufficient theorem | stronger_suffices derives x<=3 from x<=2 | The implication is in the required direction |
| Harmless constant change | harmless_constant uses y>=0 to pass from x<=y to x<=2y | Valid weaker conclusion; context matters |
| Harmful constant dependence | pointwise_constant holds, while no_uniform_constant refutes a single bound for all reals | Quantifier/constant dependence is load-bearing |
| Reversed comparison | reversed_comparison_witness has B=0, A=1, flux=1 | B<=A and flux<=A do not imply flux<=B; not a refutation of either Navier–Stokes estimate |
| Premise added during repair | OriginalGoalAttempt fails on unrestricted x; narrowed_goal assumes x>=0; unrestricted_goal_false has witness -1 | Successful repair is a separate proposition; the failed tactic alone is not the refutation |
| Wrong step, true endpoint | wrong_step_at_zero disproves a factorization; true_endpoint proves nonnegativity from the correct expression | Final success does not discharge the wrong local identity |
| Valid alternative method | direct_method sums square positivity; expanded_method rewrites to a different sum of squares | Both check; argument routes differ without falsity |
| Generic assumption versus concrete producer | generic_consumer reads PremiseData; actual_producer proves the field by square positivity; actual_consumer uses it | Inspect the producer before alleging that the result was simply assumed |

The last two method judgments follow the actual proof bodies, not their axiom lists. Declaring policyAccepted=true only observes the requested named Lean declarations under the allowed axioms. It does not check these prose judgments.
