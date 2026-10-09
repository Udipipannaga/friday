import time
from friday.config import settings
from friday import db


def desk(client, monkeypatch):
    monkeypatch.setattr(settings, 'owner_email', 'alice@example.com')
    companies = client.get('/api/operating/companies')
    assert companies.status_code == 200
    return companies.json()[0]['id']


def person(client, company_id, role, **fields):
    response = client.post(f'/api/operating/companies/{company_id}/people',
        json={'role': role, 'name': fields.pop('name', 'A person'), **fields})
    assert response.status_code == 201, response.text
    return response.json()


def tool(client, company_id, name, person_id=None, job_id=None, key=None):
    return client.post(f'/api/operating/companies/{company_id}/tools/{name}',
        json={'request_key': key or db.uid(), 'person_id': person_id, 'job_id': job_id})


def test_owner_only_and_not_configured(client, monkeypatch):
    assert client.get('/api/operating/companies').status_code == 403
    company_id = desk(client, monkeypatch)
    monkeypatch.setattr(settings, 'model', '')
    result = tool(client, company_id, 'weekly_note')
    assert result.json() == {'status': 'NOT_RUN'}
    assert client.get(f'/api/operating/companies/{company_id}').json()['drafts'] == []


def test_creator_video_gate_job_gate_and_audit(client, monkeypatch):
    company_id = desk(client, monkeypatch)
    creator = person(client, company_id, 'creator', name='Creator A',
        published_video_title='Published film', published_video_url='https://example.org/film')
    editor = person(client, company_id, 'editor', name='Editor B')
    assert tool(client, company_id, 'draft_outreach', creator['id']).status_code == 409
    assert tool(client, company_id, 'draft_outreach', editor['id']).status_code == 409
    verified = client.patch(f'/api/operating/companies/{company_id}/people/{creator["id"]}',
        json={'video_verified': True})
    assert verified.status_code == 200
    key = db.uid()
    result = tool(client, company_id, 'draft_outreach', creator['id'], key=key)
    assert result.status_code == 201 and 'Published film' in result.json()['draft']
    assert result.json()['result']['model_called'] is False
    assert result.json()['status'] == 'pending_owner_review'
    assert tool(client, company_id, 'draft_outreach', creator['id'], key=key).json()['id'] == result.json()['id']
    assert tool(client, company_id, 'weekly_note', key=key).status_code == 409
    job = client.post(f'/api/operating/companies/{company_id}/jobs', json={
        'creator_id': creator['id'], 'title': 'Cut one film', 'brief': 'A vertical cut',
        'creator_confirmation': 'Owner recorded the creator brief', 'sample_scope': 'a short test cut',
        'sample_fee': 'INR 500', 'sample_deadline': 'Friday', 'invoice_amount': 'INR 2000'})
    assert job.status_code == 201, job.text
    editor_draft = tool(client, company_id, 'draft_outreach', editor['id'], job.json()['id'])
    assert editor_draft.status_code == 201 and 'INR 500' in editor_draft.json()['draft']
    assert 'Creator A' not in editor_draft.json()['draft']
    invoice = tool(client, company_id, 'draft_invoice', job_id=job.json()['id'])
    assert invoice.status_code == 201 and 'Do not send' in invoice.json()['draft']
    assert client.get(f'/api/operating/companies/{company_id}').json()['drafts']


def test_followup_weekly_note_and_company_isolation(client, monkeypatch):
    company_id = desk(client, monkeypatch)
    creator = person(client, company_id, 'creator', name='Creator A',
        published_video_title='Published film', published_video_url='https://example.org/film',
        video_verified=True, open_loop='Asked about one paid cut', join_evidence='Owner-recorded signup')
    assert tool(client, company_id, 'chase_silent', creator['id']).status_code == 409
    follow = client.patch(f'/api/operating/companies/{company_id}/people/{creator["id"]}',
        json={'record_contact_now': True})
    assert follow.status_code == 200
    assert tool(client, company_id, 'chase_silent', creator['id']).status_code == 409
    with db.Session.begin() as s:
        s.get(db.OperatingPerson, creator['id']).last_contact_at = time.time() - 4 * 86400
    assert tool(client, company_id, 'chase_silent', creator['id']).status_code == 201
    weekly = tool(client, company_id, 'weekly_note')
    assert weekly.status_code == 201 and '1 new creator' in weekly.json()['draft']
    other = client.post('/api/operating/companies', json={'name': 'Second company'}).json()
    assert tool(client, other['id'], 'draft_outreach', creator['id']).status_code == 404
    bad = client.patch(f'/api/operating/companies/{company_id}/people/{creator["id"]}',
        json={'open_loop': 'Card 4111 1111 1111 1111'})
    assert bad.status_code == 422
