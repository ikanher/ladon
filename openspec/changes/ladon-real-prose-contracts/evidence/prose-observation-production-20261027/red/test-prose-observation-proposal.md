# Public typed prose observation test proposal (red sidecar)

Root owns the final frozen test file and integration details. These cases target only `observe_prose_bound(root, interpretation, context, *, timeout_seconds, max_rss_bytes, max_output_bytes)` and the public `observe-prose-bound` command. They deliberately avoid asserting an internal request/check representation beyond the documented nested typed result.

## Common fixture

Prepare a temporary Lean root with only `import Lean`, pinned toolchain, and a source-bound authored interpretation whose lowered proposition is the closed Nat proposition `0 = 0`. The context JSON is closed schema `ladon-prose-bound-context-v1`, with exactly `schema`, `file`, `module`, `scope`, and `scope: "file-end"`. The interpretation must be obtained through the existing native source-map/interpretation flow, not fabricated as a theorem. Separately use the checked-in `tests/fixtures/real_bound_observation` root for Real-specific typed syntax only; its fake `Real` must never be treated as mathematical evidence.

## Exact acceptance cases

1. `test_public_observer_elaborates_prop_value_without_proof_authority`
   Call the public function on the Nat fixture. Require `schema == "ladon-real-prose-observation-v1"`, `channel == "prose"`, `authority == "syntax-only"`, `fidelity == "attributed-unreviewed"`, `admission == "unresolved"`, and `contract is None`. Require `status == "observed"` and a nonempty actual typed observation at `result["check"]["result"]` (the `result` must represent an elaborated proposition value, not merely a declaration type). Assert no public output field claims theorem/proof/axiom/sorry or admitted contract authority. This proposition is a parsing fixture; it is not a claim under test.

2. `test_context_schema_is_closed_and_bad_scope_is_rejected`
   Add an unknown key, omit each required key, change `scope` to a value other than `file-end`, and set wrong JSON types. Each must fail as malformed input, with no successful observation/contract output.

3. `test_ill_typed_lowering_is_unavailable_not_admitted`
   Use an otherwise valid source-bound interpretation whose lowered formula applies a function to a Nat argument of the wrong type. Require an explicit non-observed/elaboration-failure outcome, `contract is None`, and unresolved admission. It must not turn into a successful placeholder proposition.

4. `test_context_and_source_mutation_invalidate_fresh_replay`
   Observe a valid fixture, then mutate the context source bytes and, separately, mutate the exact interpretation source span (preserving the old artifact). Fresh verification/replay must reject each as changed/stale. Do not rewrite the saved receipt to look current.

5. `test_receipt_tampering_and_rehashed_forgery_are_rejected`
   Change each public authority field (`admission`, `authority`, `fidelity`), the typed result, source/context owner, and implementation identity. Also recompute the outer identity with the production identity helper after each mutation. Fresh replay must reject both ordinary and rehashed modifications; closed schema validation must reject unknown fields.

6. `test_named_theorem_or_axiom_is_not_selected_as_the_observed_value`
   Against the existing Real fixture, request a theorem declaration or add an axiom and attempt to redirect the context/interpretation to it. The API must reject theorem selection/axiom-derived authority for this value-observation operation; it must not mark that target as a theorem proved by this operation. This is a negative behavior test only; never assert the target as theorem/axiom/sorry.

7. `test_bounded_worker_stop_has_no_dependent_success`
   Inject a deterministic worker stop/timeout and a deterministic RSS limit stop through the existing process-supervision seam. Require unavailable/resource-stopped result and exit 2; no typed success, contract, or downstream observation may be emitted. Check one absolute deadline is passed through descendants rather than reset per stage.

8. `test_cli_observe_collision_and_historical_inspection`
   Invoke `investigation contract observe-prose-bound --interpretation ... --root ... --context ... --output ...`. Successfully saved observation exits 2 because status is observed/unadmitted. Repeating to same output exits 2 and preserves bytes. Historical `inspect` without current root/context remains historical only (`validated-historical`, no fresh check); inspection with current root/context performs exact replay and rejects stale bytes. Neither mode grants proof/fidelity authority.

## Critical source-backed threats for implementation review

- The scratch proposition observer is explicitly not production: it lacks strict request validation, source/context custody, structured errors, finite expression rendering, and process/resource guarantees. Do not promote it unchanged.
- Read a generated definition's value as `Prop`; never use its inferred type `Prop` as the source proposition. Otherwise a trivial wrapper can appear to have observed the formula while losing it.
- Bind the complete lowered proposition to exact interpretation, source, context, module, generated declaration, implementation and toolchain identities. Compare/replay owners around execution to catch mid-run changes.
- Require the authored formula to elaborate as a `Prop`; reject theorem/declaration selection, axioms and fabricated extracted records in this API.
- Cap expression nodes/depth before rendering/JSON serialization, cap total output, and supervise planner plus Lean descendants under one deadline and RSS limit. Resource stop must cut off dependent work.
- Keep every result observation-only: saved or rehashed receipts cannot authenticate execution; `authority` stays syntax-only, `fidelity` unreviewed, `admission` unresolved, and `contract` null.
- Global versus set-indexed scope and alias semantics are future recognition/connection work. These observer tests must not infer either from a typed result or silently insert/discard binders.
- The checked-in `NamedBound.lean` fixture defines a fake `Real`; it is useful to prove type-directed parsing, never to admit Real laws or prove mathematical falsity.
