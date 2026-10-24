# Checking an abstraction refinement

`ladon investigation contract refine` checks an exact rational counterexample,
attempts a fresh Lean lift for a selected formal interpretation, and records
source-cited constraints and proposed repairs as separate immutable branches.
The current lift profile maps one rational variable to a natural number. It
does not handle general functions or analytic constraints.

Run the constructed example from this checkout, using a new output directory:

```bash
PYTHONPATH=src python scripts/check_refinement_cli.py --output /tmp/ladon-refinement-example
```

The script uses the ordinary `investigation init`, `observe`, `contract refine`,
`contract inspect`, and `report` commands. It saves every command, exit code,
output and elapsed time. Its subprocesses share a 30-minute deadline and stop
on failure. The native lift has a 120-second per-attempt cap and the standard
12 GiB RSS cap. It does not automatically retry a resource stop.

The example's selected formal predicate is `n < 2 → n = 0` for a natural number
`n`. Its rational abstraction admits `x = -1`: the premise holds and the
conclusion fails. A supplied Lean proof establishes both the full formal
mapping and the impossibility of realizing this particular rational value as
a natural number. The fresh result is `spurious-countermodel`.

The source-cited branch adds the caller's encoding `x ≥ 0`, citing the source's
natural-number domain. A separate repair branch proposes `x = 0`. Both exclude
the old witness. The report retains the original counterexample, the fresh
lift's saved evidence, and both revised checks. Excluding this witness does not
prove the claim: `x = 1` still refutes the source-cited rational branch. A checked
formal mapping also does not prove that the selected formal statement faithfully
represents the prose; source formula fidelity remains unverified.

## Input and output

The example writes a complete `request.json`. Its closed schema is
`ladon-proof-contract-refinement-request-v1`, with these fields:

| Field | Meaning |
| --- | --- |
| `originalFinding` | Immutable `{id, status, discrepancy, witness}`; status is `abstract-countermodel`. |
| `baseGoal` | The bounded rational AST, including every premise. |
| `lift` | `{interpretation, mode, term}` for the existing `nat-cast-v1` planner and fresh checker. |
| `refinementConstraints` | Source-cited predicates with exact path, hash, lines and quotation. |
| `repairConstraints` | Predicates labeled `proposed-repair`, with a rationale. |

The witness is `{id, status: "abstract-countermodel", assignment}`. At least
one constraint list must be nonempty. A branch can contain at most 64 predicates.
The request is bounded to 1 MiB. The workflow checks one supplied assignment;
it does not enumerate a new family or claim universal validity.

```bash
PYTHONPATH=src python -m ladon.entrypoint investigation contract refine \
  --input request.json --root SOURCE_ROOT --output refinement.json
PYTHONPATH=src python -m ladon.entrypoint investigation contract inspect \
  --input refinement.json --root SOURCE_ROOT --output inspection.json
PYTHONPATH=src python -m ladon.entrypoint investigation report \
  --plan observed.json --root SOURCE_ROOT \
  --refinement refinement.json --output report.json
```

Output files must be new. `refine` accepts `--timeout-seconds`, an optional
absolute `--deadline-monotonic` for the same machine/boot, and `--max-rss-mib`.
The earlier deadline wins; the lift retains its stricter per-attempt resource
caps. Incomplete or unsupported work returns exit code 2 and preserves the
original finding. A retry requires an explicit new invocation and output.

## Saved evidence and report association

`contract inspect` recomputes the rational checks and verifies the current source
hashes and citations. It returns `validated-historical`, `leanReplayed: false`
and `liftAuthority: "unverified-saved-result"`. It preserves the saved Lean
result without authenticating who produced it or replaying its proof. Integrity
digests detect inconsistent edits; they are not signatures. Run `refine` again
to obtain a fresh check from the original request.

`report --refinement` accepts up to four supplements. Each original finding ID
must match an existing report finding ID; for an observation, use its
`observationId`, not the author's short label. This is an attributed association
by ID, not a check that the supplied rational discrepancy translates that
observation. The report preserves both records and says so explicitly.

Reports with supplements use `ladon-investigation-report-v3`. Their
`refinementEvidence` contains historical inspection records; corresponding
findings carry `refinementIds`. Supplements do not change the plans, review
responses, pending work, original clock, or finalization receipts. Source
fidelity and mathematical falsity remain separate review obligations.
