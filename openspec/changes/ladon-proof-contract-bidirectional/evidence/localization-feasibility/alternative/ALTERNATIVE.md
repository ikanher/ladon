# Source-bound alternative feasibility

This scratch check used the original formal snapshot and prose snapshot unchanged:

- Formal snapshot: `sha256:8b24a92672b0cc584a13e36eb441d91f2551eb31861aae86349da4f6d629b73b`
- Prose snapshot: `sha256:b13d33da77fbb913192bc0d0c3d53d2a7851b86ebd85e912e43a57ecebf8393e`
- Formal observation declaration range: start line 28, column 0 (`threeStep`).
- Copied source consists exactly of original source bytes preceding that range, SHA256 `b9ed6b4bf37702e37853bdcb11128981650ca5b3de934fc0174459499a1a5fb3`, followed by `end ObligationsRed`. The generated scratch files are under `alternative/repo/`; no original/canonical source was edited.

`BridgeSufficiency.lean` proves the endpoint from an explicit middle-bound hypothesis, composing the last and first bounds. It compiles with the original pinned Lean toolchain. This demonstrates sufficiency only; it does not reverse an implication from the endpoint.

`GeneratedMiddle.lean` declares a generated local middle goal after the prefix. `SourceGoalCaptureRequest` captured it with only `s` and `y` as user assumptions. Lean also reports the synthetic `generatedMiddleGoal` target entry in its local-context array; it is implementation-detail metadata, not an assumption. `complete_source_goal` accepted `by simpa using ObligationsRed.middleBound s y`: replay accepted and trust accepted. The nearby `by sorry` candidate was trust-rejected (while replay classified it as accepted), so it was not marked completed/trusted.

Separately, `DirectEndpoint.lean` captured the generated endpoint goal with only `s` and `x` as user assumptions. A direct `simp` proof completed with accepted replay and trust. This alternative is in a separate generated source/module and is not imported into the middle-goal context.

Machine-readable capture, source digests, full completion/replay/trust receipts, and local contexts are in `completion-evidence.json`. Re-run from the repository root with:

```sh
PYTHONPATH=src .venv/bin/python .codex/state/proof-contract-analysis/obligations-red/run_alternative.py
```
