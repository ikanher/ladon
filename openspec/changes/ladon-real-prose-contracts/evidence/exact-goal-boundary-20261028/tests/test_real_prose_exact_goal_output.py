"""Expression byte bounds apply before comparing the caller's claimed view."""

from test_real_prose_exact_goal import DECLARATIONS, request, run, source
from test_real_prose_exact_goal import project as _project

project = _project


def test_large_owner_has_a_separate_rendered_byte_limit(project):
    value = request()
    declarations = list(DECLARATIONS)
    literal = 'x' * (4 * 1024**2)
    declarations[1] = f'def Reading : Prop := "{literal}" = "{literal}"'
    value['authored']['range']['endColumn'] = len(declarations[1])
    text = source(value).replace('\n'.join(DECLARATIONS), '\n'.join(declarations))
    (project / 'Case.lean').write_text(text)
    result = run(project, 'Case.lean')
    assert not result.succeeded
    assert 'exact goal expression exceeds 8 MiB' in result.stdout + result.stderr
