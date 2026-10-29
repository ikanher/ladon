# Route refinement challenge (post 1960)

I read peer findings 1958 and 1959. The red review already identifies the key
source-owner, premise, route-direction, history, and resource risks. The new
lossless DAG transport is a plausible bounded wire representation for the
measured pair, but its 5,056,694-byte result is only a feasibility datapoint;
it is not yet an accepted substitute for the frozen 8 MiB history limit.

## DAG transport boundary

- Keep three sizes distinct in the API/receipt: encoded worker stdin/stdout
  bytes (each at most 8 MiB), decoded expanded canonical-pair bytes (a
  separately named and justified bound), and peak process-tree RSS (12 GiB).
  The 32 MiB native-analysis/batch allowance does not automatically apply to
  this connection operation. If Task 2.2's “full retained history must fit the
  bound” means expanded history <= 8 MiB, a 32 MiB decoder does not satisfy it;
  root must either record this as an explicit unavailable outcome or obtain a
  contract decision before treating the in-memory cap as 32 MiB. Do not call
  the compact wire artifact an under-8-MiB full history.
- 9,191,277 raw pair bytes compress to a 5,056,694-byte encoded DAG only by
  retaining shared subtrees instead of duplicating them. That is lossless, but
  generic JSON parsing/expansion remains a denial-of-service surface. Before
  materialization, enforce a closed schema/version, strict duplicate-key and
  non-finite-number rejection, canonical wire re-encoding, maximum encoded
  bytes, node count, total edges, scalar/string bytes, unique object keys,
  and backwards-only integer references (`type(x) is int`, not bool; each
  child ref < current node index). Backward refs make cycles unrepresentable;
  still reject invalid roots, unexpected node fields/tags and repeated object
  keys. Validate depth, child multiplicities and exact expanded canonical JSON
  byte size by saturating dynamic programming before recursively allocating
  the tree; reject above the explicit expanded bound. A DAG can have only
  28k-ish nodes yet expand exponentially through repeated references.
- Validate each original owner artifact with its existing closed history
  validator before extracting/sharing it; validate reconstructed owners again
  after expansion and canonical re-encoding. In particular the nested authored
  recognition must decode and re-encode its native chunks exactly. Pair
  equality proves representation roundtrip, not source authenticity or semantic
  owner custody. Do not return a fully expanded pair through stdout: preserve
  the bounded wire/reference form through worker boundaries and have the final
  connection result refer to the independently validated owners. Bound every
  aggregate receipt/result separately; if a full retained connection history
  cannot fit its declared output bound, return unavailable rather than omit
  required fields.

## Common-context source owners

The formal source being a byte prefix of the selected authored context is a
good candidate filter and a useful copy-integrity check, but not sufficient
owner proof. The prototype macro's fully qualified formal lookup plus exact
structural type comparison addresses wrong-name and mismatched-type cases.
Before activation it also needs an exact authored value comparison against the
fresh observation's proposition Expr JSON; checking only `type = Prop` and
`inferType value = Prop` accepts any proposition definition. Require exact
fully qualified names, declaration kind, source module/range/copy-range, source
and context digests, and structural Expr equality for both the formal *type*
and authored *value*. A declaration with the expected type but imported from a
different module is still the wrong source owner. Recheck these in fresh
completion/replay, not just when generating the goal string.

Also compare the actual toolchain and compiled import inventory. Identical
source bytes compiled under different `.olean` closures can resolve names,
instances, notation and declarations differently. A common source suffix may
change namespace/open/scoped options or resolve an unqualified term differently.
The final capture must bind the source suffix's exact generated declaration
range and the final target, while the compiler replay must preserve that
closure. If exact range/module ownership cannot be extracted in the supported
Lean context, retain `source-context-unavailable`; metadata equality and
prefix length alone cannot promote it.

## Bridge premise semantics

The five-order probe is a useful positive conditional route only if the exact
term is checked under the common owner closure and all required input guards
remain in the target. Its `original` value is a formal theorem-type assumption;
successful completion proves a conditional implication, not the theorem body
or the paper claim. The coordinate-norm factor must remain a typed,
order-dependent expression wherever its scope requires it.

For each proposed bridge, record its exact goal, owner, direction, binders,
dependencies and checked term. Distinguish a bridge proved by a checked term
from an open conditional premise. A final theorem with an open premise can be
reported only as exactly that conditional theorem; do not label it an
unconditional connection. Prevent a vacuous “bridge” premise equal to the
authored conclusion (or otherwise just restating the desired implication) from
being presented as evidence. Existing `NoParameter`/norm lemmas help only when
their checked types instantiate the exact bridge; theorem names do not confer
that match. The selected four-order route should stay rejected/unresolved when
Lean cannot supply its five-order input. That is a route failure, not endpoint
falsity.

## Cheapest gate

Keep root's scratch macro/probe as feasibility, not product evidence. Before
freezing the codec/API, run the saved five-order and four-order controls through
one outer supervisor with the actual 8 MiB input/output boundaries; require
the five-order goal to bind both exact owner Exprs/ranges and full common
import inventory, and require the four-order selected application to retain
the observed mismatch. Add an adversarial synthetic transport check (forward
ref, cycle/self-ref, bool ref, duplicate key, NaN, huge scalar, deeply nested
node, high-fanout exponential expansion, wrong nested native chunk digest,
owner swap) that rejects before expansion or before semantic acceptance. No
production activation follows from transport roundtrip alone.

This is a review only. I ran no tests, Lean or builds and did not modify the
root's probe or production files.
