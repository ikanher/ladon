"""Falsification controls for the scope recovery implementation."""

import pytest

from ladon.extraction import parse_text_declarations


@pytest.mark.parametrize('ending', ['end A B', 'end 3', 'end A.'])
def test_invalid_named_end_does_not_silently_close_a_frame(ending):
    rows = parse_text_declarations(
        f'namespace A\ntheorem before : True := trivial\n{ending}\ntheorem after : True := trivial\n'
    )
    assert all(row.candidate_name is None for row in rows)


@pytest.mark.parametrize('prefix', ['unsafe', 'partial', 'local', 'protected'])
def test_declaration_only_modifiers_do_not_open_sections(prefix):
    rows = parse_text_declarations(f'{prefix} section\ntheorem t : True := trivial\n')
    assert rows[0].candidate_name is None


def test_dotted_section_names_close_component_wise():
    rows = parse_text_declarations(
        'namespace N\nsection A.B\ntheorem first : True := trivial\n'
        'end B\nend A\ntheorem later : True := trivial\nend N\n'
    )
    assert [row.candidate_name for row in rows] == ['N.first', 'N.later']
    assert rows[0].section_stack == ('A', 'B')
