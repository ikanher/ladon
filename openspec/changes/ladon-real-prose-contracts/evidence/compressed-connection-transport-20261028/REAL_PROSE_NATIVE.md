# Attributed native Real readings

The authored profile `real-bound-prose-v1` records a recognized Real estimate
with its exact attributed interpretation, source map and complete typed
observation. Its admission remains unresolved and its prose fidelity remains
unreviewed. A native record is a persistent attributed reading, not a theorem.

Use the current checkout via
`PYTHONPATH=src .venv/bin/python -m ladon.entrypoint` in place of `ladon`:

```bash
ladon investigation contract produce-real-prose-bound \
  --root /path/to/project --interpretation reading.json --context context.json \
  --alternative-id reading:a --author reviewer \
  --timeout-seconds 600 --max-rss-mib 12288 --output authored.json
ladon investigation contract inspect --input authored.json --root /path/to/project
ladon investigation contract report-real-prose-bound --input authored.json
ladon investigation contract replay-real-prose-bound \
  --input authored.json --root /path/to/project --output replayed.json
```

The reading/context formats and recognition limits are described in
[proposition observation](REAL_PROSE_OBSERVATION.md) and
[bound recognition](REAL_PROSE_RECOGNITION.md). Fresh production accepts those
inputs and an explicit alternative identity/author. It repeats recognition;
callers cannot submit admitted features. Missing guards, unsupported shapes or
unresolved arithmetic checks produce no native contract. Successful authoring
exits 0; unresolved, unavailable, invalid or resource-stopped operations exit 2.
Existing output files are never overwritten.

The native batch contains the exact source-map and interpretation envelopes
already retained by observation, followed by a separately versioned
`proofir.contract`. Record features retain global or explicit set scope, the
complete telescope, all guards, original-expression fingerprints, expression
origins and coefficient permission scope. The native payload retains the full
recognition history in bounded, canonical JSON text chunks. This preserves
deep expressions and finite timing values within the existing native nesting,
string, scalar and artifact limits. Validation decodes that history and
reconstructs the record and exact external owners; a hash alone does not
establish validity, freshness or authenticated authorship.

Alternative identities and author labels are attributed data. A consistently
rebuilt alternative is another authored identity. No signature or independent
authorship/fidelity review is implied. The complete proposition, observation
and source context remain accessible through the retained history.

Production and replay share one supervised deadline and RSS/output caps across
observation, alias checks, native construction and custody checks. Replay
validates the prior history and current input identities inside that supervised
operation. It does not automatically retry, enlarge its memory limit or repair
stale inputs. The default cap is 12 GiB; the operation deadline is at most
600 seconds.

Inspection and reporting are historical: `authority: none`, `freshCheck: false`,
`evidenceAuthentication: not-established`. With `--root`, inspection additionally
checks current source, runtime, toolchain and compiled-library identities; it
does not execute Lean. Saved native artifacts keep the same authority limits
when inspected through ProofIR or stored in its disposable SQLite projection.
No database schema migration is required. Existing Nat and extracted Real
formats keep their meanings; unsupported semantic consumers reject this
authored profile. Predicate admission and checked formal connections require
separate evidence and remain subsequent stages.

An internal exact-owner Lean constructor now supports the next connection stage.
It derives a single conditional target from the formal theorem type, ordered
premise definitions and authored proposition value, checking local module,
declaration kinds, exact ranges and full expressions. Actual expression binders
are preserved. Proof authority still requires original source-goal capture,
kernel completion and independent replay. The component itself grants no semantic admission. Its informed boundary regression is
recorded in the Real-prose change's `exact-goal-boundary-20261028` evidence.

Internal connection jobs carry complete histories using a bounded, lossless
JSON DAG. When canonical v1 bytes exceed the existing wire allowance, an
ASCII-only, separately versioned zlib envelope is used. The wire cap stays
8 MiB; decoded aggregates stay below 32 MiB, with finite depth, graph and string
bounds. Decompression is bounded before the DAG is parsed; canonicality,
expansion metrics and the expanded digest are then checked before tree
allocation. Decoded mutable owners remain independent, and JSON-looking history
strings stay opaque. The fallback does not validate native envelopes or grant
connection authority; those checks remain the responsibility of the consuming
pipeline. Inputs that still exceed the bounded envelope are rejected without
truncation or automatic limit increases.


The opt-in connection consumer is under development in Task 2.2. Its public
commands are:

```bash
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract connect-real-prose-bound \
  --formal formal.json --authored authored.json \
  --formal-root FORMAL_ROOT --prose-root PROSE_ROOT \
  --request connection.json --output connection-result.json
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract report-real-prose-connection \
  --input connection-result.json
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract replay-real-prose-connection \
  --input connection-result.json --formal formal.json --authored authored.json \
  --formal-root FORMAL_ROOT --prose-root PROSE_ROOT
```

The closed request has schema `ladon-real-prose-connection-request-v1`, a single
Lean proof `term`, and an ordered `premises` array of at most 16 distinct local
Prop-definition names. Initially, the authored context must exactly prefix-extend
the formal source; both pinned Lean executables must agree. Runtime checks bind
full original input digests, semantic owners, copied ranges and imported modules,
freshly replay formal admission and authored recognition, and check the exact
implication `formalType → premise₁ → … → authoredValue`. Replay requires both
original input records; a newer equivalent record is not silently substituted.
All stages share at most 600 seconds, 12 GiB process-tree RSS and 8 MiB wire/output;
the expanded aggregate job remains capped at 32 MiB.

New `ladon-real-prose-connection-v2` results require an independent target
commitment. A trusted MetaM function constructs the implication directly from
the source-owned declarations, bypassing source term elaborators. The commitment
must match the selected goal and witness type structurally, and the submitted
term is independently elaborated and synchronously kernel-checked against that
exact target with complete standard-axiom checks. Its source scope, executable
and compiled import inventory must match the original capture, with existing
stable disk-inventory checks around execution. Original completion and independent
replay are still required. This uses the existing Lean execution custody model;
it does not introduce an operating-system sandbox for source commands.

An actual v1 counterexample replaced the generated goal with `True`; v1 kernel
checks were therefore insufficient to establish the intended connection. Keep
those records as unqualified history. Inspection explicitly returns
`targetOwnerBinding: not-established-legacy` for v1. New v2 inspection reports a
recorded independent commitment, while retaining `authority: none`,
`freshCheck: false` and `evidenceAuthentication: not-established`. A conditional
connection never certifies the authored proposition, NL fidelity, the original
source theorem's proof, mathematical falsity or independent discovery. Task 2.2's
exact connection implementation is complete. The generic and informed
qualification matrices remain required for Task 3.1; this does not certify
whole-paper qualification or source-pair discovery.

`ladon-real-prose-connection-v3` is emitted when the worker response uses the
compressed aggregate envelope. It retains the exact ASCII stdout bytes in
bounded chunks of at most 256 KiB, so saved-history digest validation checks the
original wire bytes without recompressing with the local zlib version. Aggregate
chunk bytes are rejected before joining, empty chunks are invalid, and stopped
v3 results cannot carry completed stdout. v1/v2 snapshots retain their original
schemas and validation semantics.


Current development evaluation: the frozen public set case and seven-case generic
CLI matrix pass, and the target-substitution counterexample is rejected by v2.
The first informed five-order run remains historical and unavailable because its
v1 result exceeded the wire cap. On the compression revision, a fresh five-order
case completed as connected and the four-order control completed unresolved;
neither exceeded the unchanged process or output limits. A fresh v3 five-order
run also completed connected; its saved snapshot validates with the compressor
disabled. Exact outcomes and limits are in
`evidence/compressed-connection-transport-20261028/REPORT.md`.
An aggregate transport failure remains an operational stop, not a mathematical
rejection or permission to raise limits or publish partial evidence.
