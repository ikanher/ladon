"""Read compiled imports; observe a frozen source only in a disposable project."""
import json
import os
import shutil
import tempfile
from pathlib import Path

from ladon.lean_toolchain import resolve_toolchain_context
from ladon.source_goal_capture import SourceGoalCaptureRequest, capture_source_goal
from ladon.source_goal_completion import SourceGoalCompletionRequest, complete_source_goal
from ladon.semantic_candidate_batch_worker import check_semantic_candidates
from ladon.semantic_candidate_worker import SemanticCandidateRequest

ROOT = Path(__file__).resolve().parents[5]
PROJECT = ROOT.parent / "lean/matrix-factorization"
LEAN = Path("/home/codex/.elan/toolchains/leanprover--lean4---v4.33.0/bin/lean")
SOURCE = Path(__file__).with_name('field-source.lean')
OUT = Path(os.environ.get('LADON_FIELD_EVIDENCE_DIR', str(Path(__file__).parent)))
OUT.mkdir(parents=True, exist_ok=True)

with tempfile.TemporaryDirectory(prefix="ladon-field-replay-") as directory:
    root = Path(directory)
    for name in ("lean-toolchain", "lake-manifest.json", "lakefile.lean"):
        if (PROJECT / name).is_file():
            shutil.copyfile(PROJECT / name, root / name)
    (root / ".lake").symlink_to(PROJECT / ".lake", target_is_directory=True)
    shutil.copyfile(SOURCE, root / "EnergyPotential.lean")
    context = resolve_toolchain_context(root, lean_path=LEAN, lake_path=LEAN.with_name("lake"), selection_mode="explicit")
    batch = check_semantic_candidates(SemanticCandidateRequest(
        repo_root=root, module="Mf.Optimization.FiniteMemoryAdam.CumulativePairing",
        goal="β ^ t ≤ β ^ s", candidate="le_trans", toolchain=context,
        local_context=({'name': 'β', 'type': 'ℝ'}, {'name': 'h0', 'type': '0 ≤ β'},
                       {'name': 'h1', 'type': 'β ≤ 1'}, {'name': 's', 'type': 'ℕ'},
                       {'name': 't', 'type': 'ℕ'}, {'name': 'hst', 'type': 's ≤ t'}),
        timeout_seconds=120, max_output_bytes=64 * 1024**2,
    ), ['le_trans', 'pow_le_pow_of_le_one'])
    (OUT / 'field-batch.json').write_text(json.dumps(batch.to_dict(), sort_keys=True) + '\n')
    print('batch', batch.status, [(row['candidate'], row['status']) for row in batch.rows], flush=True)
    assert batch.status == 'available', batch.diagnostic
    assert [(row['candidate'], row['status']) for row in batch.rows] == [
        ('le_trans', 'applicable-with-residuals'), ('pow_le_pow_of_le_one', 'accepted'),
    ]
    for label, line, column in (("late", 236, 6), ("early", 14, 2)):
        result = capture_source_goal(SourceGoalCaptureRequest(
            repo_root=root, source_path="EnergyPotential.lean", module="EnergyPotential",
            line=line, column=column, toolchain=context, timeout_seconds=120,
            max_output_bytes=64 * 1024**2,
        ))
        (OUT / f"field-{label}-capture.json").write_text(json.dumps(result, sort_keys=True) + "\n")
        print(label, result["status"], result["resourceAccounting"], flush=True)
        assert result['status'] == 'captured', result['diagnostic']
        if label == "early" and result["status"] == "captured":
            completion = complete_source_goal(SourceGoalCompletionRequest(
                repo_root=root, capture=result["capture"], toolchain=context,
                term="by unfold potential; exact add_pos_of_nonneg_of_pos (secondHistory_nonneg hβ₂.1 hβ₂.2 y t) (sq_pos_of_pos hε)",
                timeout_seconds=120, max_output_bytes=64 * 1024**2,
            ))
            (OUT / "field-early-completion.json").write_text(json.dumps(completion, sort_keys=True) + "\n")
            print("completion", completion["status"], completion["resourceAccounting"], flush=True)
            assert completion['status'] == 'completed', completion['diagnostic']
            assert completion['replay']['status'] == 'accepted'
            assert completion['trust']['accepted'] is True
