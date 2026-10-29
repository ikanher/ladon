# Coordinate derivative norm bridge

## Result

Lean checks a generic finite-coordinate/operator-norm comparison and its
specialization to the existing Plane inverse theorem. This closes the
**chosen coordinate-versus-Fréchet convention** part of the local comparison,
without identifying the paper's unspecified norm or closing umbrella Task 2.1.

For a continuous n-linear map, exact expansion in d coordinate vectors and
coordinate coefficients bounded by the vector norm give
`coordinate components <= C  =>  operator norm <= d^n * C`, with `C >= 0`.
On Plane with the product max norm, the reverse implication has factor one.
For all derivative orders up to n the conversion factor is `2^n`.
The constants depend on dimension/order, not the function or its input bound.
The generic comparison supports arbitrary real normed domain/codomain spaces
satisfying these expansion hypotheses; it contains no inverse-specific logic.

`coordinateWord_eq` and `wordBound_iff` check that the coordinate tensor
convention agrees with explicitly ordered repeated coordinate partials of a
smooth complex-valued function. Order zero is checked as the function value.
`factor_one_is_false` is a checked counterexample: the sum functional has both
unit-coordinate values equal to one, but operator norm at least two in the
product max norm. Thus constants cannot simply be discarded in a transport.

The prior zero-parameter adapter is reused unchanged. Converting the input
bound, applying the original inverse theorem, then converting its output gives
`coordinate_inverse_five`. Its multiplier is `K * 2^(n+5)`, chosen before the
function and bound. It still requires **five** additional derivative orders.
A fresh application with only four orders fails exactly at that input premise.
This is a limitation of the selected proof route, not a mathematical
counterexample to the four-order estimate.

## Evidence and checks

- [CoordinateNormBridge.lean](CoordinateNormBridge.lean): complete standalone
  adapter and axiom reports; [CoordinateCore.lean](CoordinateCore.lean): general
  coordinate comparison and repeated-partial convention.
- [FreshSourceBridge.lean](FreshSourceBridge.lean): exact original selected
  source prefix, followed by the adapter. Direct Lean check passed in 5.46s.
  [FreshFourProbe.lean](FreshFourProbe.lean) has that same prefix and adapter,
  followed by the deliberately failing four-order application (5.45s).
- [VERIFICATION.json](VERIFICATION.json): actual process receipts, input
  integrity and result distinctions. Final proof byte-identical to checked
  attempt 6. All displayed successful declarations depend only on `propext`,
  `Classical.choice`, and `Quot.sound`.
- [reviewer/audit.md](reviewer/audit.md): independent Luna source/receipt audit,
  board post 1868. The auditor did not rerun Lean; root ran every check.
- Attempts 1, 3 and 4 retain the failed elaboration diagnostics. They are not
  accepted proofs. Attempts 2, 5 and 6 passed their respective increasing scopes.
  The deliberate final rejection remains separate from those development errors.

Eight Lean processes consumed 20.23s total measured process time; maximum
process-tree RSS was about 3.31 GiB. All ran within one 600-second absolute
clock for this new norm-bridge objective, with a 12 GiB RSS and 8 MiB output
cap. There were no resource stops or budget resets. The execution wrapper,
commands, environment library roots and individual process receipts are saved.
No full dependency rebuild is claimed: the selected original source was freshly
compiled against the pinned existing dependency libraries.

Integrity checks confirm 610 runtime files, 2,670 primary files, 67 previous
source-pair evidence files, and three paper inputs unchanged. No runtime,
tests, dependencies, source paper or original formalization were edited.
No full Python suite was rerun for this evidence-only change. Nothing was pushed.

## Remaining boundary

This is informed development evidence using the user-selected source pair.
It provides neither blind-discovery credit nor a refutation of the paper.
The choice of coordinate prefix bound is explicit; we do not attribute this
exact definition to the paper. Other norms, real-versus-complex scalar
interpretation, quotient-torus presentation, exact-order rather than prefix
conventions, and equation/uniqueness claims are outside this checked adapter.

The norm conversion cannot account for the extra derivative order in the
selected route. The next product gap is a generic native Real prose producer
and a checked transport/frontier consumer: it must retain norm/order-dependent
constants, source-interpretation qualification, exact bridge premises and
conditional authority. The current native profile does not consume this Lean
adapter automatically. Existing Real pair/prefix/chain tools are not an
AND/OR propagation frontier. No Real record has been relabeled as Nat.
Task 2.1 and the evaluation gates remain open; this packet is a concrete input
to that design, not authorization to bypass the runtime scope freeze.
