import time
from friday import db, operating
from friday.config import settings


def test_weekly_note_schedule_is_owner_enabled_draft_only(client, monkeypatch):
    assert client.post('/api/operating/companies/unknown/weekly-schedule',
        json={'enabled': True}).status_code == 403
    monkeypatch.setattr(settings, 'owner_email', 'alice@example.com')
    company_id = client.get('/api/operating/companies').json()[0]['id']
    path = f'/api/operating/companies/{company_id}/weekly-schedule'
    assert client.get(f'/api/operating/companies/{company_id}').json()['weekly_schedule']['enabled'] is False
    assert client.post(path, json={'enabled': 'yes'}).status_code == 422
    assert client.post(path, json={'enabled': True}).status_code == 200
    first_due = client.get(f'/api/operating/companies/{company_id}').json()['weekly_schedule']['next_run']
    assert operating.run_due_weekly_notes(now=first_due + 1, model_ready=False) == 0
    assert operating.run_due_weekly_notes(now=first_due + 1, model_ready=True) == 1
    assert operating.run_due_weekly_notes(now=first_due + 1, model_ready=True) == 0
    view = client.get(f'/api/operating/companies/{company_id}').json()
    assert len(view['drafts']) == 1
    result = view['drafts'][0]
    assert result['tool'] == 'weekly_note'
    assert result['status'] == 'pending_owner_review'
    assert result['request']['scheduled'] is True
    assert result['result']['model_called'] is False
    assert 'FAILED WEEK' in result['draft']
    assert client.post(path, json={'enabled': False}).status_code == 200
    assert operating.run_due_weekly_notes(now=time.time() + operating.WEEK * 2,
        model_ready=True) == 0
    with db.Session() as s:
        assert s.query(db.OperatingDraft).count() == 1

