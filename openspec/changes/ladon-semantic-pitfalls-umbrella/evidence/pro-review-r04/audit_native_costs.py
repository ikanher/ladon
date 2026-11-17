"""Audit retained r04 native MF costs and outcomes without executing packet code.

This reads JSON/text, verifies retained hashes, and writes derived summaries only.
It does not execute Lean, load Ladon, replay checks, or access original donor paths.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


EVIDENCE_PATH = Path(
    'sources/openspec/changes/ladon-proofir-correspondence-context/'
    'evidence/mf-native-r01'
)
OLD_EVIDENCE_PATH = Path(
    'sources/openspec/changes/ladon-semantic-pitfalls-umbrella/evidence'
)


def read_json(path: Path):
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify_operation(command: list[str]) -> str:
    for operation in ('check', 'inspect', 'align', 'interpret', 'slice'):
        if operation in command:
            return operation
    return 'other'


def summarize(rows: list[dict]) -> dict:
    failed = [row for row in rows if row['returncode'] != 0]
    return {
        'operations': len(rows),
        'summed_top_level_command_wall_seconds_overlapping': sum(row['top_level_command_wall_seconds'] for row in rows),
        'failed_operations': len(failed),
        'failed_summed_top_level_command_wall_seconds_overlapping': sum(
            row['top_level_command_wall_seconds'] for row in failed
        ),
        'timeouts': sum(row['timed_out'] for row in rows),
        'memory_limit_events': sum(row['memory_limited'] for row in rows),
        'output_limit_events': sum(row['output_limited'] for row in rows),
    }


def process_rows(base: Path, packet: Path) -> list[dict]:
    rows = []
    for path in sorted(base.glob('*.process.json')):
        result = read_json(path)
        case = path.name.split('-')[0]
        operation = classify_operation(result['command'])
        if result['timed_out']:
            outcome = 'outer-timeout'
        elif result['returncode'] == 0:
            outcome = 'success'
        elif 'collection exceeds item limit' in result['stdout']:
            outcome = 'collection-limit-rejection'
        elif 'No such file or directory' in result['stdout']:
            outcome = 'missing-input'
        elif operation == 'slice':
            outcome = 'wrapper-slice-rejection'
        else:
            outcome = 'unsuccessful'
        rows.append({
            'receipt': str(path.relative_to(packet)),
            'sha256': sha256(path),
            'case': case,
            'operation': operation,
            'outcome': outcome,
            'returncode': result['returncode'],
            'top_level_command_wall_seconds': result['elapsed_seconds'],
            'peak_rss_bytes': result['peak_rss_bytes'],
            'peak_rss_gib': result['peak_rss_bytes'] / 2**30,
            'timed_out': result['timed_out'],
            'memory_limited': result['memory_limited'],
            'output_limited': result['output_limited'],
            'command': result['command'],
        })
    return rows


def inspect_case(base: Path, packet: Path, name: str) -> dict:
    bundle_path = base / name / 'checked-1800-r02.json'
    bundle = read_json(bundle_path)
    view = read_json(base / name / 'inspection.json')['native']
    expected_parent = (
        'refuted-correspondence' if name == 'fdp'
        else 'supported-for-attributed-interpretation'
    )
    assert bundle['parentSupport'] == expected_parent
    assert view['authority'] == 'stored-evidence-only'
    assert view['coverage']['complete'] is True
    assert view['checkEvidence']['unboundObligations'] == []
    checks = {row['obligation']: row for row in bundle['checks']}
    assert len(checks) == 4
    receipt_obligations = set()
    check_summaries = []
    for row in view['checkEvidence']['rows']:
        assert row['binding']['status'] == 'matched-stored-records'
        receipt = row['receipt']['value']
        checked = checks[receipt['obligation']]
        expected_goal = (
            checked['goal'] if checked['mode'] == 'prove'
            else '¬ (' + checked['goal'] + ')'
        )
        assert receipt['checkedGoal'] == expected_goal
        assert receipt['status'] == checked['status']
        assert receipt['mode'] == checked['mode']
        assert receipt['planId'] == bundle['planId']
        completion = checked['completion']
        assert completion['status'] == 'completed'
        assert completion['replay']['status'] == 'accepted'
        assert completion['trust']['accepted'] is True
        receipt_obligations.add(receipt['obligation'])
        check_summaries.append({
            'obligation': receipt['obligation'],
            'status': checked['status'],
            'mode': checked['mode'],
            'goal': checked['goal'],
            'checked_goal': receipt['checkedGoal'],
            'completion': completion['status'],
            'replay': completion['replay']['status'],
            'trust_accepted': completion['trust']['accepted'],
            'binding': row['binding']['status'],
        })
    assert receipt_obligations == set(checks)
    assert all(
        row['status'] == ('refuted' if name == 'fdp' and key == 'conclusion'
                          else 'supported')
        for key, row in checks.items()
    )
    accounting = bundle['executionAccounting']
    process = read_json(base / f'{name}-check-1800-r02.process.json')
    inspection_process = read_json(base / f'{name}-inspect-final.process.json')
    stored = read_json(base / 'RESULT.json')['cases'][name]
    compiled_count = len(bundle['plan']['slice']['compiledInventory']['modules'])
    assert stored['checks'] == {key: row['status'] for key, row in checks.items()}
    assert stored['executionAccounting'] == accounting
    assert stored['compiledModules'] == compiled_count
    assert accounting['processCount'] == len(accounting['processes'])
    structural_stage_seconds = sum(
        accounting['stages'][key]['wallSeconds']
        for key in ('obligation:interpretation', 'obligation:object-map')
    )
    return {
        'bundle': str(bundle_path.relative_to(packet)),
        'bundle_sha256': sha256(bundle_path),
        'bundle_bytes': bundle_path.stat().st_size,
        'parent_support': bundle['parentSupport'],
        'compiled_modules': compiled_count,
        'outer_check_seconds': process['elapsed_seconds'],
        'outer_peak_rss_bytes': process['peak_rss_bytes'],
        'outer_peak_rss_gib': process['peak_rss_bytes'] / 2**30,
        'inspection_seconds': inspection_process['elapsed_seconds'],
        'inspection_peak_rss_bytes': inspection_process['peak_rss_bytes'],
        'inspection_bytes': (base / name / 'inspection.json').stat().st_size,
        'native_check_count': accounting['checkCount'],
        'distinct_prose_subjects': accounting['distinctProseSubjects'],
        'recorded_substantive_check_count': accounting['substantiveCheckCount'],
        'recorded_typing_probe_count': accounting['typingProbeCount'],
        'internal_accounting_wall_seconds': accounting['wallSeconds'],
        'internal_accounting_peak_rss_bytes': accounting['peakRssBytes'],
        'recorded_process_count': accounting['processCount'],
        'typing_only_disjoint_obligation_stage_seconds': structural_stage_seconds,
        'typing_only_share_of_outer_check_wall': structural_stage_seconds / process['elapsed_seconds'],
        'typing_only_stage_scope': 'Sequential obligation:interpretation and obligation:object-map stages only; do not add nested capture/completion durations; not an estimated removable cost.',
        'sum_recorded_process_elapsed_seconds': sum(
            item['elapsedSeconds'] for item in accounting['processes']
        ),
        'reported_stage_overlap_warning': accounting['stageMeasurementScope'],
        'stages_not_to_be_summed': accounting['stages'],
        'checks': sorted(check_summaries, key=lambda item: item['obligation']),
    }


def verify_custody(base: Path, packet: Path) -> dict:
    manifest = read_json(base / 'MANIFEST.json')['files']
    for relative, expected in manifest.items():
        path = base / relative
        assert path.resolve().is_relative_to(base.resolve())
        assert sha256(path) == expected, relative
    primary_count = 0
    unavailable_compiled = []
    for name in ('INPUTS-r03.json', 'ADAM-INPUTS.json'):
        inputs = read_json(base / name)
        for relative, expected in inputs['primaryInputs'].items():
            assert sha256(base / relative) == expected, relative
            primary_count += 1
        # The donor paths are outside this packet. Do not read or pretend to verify them.
        unavailable_compiled.extend(inputs.get('directCompiledImports', {}).keys())
    prefixes = {
        'project/Fdp.lean': 'fdp-ordering-privacy-20261115T072023Z/Countermodel.lean',
        'adam-project/AdamCase.lean': 'dpadam-source-constructor-r01/Full.lean',
    }
    for actual, original in prefixes.items():
        assert (base / actual).read_bytes().startswith(
            (packet / OLD_EVIDENCE_PATH / original).read_bytes()
        ), actual
    return {
        'manifest_entries_verified': len(manifest),
        'primary_input_hash_checks': primary_count,
        'original_proof_prefixes_verified': list(prefixes),
        'direct_compiled_import_paths_not_reverified': sorted(set(unavailable_compiled)),
        'native_lean_replays_performed_by_this_audit': 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    packet = args.packet.resolve()
    base = packet / EVIDENCE_PATH
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    rows = process_rows(base, packet)
    final_cases = {case: inspect_case(base, packet, case) for case in ('fdp', 'adam')}
    result = {
        'scope': 'Independent retained-record audit; no fresh Lean execution',
        'custody': verify_custody(base, packet),
        'all_recorded_operations': summarize(rows),
        'by_operation': {
            operation: summarize([row for row in rows if row['operation'] == operation])
            for operation in sorted({row['operation'] for row in rows})
        },
        'by_case': {
            case: summarize([row for row in rows if row['case'] == case])
            for case in ('fdp', 'adam')
        },
        'outcomes': dict(Counter(row['outcome'] for row in rows)),
        'final_cases': final_cases,
        'final_check_summed_top_level_command_wall_seconds_overlapping': sum(
            case['outer_check_seconds'] for case in final_cases.values()
        ),
        'interpretation': [
            'Summed command-wall durations are neither project elapsed time nor CPU time.',
            'Final check runs were concurrent; their durations must not be presented as sequential elapsed time.',
            'No measured source-reading, wrapper-authoring, donor-cache preparation, total reviewer effort, or ongoing maintenance cost is available.',
            'Internal inclusive stage durations overlap and must not be summed.',
            'Eight checks concern two supplied source readings; interpretation goals are P -> P and object-map goals end True.',
            'The recorded substantiveCheckCount is a producer category, not a count of independent nontrivial mathematical discoveries.',
            'Hash verification demonstrates consistency of retained bytes, not independent semantic truth or authenticity.',
        ],
    }
    (output / 'native-cost-summary.json').write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + '\n'
    )
    (output / 'native-process-ledger.json').write_text(
        json.dumps(rows, indent=2, ensure_ascii=False) + '\n'
    )
    columns = [key for key in rows[0] if key != 'command']
    with (output / 'native-process-ledger.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({
        'all_operations': result['all_recorded_operations'],
        'checks': result['by_operation']['check'],
        'custody': result['custody'],
        'native_checks_verified_in_stored_records': sum(
            case['native_check_count'] for case in final_cases.values()
        ),
    }, indent=2))


if __name__ == '__main__':
    main()
