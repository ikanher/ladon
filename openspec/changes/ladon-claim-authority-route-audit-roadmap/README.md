# ladon-claim-authority-route-audit-roadmap

Umbrella packet for making claim authority route auditing Ladon's next priority.

The design question is:

```text
Does the claim's authority label match the evidence route?
```

This packet does not ask Ladon to prove theorem truth. It asks Ladon to catch
process overclaims such as "fully Lean closed" when the observed route still
contains imported certificate rows, interval-certified evidence, missing primary
theorem surfaces, or a narrower endpoint scope.

Architecture smell work remains useful, but secondary to this authority-route
audit.
