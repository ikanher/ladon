"""Repeat saved API controls in a fresh Lean source directory with this checkout."""
import json
import shutil
import sys
from pathlib import Path

from run_acceptance import run_case


def main():
    evidence = Path(__file__).resolve().parent
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=False)
    root = out/'lean-project'
    root.mkdir()
    for name in ('ThreeSteps.lean', 'lean-toolchain'):
        shutil.copyfile(evidence/name, root/name)
    expected = {'positive': 'checked-support', 'middle': 'unresolved-bridge',
                'parent': 'unresolved-bridge'}
    for name, budget in [('positive', 180), ('middle', 180), ('parent', 90)]:
        record = json.loads((evidence/(name+'-request.json')).read_text())
        request = record['sourceRequest']
        request['repoRoot'] = str(root)
        result, _row = run_case(out, name, request, record['terms'], budget)
        assert result['status'] == expected[name], result['diagnostic']
        assert result['wholeMethodAuthority'] == 'none'
        if result.get('memoryReportBackRequired'):
            raise RuntimeError(result['diagnostic']['message'])


if __name__ == '__main__':
    main()
