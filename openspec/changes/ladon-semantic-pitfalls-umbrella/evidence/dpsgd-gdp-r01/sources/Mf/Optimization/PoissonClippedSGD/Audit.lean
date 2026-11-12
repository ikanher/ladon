import Mf.Optimization.PoissonClippedSGD

/-!
# Public theorem trust audit

These prints expose the final theorem boundary and logical axioms. They are
checked against the allowed standard logical axioms during project validation.
-/

open Mf.Optimization.PoissonClippedSGD
#print gaussian_convergence
#print gaussian_convergence_with_rates
#print finite_sum_gaussian_convergence
#print axioms clippedMean_alignment
#print axioms integral_norm_sq_sampledGradient
#print axioms gaussianVectorLaw_energy
#print axioms gaussian_actual_one_step
#print axioms Trajectory.commonHistory_fin_average_potential_le
#print axioms gaussian_convergence
#print axioms gaussian_convergence_with_rates
#print axioms finite_sum_gaussian_convergence

#print axioms output_norm_integrable
#print axioms output_integral_average
#print axioms uniform_output_convergence
#print axioms retunedBudget_exact
#print axioms retunedBudget_ceiling
#print axioms retunedBudget_improves_initial
#print QuadraticApplication.expected_norm_lt
#print axioms QuadraticApplication.expected_batch_size
#print axioms QuadraticApplication.step_gate
#print axioms QuadraticApplication.output_norm_integrable
#print axioms QuadraticApplication.expected_norm_le_budget
#print axioms QuadraticApplication.expected_norm_lt
#print axioms QuadraticApplication.expected_norm_improves_initial
