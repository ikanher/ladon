"""Conservative statement boundaries for lexical navigation, without Lean parsing."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_DELIMITERS = {'(': ')', '[': ']', '{': '}', '⟨': '⟩'}
_TOKENS = re.compile(r':=|[()\[\]{}⟨⟩|]|(?<![\w.])(?:letI|let|have|suffices|where|match|do)\b')


@dataclass
class _StatementScan:
    stack: list[str] = field(default_factory=list)
    pending_lets: int = 0
    has_match: bool = False
    has_let: bool = False

    def delimiter(self, token: str) -> bool:
        """Track delimiters; raise on mismatched closing syntax."""
        if token in _DELIMITERS:
            self.stack.append(_DELIMITERS[token])
            return True
        if token in _DELIMITERS.values():
            if not self.stack or self.stack.pop() != token:
                raise ValueError('unbalanced statement')
            return True
        return False

    def root_token(self, text: str, token: str, offset: int) -> bool:
        """Return true only at the declaration value/equation boundary."""
        if token in {'let', 'letI'}:
            self.start_let(text, token, offset)
        elif token == ':=':
            return self.assignment()
        elif token in {'have', 'suffices', 'do'}:
            raise ValueError('unsupported statement syntax')
        elif token == 'match':
            self.has_match = True
        else:
            return self.special_boundary(text, token, offset)
        return False

    def start_let(self, text: str, token: str, offset: int) -> None:
        if re.match(r'\s+rec\b', text[offset + len(token):]):
            raise ValueError('unsupported recursive let')
        self.pending_lets += 1
        self.has_let = True

    def assignment(self) -> bool:
        if not self.pending_lets:
            return True
        self.pending_lets -= 1
        return False

    def special_boundary(self, text: str, token: str, offset: int) -> bool:
        if self.pending_lets:
            return False
        if token == 'where':
            return _at_line_start(text, offset)
        return token == '|' and not self.has_match and _equation_clause(text, offset)



def _at_line_start(text: str, offset: int) -> bool:
    return not text[text.rfind('\n', 0, offset) + 1:offset].strip()


def _equation_clause(text: str, offset: int) -> bool:
    """Recognize a line-head equation arm, without treating |x| as an arm."""
    if not _at_line_start(text, offset):
        return False
    end = text.find('\n', offset)
    line = text[offset + 1:end if end >= 0 else len(text)]
    arrow = line.find('=>')
    return arrow >= 0 and '|' not in line[:arrow]


def lexical_signature_boundary(masked_tail: str, *, allow_bodyless: bool = False) -> int | None:
    """Stop before proof/value syntax; ambiguous supported syntax is unavailable.

    Balanced binder/nested-term groups are opaque. Root let/letI assignments are
    consumed before the declaration assignment, for semicolon and newline forms.
    Proof text after that assignment is never scanned for statement validity.
    """
    state = _StatementScan()
    try:
        for match in _TOKENS.finditer(masked_tail):
            token = match.group()
            if state.delimiter(token) or state.stack:
                continue
            if state.root_token(masked_tail, token, match.start()):
                return match.start()
    except ValueError:
        return None
    if state.stack or state.pending_lets:
        return None
    return None if state.has_let and not allow_bodyless else len(masked_tail)
