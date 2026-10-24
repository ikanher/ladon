"""Parent-free provider adapters and generated contract correspondence subjects."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from ._proof_contract_source_obligations_formula import _formula_symbols
from ._proof_contract_source_obligations_staging import _safe_create_parent, _write_probe
from .proof_contract_bridge_supervision import run_bridge_job
from .source_association_io import _read_regular


def prepare_bridge(request, construction, deadline, limits):
    """Only consume a freshly verified source construction, never caller plans."""
    from ._proof_contract_bridge_goals import bridge_goals, bridge_interpretation
    from .correspondence_check import prepare_correspondence

    demand = _selected_demand(construction)
    root = Path(request['repoRoot']).resolve(strict=True)
    selected = construction['selectedRequirement']
    provider = request['providerSnapshot']
    symbols = _formula_symbols(provider['observation']['normalizedTypeExpr'])
    adapter, source = _stage_adapter(root, provider, construction, symbols)
    extraction = run_bridge_job('extract-provider', {**adapter,
        'declaration': source['declaration'], 'application': provider['selection']['declaration']},
        deadline_monotonic=deadline, limits=limits)
    prepared = {'adapter': adapter, 'extraction': extraction, 'goals': [],
                'selectedDemand': demand}
    actual = extraction.get('result')
    if extraction['status'] != 'completed' or not isinstance(actual, dict) or actual.get('complete') is not True:
        return prepared
    record = bridge_interpretation({'contractRecord': selected['contractRecord']},
        {key: value for key, value in symbols.items() if key != 'kind'},
        {'path': source['requirementSource']['path']})
    correspondence = prepare_correspondence(record, actual, {'s': 'b0', 'x': 'b1'})
    demand_digest = _digest(json.dumps(demand, sort_keys=True, separators=(',', ':')).encode())
    prepared.update(correspondence=correspondence, symbols=record['symbols'],
                    selectedDemandDigest=demand_digest,
                    goals=bridge_goals(correspondence, {**construction,
                        'selectedDemand': demand, 'selectedDemandDigest': demand_digest}))
    return prepared


def _stage_adapter(root, provider, construction, symbols):
    subject = construction['prefixCheck']['subject']
    path = (root / subject['path']).resolve(strict=True)
    path.relative_to(root)
    prefix = _read_regular(path, 8*1024**2)
    if _digest(prefix) != subject['digest']:
        raise ValueError('checked source prefix changed before bridge construction')
    quote = json.dumps(construction['selectedRequirement']['contractRecord'], sort_keys=True,
                       separators=(',', ':'), ensure_ascii=False)
    key = hashlib.sha256((construction['requestDigest'] + quote).encode()).hexdigest()
    namespace = 'LadonBridge_' + key[:24]
    declaration = namespace + '.provider'
    text = prefix + _adapter_text(namespace, provider['selection']['declaration'], symbols).encode()
    directory = root / '.ladon' / 'contract-obligations' / key / 'bridge'
    _safe_create_parent(root, directory)
    target, sidecar = directory / 'Bridge.lean', directory / 'requirement.txt'
    _write_probe(target, text)
    _write_probe(sidecar, quote.encode())
    source = {'path': str(sidecar.relative_to(root)), 'startLine': 1, 'endLine': 1,
              'quote': quote, 'sha256': hashlib.sha256(quote.encode()).hexdigest()}
    return ({'repoRoot': str(root), 'sourcePath': str(target.relative_to(root)),
             'sourceDigest': _digest(text)},
            {'declaration': declaration, 'requirementSource': source})


def _adapter_text(namespace, provider, symbols):
    # Symbols came from fresh normalized expressions; the interpretation
    # validator also rejects anything outside ordinary qualified Lean names.
    from .correspondence_interpretation import validate_symbols

    validate_symbols({key: {'leanName': symbols[key], 'leanType': 'Nat'}
                      for key in ('leftOperator', 'map', 'constantName', 'inputScale')})
    validate_symbols({'provider': {'leanName': provider, 'leanType': 'Nat'}})
    out, mapping = symbols['leftOperator'], symbols['map']
    coefficient, inp, offset = symbols['constantName'], symbols['inputScale'], symbols['offset']
    return (f'\nnamespace {namespace}\n'
        f'theorem provider (s x : Nat) : _root_.{out} s (_root_.{mapping} x) ≤ '
        f'_root_.{coefficient} * _root_.{inp} (s + {offset}) x := _root_.{provider} s x\n'
        f'end {namespace}\n')


def _digest(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def _selected_demand(construction):
    from ._contract_propagation_budget import fingerprint

    routes = [row for row in construction['routeComparisons']
              if row['routeId'] == construction['selectedRouteId']]
    if len(routes) != 1:
        raise ValueError('bridge route is not unique')
    selected = construction['selectedRequirement']
    digest = 'sha256:' + fingerprint(selected['contractRecord']).hex()
    demands = [row for row in routes[0].get('obligationBundle', {}).get('demands', [])
               if row.get('witnessRef') == selected['parentWitnessRef']
               and row.get('outputContractDigest') == digest
               and row.get('status') == 'requires-source-check']
    if len(demands) != 1:
        raise ValueError('bridge requires one exact version-two source demand')
    return copy.deepcopy(demands[0])
