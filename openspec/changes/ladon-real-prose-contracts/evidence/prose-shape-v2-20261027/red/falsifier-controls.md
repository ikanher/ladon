# Task1.3 falsifier controls

Scope: source review of `CONTRACT.md`, `src/ladon/real_bound_shape.py`, and `src/ladon/_real_bound_terms.py`; no product/test edits or Lean/build execution.

## Critical arity ambiguity

`application(expr, n, ...)` takes the final `n` arguments and returns the remaining prefix as the predicate. Thus trying arity 3 and then 4 on a predicate with a fixed parameter can shift the role boundary: a fixed predicate parameter may be reinterpreted as `function`, `set`, or `order`, and then disappear from the reconstructed residual predicate. The current v1 helper hardcodes four trailing arguments (`function,set,order,bound`) and does not implement global form.

Treat each proposed decomposition as a complete typed candidate, preserving the exact predicate prefix and every fixed argument. Require exactly one candidate that satisfies all role type/direct-binder conditions, input/output matching, guard checks, and typed application well-formedness. If both arities yield valid candidates, return an ambiguity residual; do not prefer the first match. If convenient, use elaborated argument types/expected function domains as a role proof, but never infer arity from name or an apparent number of explicit arguments alone. Global candidate roles are `(f,n,C)`; set candidate roles are `(f,S,n,C)`. In both, compare the untouched fixed predicate portion exactly across input and output.

## Scope and guards

- Preserve a source telescope and origin path for every forall/exists binder, including binders not used as roles. Check role universality and types against that full telescope; do not let a later forall overwrite a prior `last_input` candidate without a unique supported input role.
- Collect the complete conjunction tree (including nested `And`) and retain every clause/path. Require one clause that is exactly the coefficient nonnegativity guard for the selected K. Do not treat a found guard as license to discard sibling clauses or quantifier scope.
- For the input bound C, prove the selected guard is explicitly `0 ≤ C` with C in scope. If multiple candidate nonnegativity clauses or candidate C binders fit, reject as ambiguous instead of selecting the first (`_guards` currently returns `matches[0]`). Distinguish K's permitted dependencies (only preceding universals) from C and other role binders.
- Never commute/reorder binders, float guards across quantifiers, or infer missing guards. A guard under the wrong binder scope is a different proposition.

## Predicate and normalization controls

- Exact input/output predicate and set equality is necessary but not sufficient if role slicing has dropped an argument. Preserve the full application and explicitly mark only the selected mutable slots (function/order/bound; plus set slot for indexed form).
- Normalize only selected input-order and output-product expressions. Save both original and canonical typed refs. A syntactic rewrite, same pretty-print, or meta-level definitional equality is not enough: require a source-context kernel-checked equality certificate, closed over the exact observed binders. Any failed proof, changed K scope, symbolic shift, or unknown head stays residual.
- Treat shape recognition as syntax only. A successful typed decomposition says nothing about predicate meaning, operator laws, or Real-bound validity and must not enter native admission/contract state.

## Minimal fixture proposals for root-owned tests

1. Positive global `(f,n,C)` and indexed `(f,S,n,C)` sources with complete binders/guards; assert the mode, exact roles, origins, preserved predicate application, and unresolved admission.
2. A single fixed parameter before each apparent role slice so try-3/try-4 creates competing interpretations; assert ambiguity/residual and that no parameter disappears. Add a case where one arity appears syntactically plausible but fails the role type constraints, to show selection is based on typed roles.
3. Wrong or changed set/fixed parameter on output; different predicate head; altered function; wrong product coefficient/order; assert rejection with no alias normalization masking the change.
4. Nested conjunction with both required and unrelated guard, guard under wrong quantifier, missing guard, two nonnegative candidate binders, and K occurring after a universal; assert paths/scope retained and no first-match behavior.
5. Input order alias (`n + literal`) and output product alias: assert original plus kernel-certified canonical refs. Symbolic offset, out-of-range literal, unprovable alias, or wrong-context proof must stay residual.
6. Extra unused binders and shadowed/local binders: assert all telescope entries/origins survive and de Bruijn refs do not capture a nested lambda.

These are controls over typed shape, not positive mathematical admission tests.
