"""Budgeted native JSON loading retains strict input rejection at the CLI boundary."""

import io

import pytest

from ladon.proof_contract_io import load_bounded_plans


def test_budget_is_shared_across_files_and_exact_boundary_is_admitted(tmp_path):
    paths = [tmp_path / f"input{i}.json" for i in range(2)]
    for path in paths:
        path.write_bytes(b'{"x":1}')
    assert load_bounded_plans(paths, max_bytes=14) == [{"x": 1}, {"x": 1}]
    with pytest.raises(ValueError, match="aggregate"):
        load_bounded_plans(paths, max_bytes=13)


@pytest.mark.parametrize("text,error", [
    ('{"x":1,"x":2}', ValueError), ('{"x":NaN}', ValueError),
    ('[]', TypeError), ('{"x":Infinity}', ValueError),
])
def test_native_loader_rejects_duplicate_nonfinite_and_nonobject_inputs(tmp_path, text, error):
    path = tmp_path / "input.json"
    path.write_text(text)
    with pytest.raises(error):
        load_bounded_plans([path], max_bytes=128)


def test_input_that_grows_is_bounded_by_the_actual_read_size():
    sizes = []

    class GrowingInput:
        def open(self, _mode):
            class Stream(io.BytesIO):
                def read(self, size):
                    sizes.append(size)
                    return super().read(size)

            return Stream(b"x" * 10000)

    with pytest.raises(ValueError, match="aggregate"):
        load_bounded_plans([GrowingInput()], max_bytes=64)
    assert sizes == [65]


def test_excessive_json_depth_is_a_bounded_validation_error(tmp_path):
    path = tmp_path / "deep.json"
    path.write_text('{"x":' + '[' * 2000 + '0' + ']' * 2000 + '}')
    with pytest.raises(ValueError, match="bounded"):
        load_bounded_plans([path], max_bytes=10000)
