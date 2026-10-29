# Typed prose bound recognition

`investigation contract recognize-prose-bound` observes an attributed proposition
and recognizes a restricted estimate skeleton. It does not prove the estimate,
admit its bound predicate, or certify the interpretation of the prose.

Use the current checkout with
`PYTHONPATH=src .venv/bin/python -m ladon.entrypoint` in place of `ladon`:

```bash
ladon investigation contract recognize-prose-bound \
  --interpretation reading.json --context context.json --root /path/to/project \
  --timeout-seconds 600 --max-rss-mib 12288 --output recognized.json
ladon investigation contract inspect --input recognized.json --root /path/to/project
```

The reading and context use the [observation request formats](REAL_PROSE_OBSERVATION.md).
Output paths cannot already exist. The new profile is
`real-bound-prose-shape-v2`; existing extracted Real and Nat formats keep their
meanings. No native semantic contract is emitted.

The supported skeleton has one existential Real coefficient, its explicit
nonnegative guard, universal inputs and guards, and a bound implication. Both
`J f (n+d) C -> J (A f) n (K*C)` and the form with an explicit set argument are
supported. Exactly one complete decomposition must match. Global scope stays
global; a set-indexed reading retains its actual Set-typed binder. The complete
typed telescope, every guard, fixed predicate/operator parameters, coefficient
permission scope and expression origins remain in the result.

Only the selected input order and output coefficient are normalized. A literal
loss and canonical product require fresh synchronous Lean kernel checks of
exact equalities in the selected context. Each equality retains the original
expression and closes over every preceding source binder, including unused
proofs and local instances. Multiplication retains its observed instance. No
whole-statement unfolding or theorem-name/loss whitelist is used.

Head unfolding is bounded at 32 steps, source scopes at 64 binders, and losses
at nonnegative integers no larger than 2^53−1. Symbolic offsets, wrong products,
unsupported shapes and exhausted normalization leave explicit residuals; an
unknown loss is never reported as zero. Expression rendering retains the
observation limits of 100,000 nodes and depth 128.

`recognized` exits 0 and means the skeleton and both arithmetic checks passed.
`unresolved` or `unavailable` exits 2. All outcomes retain `authority: syntax-only`,
`fidelity: attributed-unreviewed`, `admission: unresolved` and `contract: null`.
Observation, alias checks and custody checks share one supervised process tree,
one deadline (at most 600 seconds), the configured RSS limit (default 12 GiB),
and an 8 MiB worker-output ceiling. Resource stops do not trigger retries or
larger limits.

Inspection validates saved structure and, with `--root`, current source,
implementation, toolchain and compiled context identities. It returns
`authority: none`, `freshCheck: false` and
`evidenceAuthentication: not-established`. Saved receipts are unauthenticated
history. Run recognition again from the original inputs for fresh checks;
inspection does not replay Lean. [Authored native records](REAL_PROSE_NATIVE.md) retain this syntax history
through persistence. Predicate-law admission and checked formal connections
remain separate stages.
