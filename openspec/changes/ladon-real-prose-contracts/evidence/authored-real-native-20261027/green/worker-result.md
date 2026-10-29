worker_result:
  role: implementer
  status: implemented
  exact_claim: >
    Proposed an isolated bounded history codec implementing the frozen encode/decode
    shape. It canonically serializes JSON objects to ASCII, partitions fixed-size
    chunks, checks digest/length/shape/partition and duplicate keys, rejects
    nonfinite values and excessive JSON depth, and preflights the actual outer
    envelope with the unchanged MAX_ARTIFACT_BYTES limit.
  artifacts: .codex/state/real-prose-native/green/real_prose_native_codec.py; board posts 1932-1933
  commands: >
    Read-only inspection of frozen test and existing canonical/depth helpers;
    authored the isolated scratch module. No tests, build, Lean, or shared product
    commands run by assignment.
  baseline: >
    Board contract post 1921 and codec implementation assignment post 1929;
    shared worktree contains frozen tests/test_real_prose_native_codec.py.
  dependencies: none
  assigned_files_edited: .codex/state/real-prose-native/green/real_prose_native_codec.py; .codex/state/real-prose-native/green/worker-result.md
  frozen_tests_unchanged: true
  remaining_gate: >
    Root must integrate deliberately and run the frozen codec tests, including
    actual artifact-size behavior, before accepting the route.
  trust_notes: >
    The digest proves transport integrity only; callers remain responsible for
    source freshness and history authority. Codec output is not producer or
    semantic proof authority.
