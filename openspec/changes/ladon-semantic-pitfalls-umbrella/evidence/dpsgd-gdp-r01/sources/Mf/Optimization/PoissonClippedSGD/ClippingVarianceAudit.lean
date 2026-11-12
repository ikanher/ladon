import Mf.Optimization.PoissonClippedSGD.ClippingVariance

/-!
# Audit of variance-only record clipping

The declarations produce a clipped-query decomposition from the actual finite
record mean and centered variance. They assert no Adam alignment or utility.
-/

#check Mf.Optimization.PoissonClippedSGD.ClippingVariance.clippedMean_eq_meanWeight_smul_add_bias
#check Mf.Optimization.PoissonClippedSGD.ClippingVariance.meanClipWeight_lower
#check Mf.Optimization.PoissonClippedSGD.ClippingVariance.centeredClipBias_norm_le_min

#print axioms Mf.Optimization.PoissonClippedSGD.ClippingVariance.euclideanBallClip_eq_clipWeight_smul
#print axioms Mf.Optimization.PoissonClippedSGD.ClippingVariance.clipWeight_mem_Icc_one
#print axioms Mf.Optimization.PoissonClippedSGD.ClippingVariance.radialClipFactor_sub_le
#print axioms Mf.Optimization.PoissonClippedSGD.ClippingVariance.clipWeight_sub_le_norm_div
#print axioms Mf.Optimization.PoissonClippedSGD.ClippingVariance.clippedMean_eq_meanWeight_smul_add_bias
#print axioms Mf.Optimization.PoissonClippedSGD.ClippingVariance.centeredClipBias_norm_le
#print axioms Mf.Optimization.PoissonClippedSGD.ClippingVariance.centeredClipBias_norm_le_variance_div
#print axioms Mf.Optimization.PoissonClippedSGD.ClippingVariance.meanClipWeight_lower
#print axioms Mf.Optimization.PoissonClippedSGD.ClippingVariance.centeredClipBias_norm_le_min
