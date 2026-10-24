"""The ordinary CLI exposes bounded provider expansion with structured errors."""
import json

from ladon.proof_contract_cli import contract_main


def test_provider_expansion_cli_help_exposes_bound_inputs(capsys):
    from ladon.proof_contract_cli import _parser
    parser = _parser()
    assert 'expand-provider' in parser.format_help()
    try:
        parser.parse_args(['expand-provider','--help'])
    except SystemExit as error:
        assert error.code == 0
    help_text = capsys.readouterr().out
    assert '--request' in help_text
    assert '--application' in help_text
    assert '--timeout-seconds' in help_text
    assert '--max-rss-mib' in help_text


def test_provider_expansion_cli_invalid_input_is_bounded_json(tmp_path, capsys):
    paths = [tmp_path/name for name in ('analysis.json','context.json','request.json')]
    for path in paths:
        path.write_text('{}')
    code = contract_main(['expand-provider','--input',str(paths[0]),
        '--context',str(paths[1]),'--request',str(paths[2]),'--root',str(tmp_path),
        '--application','Eq.trans','--timeout-seconds','0'])
    body = json.loads(capsys.readouterr().out)
    assert code == 2
    assert body['status'] in {'invalid','rejected','incomplete'}
    assert len(json.dumps(body)) < 10000
