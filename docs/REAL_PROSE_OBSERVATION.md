# Typed prose proposition observation

`investigation contract observe-prose-bound` elaborates an attributed interpretation
in a selected Lean source context and saves its exact proposition expression.
The operation can observe an unproved or false proposition: this checks its type,
not its truth. The result retains `authority: syntax-only`,
`fidelity: attributed-unreviewed`, `admission: unresolved` and `contract: null`.

Use the current checkout through `PYTHONPATH=src .venv/bin/python -m ladon.entrypoint`:

```bash
ladon investigation contract observe-prose-bound \
  --interpretation reading.json --context context.json --root /path/to/project \
  --timeout-seconds 600 --max-rss-mib 12288 --output observed.json
```

The existing interpretation format contains the attributed source span/digest,
structured formula and explicit symbol map. Its source path is relative to
`--root`; original text outside the project needs an explicit local source copy
with preserved content identity and attribution. The context request is closed:

```json
{
  "schema": "ladon-prose-bound-context-v1",
  "file": "Project/Context.lean",
  "module": "Project.Context",
  "scope": "file-end"
}
```

The context file is read and compiled with an appended generated definition of
type `Prop`. Its value is observed, and its generated declaration/range remains
distinct from the authored prose span. The command takes no theorem selector.
Closed propositions at file end are supported; open local goals need a separate
context adapter. Opaque readings remain unsupported; ill-typed readings return
an elaboration failure. Neither creates a placeholder or admitted contract.

Successful syntax observation exits 0. Unsupported, unavailable, malformed and
resource-stopped operations exit 2. Output paths are immutable: an existing file
is never overwritten. Source-map and interpretation artifacts are included;
there is no new native semantic contract in this operation.

```bash
ladon investigation contract inspect --input observed.json
ladon investigation contract inspect --input observed.json --root /path/to/project
ladon investigation contract replay-prose-bound \
  --input observed.json --root /path/to/project --output replayed.json
```

Inspection validates saved history with `authority: none` and `freshCheck: false`.
Supplying `--root` additionally checks current prose/context source, implementation,
toolchain and imported compiled-library identities. It does not execute the
proposition again or authenticate a saved execution receipt. Explicit replay
requires those inputs to remain current and performs a new bounded observation.

Preparation, import inventory, both Lean observations and result construction
run within one supervised process tree and a shared deadline. The first
observation supplies exact loaded-module paths; a second identical observation
is surrounded by compiled-module/sidecar inventory checks. The expression
renderer caps traversal at 100,000 nodes and depth 128 before JSON emission.
Requests and worker outputs are capped at 8 MiB. The default RSS cap is 12 GiB,
and the timeout cannot exceed this profile's 600 seconds. A memory stop returns
the shared stop-and-report diagnostic; the command does not retry automatically.

[Versioned bound-shape recognition](REAL_PROSE_RECOGNITION.md) is available as a
separate operation. Predicate-law admission, checked connection to formal
contracts and graph propagation remain subsequent stages. Observation alone
preserves their input while leaving their authority open.
