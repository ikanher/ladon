# Source-bound backward-obligation feasibility

Status: feasible as a narrow new constructor over the already recognized Nat estimate fragment; no production integration is present and no child requirement is closed by this scout.

## Safe route

1. Verify the current parent/reading snapshot and every provider snapshot with `verify_formal_snapshot`. Require their source SHA, module, pinned environment, helper/profile digests, and contract identities to agree with the selected request. Keep source fidelity `attributed-unreviewed`.
2. Consume the exact backward-transform request/result identities and selected branch together with those snapshots. The constructor must derive symbols, quantifiers, types, scopes, and selected offset from `normalizedTypeExpr` plus the validated recognizer output. Reject unknown telescope/dependency/domain cases. Do not consume display strings or natural-language formulas as targets.
3. Use the parent snapshot's declaration start byte range to copy the exact source prefix before the unfinished parent. Keep original provider definitions in that prefix, preserve the observed namespace, append a generated declaration from the structured contract, and close the namespace afterward. Do not import the source module's compiled OLean.
4. Put a guard in that same generated compilation requiring the reserved parent declaration absent and the source module absent from the import closure. Bind a generated-source digest and prefix digest to the parent/provider snapshot IDs and backward branch identity.
5. Call `capture_source_goal` on that exact generated file with its expected digest; independently compare the captured goal and local telescope against the structured branch. Call `complete_source_goal` only with the corresponding capture. Its fresh recapture, exact type elaboration, closure, replay, and axiom policy then check the proof in that same context.

`correspondence_check._check_goal` is a useful orchestration precedent for writing a generated source, capturing its goal and completing it. It does not supply the new bridge: its current goals are lowered from attributed correspondence inputs, and its full-source prelude does not bind backward request/result/snapshot identities. `prepare_source_context` compiles the original source as an import and must not be used for this unfinished-parent route.

## Isolated receipts

The source copy is the historical `ObligationsRed.lean`, SHA256 `f42e538e1a7135435c295ddb3ddade16487272f241e13a66241059c12ffb5079`. In the new scratch repo I freshly produced and verified both `threeStep_snapshot.json` and `middleBound_snapshot.json`; both source digests match that source. IDs: parent `sha256:f43ee593d5fc8f652ee74f2590f2f8a30c91c339fb76489636bc612f72f4d80e`, provider `sha256:103c7496f183396021e866ef484892474c153f4158d5e40c58a377b2a8d11048`.

The structured summary from the provider AST retained binders `s,y : Nat` in source order and symbols `N2`, `F2`, `N1`, `C`; with selected offset 1 it generated `N2 s (F2 y) ≤ C * N1 (s + 1) y`. The generated source preserved the raw source prefix through the parent's observed start range, kept the goal inside namespace `ObligationsRed`, and guarded `ObligationsRed.threeStep` absent. Capture returned `captured`, visible locals exactly `s,y`, and goal display exactly the selected formula. Completion using `by simpa [ObligationsRed.N1, ObligationsRed.N2, ObligationsRed.C] using ObligationsRed.middleBound s y` returned `completed`, replay `accepted`, trust `true`. The nearby term `by exact ObligationsRed.threeStep s y` returned `rejected` with `Unknown identifier`, replay not run.

A separate compiled-import probe compiled the full source module (which contains the parent), imported it into `ImportedAlias.lean`, and successfully declared `AliasHost.parentAlias := ObligationsRed.threeStep`. Thus an OLean import can reintroduce the excluded parent under another alias; guard and source-inventory checks must cover the imported module closure, and the original source module must not be imported. Exact-prefix positive probe returned 0; attempted reference to the omitted parent returned 1 with `lean.unknownIdentifier`. Each direct Lean probe used `run_bounded_target_process`, timeout 60s, output 8 MiB, RSS 12 GiB. The capture/completion API calls used the same request bounds; individual operation peak RSS was at most 3.75 GiB.

Commands:

```sh
PYTHONPATH=src python .codex/state/proof-contract-analysis/source-bridge-scout/run_probes.py
PYTHONPATH=src python .codex/state/proof-contract-analysis/source-bridge-scout/capture_complete_probe.py
```

Machine receipts are in `probe_receipts.json` and `capture_complete_receipt.json`. The former captures the direct Lean processes; the latter captures generated source, source/capture IDs, imported inventory, completion/replay/trust statuses, and resource accounting.

## Limits

The preserved historical localization report #187 remains unchanged and correctly labels its manually authored bridge as not produced by a backward planner. The new probe is also feasibility evidence, not a generic constructor or a proof that an arbitrary branch is source-correct. Its selected offset and supported Nat/global-constant expression fragment are narrow. Source attribution remains unreviewed, no natural-language correspondence was authenticated, and the generated sufficient condition proves neither a converse nor necessity. Snapshot/capture hashes bind bytes and observations but do not themselves certify source fidelity.
