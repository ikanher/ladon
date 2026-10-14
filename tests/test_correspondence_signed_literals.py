"""The typed profile admits bounded signed numerals without rewriting legacy."""
import pytest

from ladon.correspondence_interpretation import LEGACY_PROFILE, lower_formula


def test_signed_integer_is_lowered_only_in_current_profile():
    term = {'tag': 'app', 'symbol': 'neg', 'args': [{'tag': 'const', 'name': '-3'}]}
    symbols = {'neg': {'leanName': 'Neg.neg', 'leanType': 'Int → Int'}}
    assert '(-3)' in lower_formula(term, symbols)
    with pytest.raises(ValueError, match='explicit symbol mapping'):
        lower_formula(term, symbols, _profile=LEGACY_PROFILE)


@pytest.mark.parametrize('value', ['--3', '- 3', '-3; trivial', '-' + '3' * 21])
def test_malformed_or_overbound_signed_literal_rejects(value):
    with pytest.raises(ValueError):
        lower_formula({'tag': 'const', 'name': value}, {})
