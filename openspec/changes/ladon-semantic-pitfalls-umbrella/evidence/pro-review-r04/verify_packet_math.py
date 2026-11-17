'''Inspect retained r04 mathematics and native records without running Lean.

This verifies finite arithmetic and selected stored-record consistency. It does
not authenticate records, rebuild imported dependencies, or certify prose.
'''

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from itertools import combinations, permutations, product
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[2]
PACKET = WORKSPACE / 'ladon-semantic-strategy-review-data-r04'
PREVIOUS = WORKSPACE / 'ladon-semantic-strategy-review-data-r03'
NATIVE_RELATIVE = Path('sources/openspec/changes/ladon-proofir-correspondence-context/evidence/mf-native-r01')
OLD_RELATIVE = Path('sources/openspec/changes/ladon-semantic-pitfalls-umbrella/evidence')
NATIVE = PACKET / NATIVE_RELATIVE


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prefix_checks() -> list[dict]:
    pairs = [
        ('project/Fdp.lean', 'fdp-ordering-privacy-20261115T072023Z/Countermodel.lean'),
        ('adam-project/AdamCase.lean', 'dpadam-source-constructor-r01/Full.lean'),
    ]
    result = []
    for wrapper, original in pairs:
        old = (PACKET / OLD_RELATIVE / original).read_bytes()
        new = (NATIVE / wrapper).read_bytes()
        prefix_matches = new.startswith(old)
        assert prefix_matches
        previous_path = PREVIOUS / OLD_RELATIVE / original
        unchanged = previous_path.read_bytes() == old if previous_path.exists() else None
        result.append({
            'wrapper': str(NATIVE_RELATIVE / wrapper),
            'original': str(OLD_RELATIVE / original),
            'original_bytes': len(old),
            'original_sha256': sha256(old),
            'exact_prefix': prefix_matches,
            'original_unchanged_from_r03': unchanged,
        })
    return result


def inspect_slice(name: str) -> dict:
    value = read_json(NATIVE / name)
    return {
        'file': name,
        'selection': value['selection'],
        'complete': value['complete'],
        'local_count': len(value['localContext']),
        'direct_proposition_locals': sum(bool(row['isProp']) for row in value['localContext']),
        'local_names': [row['name'] for row in value['localContext']],
        'selected_nodes': [{
            'declaration': row['declaration'],
            'direct_premise_count': len(row['premises']),
            'premise_occurrences': [premise['occurrence'] for premise in row['premises']],
        } for row in value['nodes']],
        'frontiers': value['frontiers'],
        'compiled_modules': len(value['compiledInventory']['modules']),
    }


def inspect_native(case: str) -> dict:
    bundle = read_json(NATIVE / case / 'checked-1800-r02.json')
    view = read_json(NATIVE / case / 'inspection.json')['native']
    interpretation = read_json(NATIVE / case / 'interpretation.json')
    source_file = NATIVE / ('adam-project' if case == 'adam' else 'project') / interpretation['source']['path']
    source = source_file.read_bytes()
    anchor = interpretation['source']
    selected_lines = '\n'.join(source.decode().splitlines()[anchor['startLine'] - 1:anchor['endLine']])
    assert selected_lines == anchor['quote']
    assert sha256(source) == anchor['sha256']
    assert view['coverage']['complete']
    assert not view['checkEvidence']['unboundObligations']
    checks = {row['obligation']: row for row in bundle['checks']}
    observations = []
    for row in view['checkEvidence']['rows']:
        assert row['binding']['status'] == 'matched-stored-records'
        receipt = row['receipt']['value']
        checked = checks[receipt['obligation']]
        expected = checked['goal'] if checked['mode'] == 'prove' else '¬ (' + checked['goal'] + ')'
        assert receipt['checkedGoal'] == expected
        assert receipt['status'] == checked['status']
        completion = checked['completion']
        assert completion['status'] == 'completed'
        assert completion['replay']['status'] == 'accepted'
        assert completion['trust']['accepted']
        assert completion['captureId'] == checked['capture']['capture']['captureId']
        capture_inventory = checked['capture']['capture']['environment']['compiledInventory']
        assert capture_inventory['moduleCount'] == len(capture_inventory['modules'])
        observations.append({
            'obligation': checked['obligation'],
            'mode': checked['mode'],
            'status': checked['status'],
            'exact_receipt_goal_and_polarity_match': True,
            'completion': completion['status'],
            'retained_replay': completion['replay']['status'],
            'retained_trust_accepted': completion['trust']['accepted'],
            'observed_axioms': completion['trust']['observedAxioms'],
            'capture_module_count': capture_inventory['moduleCount'],
            'goal': checked['goal'],
            'captured_goal_type': checked['capture']['capture']['goal']['typeDisplay'],
        })
    assert len(observations) == 4
    assert set(checks) == {row['obligation'] for row in observations}
    return {
        'dimensions': view['dimensions'],
        'coverage': view['coverage'],
        'inspection_authority': view['authority'],
        'source_anchor': {
            'file': str(source_file.relative_to(PACKET)),
            'start_line': anchor['startLine'],
            'end_line': anchor['endLine'],
            'quote_and_hash_match': True,
        },
        'direct_premise_supply_obligations': sum(row['kind'] == 'premise-supply' for row in bundle['plan']['obligations']),
        'selected_slice_premise_count': sum(len(row['premises']) for row in bundle['plan']['slice']['nodes']),
        'selected_compiled_modules': len(bundle['plan']['slice']['compiledInventory']['modules']),
        'checks': observations,
        'definition_declarations_in_inspection': {
            needle: needle in (NATIVE / case / 'inspection.json').read_text()
            for needle in ['structure Inputs', 'def commonLaw', 'def sampledTrue', 'sourceLaw_resample']
        },
    }


def check_fdp_arithmetic() -> dict:
    inputs = tuple(product(range(4), repeat=2))
    events = tuple(product((False, True), repeat=2))

    def probability(pair: tuple[int, int]) -> Fraction:
        if pair[0] == 0:
            return Fraction(2, 3) if pair[1] == 1 else Fraction(1, 3)
        return Fraction(1, 3) if pair[1] == 1 else Fraction(1, 6)

    def event_mass(prob: Fraction, event: tuple[bool, bool]) -> Fraction:
        return (prob if event[0] else Fraction(0)) + (1 - prob if event[1] else Fraction(0))

    count = 0
    for x, y in product(inputs, repeat=2):
        assert 0 <= probability(x) <= 1
        if sum(a != b for a, b in zip(x, y)) != 1:
            continue
        for event in events:
            count += 1
            assert event_mass(probability(x), event) <= 2 * event_mass(probability(y), event)

    def sampled(dataset: tuple[int, int, int], shuffled: bool = False) -> Fraction:
        selections = tuple(permutations(range(3), 2) if shuffled else combinations(range(3), 2))
        return sum((probability((dataset[i], dataset[j])) for i, j in selections), Fraction(0)) / len(selections)

    first, second = (0, 1, 2), (3, 1, 2)
    inherited = sampled(first), sampled(second)
    shuffled = sampled(first, True), sampled(second, True)
    gap = inherited[0] - Fraction(5, 3) * inherited[1]
    assert gap == Fraction(1, 54)
    for event in events:
        for x, y in [shuffled, shuffled[::-1]]:
            assert event_mass(x, event) <= Fraction(5, 3) * event_mass(y, event)
    return {
        'authority': 'independent rational-arithmetic reproduction, not Lean replay',
        'input_pairs': len(inputs),
        'binary_events': len(events),
        'directed_base_privacy_checks': count,
        'base_violation_count': 0,
        'inherited_true_probabilities': list(map(str, inherited)),
        'factor_5_over_3_gap': str(gap),
        'shuffled_true_probabilities': list(map(str, shuffled)),
        'shuffled_selected_pair_all_event_bidirectional_bound': True,
        'general_shuffled_theorem_verified': False,
    }


def main() -> None:
    result = {
        'scope': 'packet source and stored-record checks only; no native Lean execution',
        'prefixes': prefix_checks(),
        'slices': [inspect_slice(name) for name in ['adam-slice.json', 'adam-wrapper-slice.json', 'fdp-slice-03.json']],
        'native_cases': {case: inspect_native(case) for case in ['adam', 'fdp']},
        'fdp_arithmetic': check_fdp_arithmetic(),
    }
    destination = Path(__file__).with_name('verification-results.json')
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({
        'status': 'passed',
        'stored_native_checks': sum(len(case['checks']) for case in result['native_cases'].values()),
        'prefixes_match': all(row['exact_prefix'] for row in result['prefixes']),
        'fdp_base_checks': result['fdp_arithmetic']['directed_base_privacy_checks'],
        'fdp_gap': result['fdp_arithmetic']['factor_5_over_3_gap'],
        'results': str(destination),
    }, indent=2))


if __name__ == '__main__':
    main()
