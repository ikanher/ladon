# Independent review: common registration v1

**Reviewed:** 2026-11-12  
**Review scope:** `common-registration-v1.json` against the accepted corpus,
feasibility policy/r19 evidence, runtime custody, CLI parsers, Task 1.3d and the
baseline design.  
**Result:** accepted for configuration freeze. Later family command execution
and environment qualification remain pending under Tasks 1.4/2.2.

The read-only independent review verified:

- all 24 case IDs, family/role pairs, source quotes/spans, formal declarations,
  claims and obligations against `corpus/cases.json`;
- corpus/runtime identities and the six path/hash bindings to the feasibility
  policy, runner lock, r19 index, status addendum, blind adjudication and
  protocol review;
- corpus listing order is separate from staged execution order, which starts
  with feasibility, then provenance and operation-definedness, followed by the
  two full-baseline-only families;
- command arguments match the current parsers, including proof-slice application
  names for all four provenance subjects, separate source/formal and axiom
  probes for claim-trust, and the fixed generic proof tactic;
- operational projections withhold roles, expected evidence, oracle sources,
  and validation sources; the allowlist explicitly names `Pitfalls.lean` and
  `LeastElement.lean`, whose shared definitions contain no proof certificates or
  expected labels; and
- feasibility remains bound to its original accepted r19 profile. The other
  five profiles are registered but are not represented as batch-qualified or
  as proven unsupported.

The reviewer requested three revisions during review: separate listing order
from staged execution order, bind r19 artifacts by hash, and enumerate the
shared source modules permitted by isolation. All were applied and confirmed.
The reviewer also checked the premise route and claim-trust observables; their
registered commands now cover the declared judgment dimensions.

## Remaining qualification boundary

This review accepts the common configuration only. It does not qualify a new
family runtime, establish mathematical outcomes for unrun cases, or close Tasks
1.4, 2.1, or 2.2. Those later runs must apply the frozen profiles and retain
their own isolation, preparation, resource and independent-adjudication
receipts.
