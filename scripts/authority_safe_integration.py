#!/usr/bin/env python3
"""Verify complete candidate-specific integration evidence without release promotion."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ladon.child_acceptance import _json_object
from ladon.integration_acceptance import evaluate_integration_gate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for role in ('correctness', 'authority', 'integration'):
        parser.add_argument('--' + role, type=Path, required=True)
        parser.add_argument('--' + role + '-inventory', type=Path, required=True)
    parser.add_argument('--evidence-root', type=Path, required=True)
    args = parser.parse_args()
    try:
        receipts = {role: _json_object(getattr(args, role).read_bytes())
                    for role in ('correctness', 'authority', 'integration')}
        inventories = {role: _json_object(getattr(args, role + '_inventory').read_bytes())
                       for role in receipts}
        result = evaluate_integration_gate(
            receipts['integration'], receipts['correctness'], receipts['authority'],
            bundle_root=args.evidence_root, inventories=inventories,
        )
    except (OSError, ValueError, KeyError, TypeError) as error:
        result = {'schema': 'ladon-integration-qualification-v1', 'status': 'failed',
                  'reason': str(error)}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['status'] == 'passed' else 2


if __name__ == '__main__':
    raise SystemExit(main())
