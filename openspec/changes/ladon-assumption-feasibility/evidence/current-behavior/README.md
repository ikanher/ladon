# Current mathematical behavior

The existing domain obligation does not check joint satisfiability of the
hypotheses. Native extraction and correspondence preparation produced the same
domain goal for both cases:

| Case | Assumptions | Conditional theorem | Context |
| --- | --- | --- | --- |
| impossible | `n : Nat`, `n = 0`, `n = 1` | `n = 37` | Inconsistent |
| inhabited | `n : Nat`, `n = 0` | `n + 1 = 1` | Has witness `n = 0` |

Both conditional theorems compile correctly. Neither is, by itself, an
exposition error. The generated domain goal, in both cases, is:

```lean
∀ (n : Nat), ∃ witness : Nat, witness = n
```

That goal is true independently of the hypotheses. This matches the existing
domain-admissibility implementation's documented scope; the missing capability
is a separate feasibility obligation, rather than a correction to conditional
proof checking. The useful additional questions are whether Lean can prove
`∃ n : Nat, n = 0 ∧ n = 1` or its negation, and analogously for the inhabited
control, with no tested hypotheses available as ambient assumptions.

`observed.json` preserves the two actual native slices, process receipts,
original typed contexts and generated obligations. `summary.json` binds that
observation and the relevant implementation files by digest. The extraction and
planning took about 7.6 seconds per case. All generated obligations retain their
original **open** status: this experiment does not claim that correspondence
completion or an operational detector ran.

To reproduce from the Ladon checkout, choose a new output path:

```bash
PYTHONPATH=src .venv/bin/python openspec/changes/ladon-assumption-feasibility/evidence/current-behavior/observe.py --output /tmp/feasibility-observed.json
```

The adjacent Lean project pins Lean 4.32.1. This is a two-case diagnostic
measurement, not the frozen 24-case operational baseline or an improvement score.
An initial scratch attempt used an unsupported interpretation formula tag;
the retained successful observation uses the supported typed `Nat.add`
application. No production runtime or frozen corpus was changed.
