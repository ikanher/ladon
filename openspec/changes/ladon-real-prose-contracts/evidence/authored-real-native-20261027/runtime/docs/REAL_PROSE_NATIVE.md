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
