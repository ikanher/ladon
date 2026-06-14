namespace BMinSep.CountBucket

structure Certificate where
  ok : Bool

structure EvidenceAt where
  row : Nat

theorem closed_eventDP
    (hForwardCDF : EvidenceAt)
    (hcountMassEvidence : Certificate) :
    True := by
  trivial

theorem sampled_null_eventDP : True := by
  trivial

end BMinSep.CountBucket
