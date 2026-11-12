"""Human CLI guidance without changing immutable contract evidence."""

import shlex
import sys

from ladon.proof_contract_recognition import MAX_ESTIMATE_BINDERS
from ladon.proof_contract_worker import PROFILE


def emit_contract_guidance(args, result):
    if (args.operation == 'produce' and result.get('channel') == 'formal'
            and result.get('status') == 'unsupported' and result.get('observation') is not None):
        _unsupported_statement(args, result)
    if args.operation == 'expand' and result.get('slice', {}).get('status') == 'unavailable':
        _unavailable_application(result['slice'])


def _unsupported_statement(args, result):
    print(f'Typed Lean statement retained; this statement is outside the current {PROFILE} '
          'contract summary profile. This does not reject the Lean theorem.',
          file=sys.stderr)
    for residual in result.get('residuals', [])[:3]:
        print((str(residual.get('code', 'unsupported')) + ': ' +
               str(residual.get('message', 'Unsupported statement shape')))[:500], file=sys.stderr)
        if residual.get('code') == 'telescope-limit':
            print(f'This recognizer admits at most {MAX_ESTIMATE_BINDERS} binders '
                  '(parameters and hypotheses); this is a profile restriction.', file=sys.stderr)
    source = str(args.output) if args.output else '<saved-observation.json>'
    if not args.output:
        print('Save the JSON observation using --output before expanding it.', file=sys.stderr)
    command = shlex.join(['ladon', 'investigation', 'contract', 'expand', '--root',
                          str(args.root), '--input', source, '--application',
                          '<qualified-provider-name>', '--obligation-id', 'premise:1'])
    print('To inspect an original proof application, substitute its qualified name:\n'
          + command + '\nExpansion has separate bounds and may remain incomplete.', file=sys.stderr)


def _unavailable_application(sliced):
    print('No application route was established. Inspect the saved slice frontiers and '
          'processReceipts for the extraction failure.', file=sys.stderr)
    for receipt in sliced.get('processReceipts', []):
        if receipt.get('returncode', 0) != 0:
            detail = (receipt.get('stdout', '') + '\n' + receipt.get('stderr', '')).strip()
            if detail:
                safe = ''.join(c if c.isprintable() or c in '\n\t' else repr(c)[1:-1]
                               for c in detail[-1200:])
                print('First failed process output:\n' + safe[-1200:], file=sys.stderr)
            break
