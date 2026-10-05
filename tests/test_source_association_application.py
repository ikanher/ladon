"""Source association targets declarations independently of application spelling."""
from __future__ import annotations

import test_source_association as fixture


def test_applied_candidate_still_has_the_same_source_owner(tmp_path, monkeypatch):
    original_builder = fixture._accepted_artifacts

    def applied(*args, **kwargs):
        payload = dict(args[3], applicationTerm='Owner.target argument')
        return original_builder(*args[:3], payload, **kwargs)

    monkeypatch.setattr(fixture, '_accepted_artifacts', applied)
    _, capture = fixture._api()
    context, _ = fixture._context(tmp_path)
    artifacts = fixture._stored_checked_artifacts(tmp_path, context)
    result = capture(fixture._request(tmp_path, context, artifacts), artifacts,
                     process_runner=fixture._runner(ilean=fixture._ilean()))
    assert result['status'] == 'associated', result
    assert result['checking'] == 'not-assessed'
    fixture._associated(result)
