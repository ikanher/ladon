# Run and adjudication protocol

## Roles and custody

- **Custodian:** root agent. Holds `units.json`, the random arm-label key, and
  all run outputs. It has seen broad project context and the selected
  source-to-declaration mapping, but has not been given a correctness answer
  for these six claims. The custodian must not steer either arm or edit its
  report.
- **Ordinary arm and Ladon arm:** separate fresh model contexts using the same
  registered model/settings. They receive byte-identical source capsules and
  recipe; they do not receive the selected-unit manifest, other arm's files,
  or prior audit materials. Each must acknowledge the no-cross-role/no-answer
  instruction before doing analysis.
- **Adjudicators:** two fresh, independent contexts that did not select the
  units and did not participate in either audit. They receive anonymized
  allegations and evidence only after both first reports are frozen. They
  independently apply `RUBRIC.md`; neither sees the arm-label key before both
  ratings are signed and hashed.

The agent environment has no per-agent filesystem sandbox. The separation above
is therefore procedural, not OS-enforced. This limitation is part of the
validity record. If an arm reads outside its assigned input or sees registered
answers, mark the comparison contaminated and do not apply the primary gate.

## Registration and execution

1. Freeze `RUN-REGISTRATION.json`, arm prompts, capsule manifest, recipe,
   rubric, and this protocol; record SHA-256 hashes before launching either
   arm. The six selected identities remain custodian-only until adjudication.
2. Randomly assign Ordinary/Ladon to anonymized labels A/B and randomize which
   context is launched first. The custodian stores the mapping in the private
   run record. Launch both with the same model, reasoning setting, source
   capsule contents, wall-time ceiling and Lean/Lake invocation ceiling.
3. The arm must acknowledge its assigned role, then conduct the audit without
   seeing the other arm. Preserve the exact prompt, output, timestamps,
   command transcripts available from the runtime, and all generated evidence.
   Freeze each `FIRST-REPORT.md` before any comparison or adjudication.
4. Verify prompt and capsule hashes, source/toolchain identity, report freeze
   times, invocation counts and any contamination/resource events. Mark
   unavailable runtime telemetry as unavailable. Do not replace failed runs or
   extend a budget after seeing an outcome.
5. Strip arm identifiers and Ladon-specific wording from the report copies
   where practical, assign randomized labels, and give the same evidence
   format to both adjudicators. Freeze both signed ratings before unblinding.
6. Map each judgment to the six score units, unblind, compute the primary gate,
   and report out-of-population findings separately. Preserve negative,
   incomplete and unresolved outcomes.

## Primary gate

Apply the gate registered in `RUN-REGISTRATION.json` only after both first
reports, integrity verification, and both blind adjudications are frozen. The
gate is met only if Ladon has at least one additional independently upheld,
reader-useful finding among the six units versus Ordinary and has no new
serious false accusation. No post-hoc unit replacement, category change, or
threshold change is allowed.
