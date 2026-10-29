"""The live harness must read CLI rejection diagnostics as well as artifacts."""

from real_bound_task32_helpers import cli


def test_invalid_cli_output_is_read_from_stdout_without_changing_exit_expectation(tmp_path):
    invalid = tmp_path / 'invalid.json'
    invalid.write_text('{}')
    result = cli(tmp_path, 'rejected', ['replay-real-transfer', '--input', str(invalid),
                                      '--root', str(tmp_path)], 2)
    assert result['status'] == 'invalid'
    assert isinstance(result['error'], str) and result['error']
    assert not (tmp_path / 'rejected.json').exists()
