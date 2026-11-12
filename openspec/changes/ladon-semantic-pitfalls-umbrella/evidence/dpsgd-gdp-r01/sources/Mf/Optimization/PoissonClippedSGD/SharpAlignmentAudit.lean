import Mf.Optimization.PoissonClippedSGD.SharpAlignment

/-! Audit the sharpened full-vector clipping alignment used by V=0 cells. -/

#check Mf.Optimization.PoissonClippedSGD.norm_clippedMean_sub_mean_le_of_half
#check Mf.Optimization.PoissonClippedSGD.clippedMean_alignment_sharp

#print axioms Mf.Optimization.PoissonClippedSGD.norm_clippedMean_sub_mean_le_of_half
#print axioms Mf.Optimization.PoissonClippedSGD.clippedMean_alignment_sharp
