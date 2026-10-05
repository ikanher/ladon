# Result inspection: fixed-epoch exposition, r45

`ladon result inspect` now exposes component coverage, attributed differences,
exact target resolution and stored checking evidence. This qualifies the first
inspection slice; the formalization-dossier child remains incomplete.

The installed CLI traversed 30 pages across eight sections using the immutable
r44 capture. It resolved all 25 targets and preserved 25 accepted stored
`exact-candidate-elaboration` observations. The 26 model-attributed component
assessments remain distinct: 15 source correspondence, nine conventional-only,
and two reported implications without checked adapters. There are no human
reviews. These counts do not establish whole-paper proof coverage.

The pointwise strict/closed endpoint difference and transcript/average-only
scope differences remain beside their components. Assumption extraction and
lineage ingestion explicitly report unavailable evidence and unknown totals.
Their integration is the next implementation task.

Verification passed: clean quality gate **2,786 tests**, **117 result tests on
each installed Python 3.11 and 3.12 runtime**, packaged schema checks and the
ordinary CLI outside the source checkout. Independent model review is recorded
in engineering-board posts 180 and 183; post 188 reviews the task credits. The original TeX and r44 evidence were
not modified; the new companion is a format conversion preserving the supplied
model author, basis, scope and differences.

Peak offline inspection RSS was **162.2 MiB**.
Pages took **6.92–7.58 seconds**
and the complete traversal took **215.2 seconds**.
The largest page was **32,450 bytes**. This measures
inspection only; it is not a comparison with Lean capture memory or runtime.
The existing 32 GiB Lean execution defaults remain unchanged.

The field use exposed two fixed usability defects: author labels containing
spaces were rejected, and some clipped nested collections pointed to the wrong
source input. Frozen regressions now cover both. Repeated full artifact
validation on every continuation page remains a performance concern. No
held-out benefit metric or human-understanding claim follows from this run.

Run the same offline traversal with an installed Ladon and the r44 directory:

```bash
python reproduce.py /path/to/ladon /path/to/new-output /path/to/target-capture-r44
```

`field/` retains commands, page outputs, converted assessments, timing and RSS
measurements. `identity.json` and `source-inventory.json` name the qualified
candidate; `../../acceptance-r45.json` records the scope and remaining tasks.
`engineering-board.jsonl` retains implementation and review evidence. The full
child exit, guides and bundles are uncredited.

Qualification also retained two harness failures: an elan shim downloaded
Lean under the clean environment and exhausted scratch quota; then a temporary
directory nested in an ignored Git tree invalidated one source-identity test.
The successful gate used the existing pinned compiler and a standalone scratch
directory outside any repository. No test assertions were removed to pass.

The default installed runtime also matches all 325 packaged files and reproduces
the qualified component page outside the checkout. Final OpenSpec validation
passed all 54 items; hygiene and backlog checks report zero findings. The
dossier has 6/9 tasks complete and the parent umbrella has 13/50.
