import time
import pytest
from sqlalchemy import select
from friday import db
from friday.config import settings

def test_private_access_lifecycle(client, monkeypatch):
    monkeypatch.setattr(settings, 'owner_email', 'alice@example.com')
    monkeypatch.setattr(settings, 'registration_open', False)
    owner_cookie=client.cookies.get('friday_session')
    assert client.get('/api/me').json()['is_owner']
    client.cookies.clear()
    assert client.post('/api/auth/register',json={'email':'outsider@example.com','password':'long-test-password'}).status_code==403
    assert client.get('/api/access').status_code==401
    assert client.post('/api/access/request',json={'email':'team@example.com'}).status_code==200
    assert client.post('/api/access/request',json={'email':'team@example.com'}).status_code==200
    client.cookies.set('friday_session',owner_cookie)
    rows=client.get('/api/access').json();assert len(rows)==1
    id=rows[0]['id']
    url=client.post(f'/api/access/{id}/review',json={'action':'approve'}).json()['invitation']
    token=url.split('#invite=')[1]
    with db.Session() as s:
        row=s.get(db.AccessRequest,id);assert row.digest != token;row.expires=time.time()-1;s.commit()
    client.cookies.clear()
    body={'email':'team@example.com','password':'team-long-password','token':token}
    assert client.post('/api/access/accept',json=body).status_code==400
    client.cookies.set('friday_session',owner_cookie)
    body['token']=client.post(f'/api/access/{id}/review',json={'action':'approve'}).json()['invitation'].split('#invite=')[1]
    client.cookies.clear()
    assert client.post('/api/access/accept',json={**body,'email':'wrong@example.com'}).status_code==400
    assert client.post('/api/access/accept',json=body).status_code==200
    assert not client.get('/api/me').json()['is_owner']
    assert client.post('/api/access/request',json={'email':'team@example.com'}).status_code==200
    with db.Session() as s:
        assert s.get(db.AccessRequest,id).status == 'accepted'
    assert client.get('/api/me').status_code==200
    assert client.get('/api/access').status_code==403
    assert client.post(f'/api/access/{id}/review',json={'action':'approve'}).status_code==403
    assert client.get('/api/conversations').json()==[]
    assert client.post('/api/access/accept',json=body).status_code==400
    member_cookie=client.cookies.get('friday_session')
    client.cookies.clear();client.cookies.set('friday_session',owner_cookie)
    assert client.post(f'/api/access/{id}/review',json={'action':'revoke'}).status_code==200
    client.cookies.clear();client.cookies.set('friday_session',member_cookie)
    assert client.get('/api/me').status_code==401
    assert client.post('/api/auth/login',json=body).status_code==403


@pytest.mark.parametrize('decision', ['deny', 'revoke'])
def test_denied_or_revoked_person_can_request_again(client, monkeypatch, decision):
    monkeypatch.setattr(settings, 'owner_email', 'alice@example.com')
    monkeypatch.setattr(settings, 'registration_open', False)
    assert client.post('/api/access/request', json={'email': 'team@example.com'}).status_code == 200
    row_id = client.get('/api/access').json()[0]['id']

    if decision == 'revoke':
        invitation = client.post(f'/api/access/{row_id}/review', json={'action': 'approve'}).json()['invitation']
        owner_cookie = client.cookies.get('friday_session')
        client.cookies.clear()
        assert client.post('/api/access/accept', json={
            'email': 'team@example.com', 'password': 'team-long-password',
            'token': invitation.split('#invite=')[1],
        }).status_code == 200
        client.cookies.clear()
        client.cookies.set('friday_session', owner_cookie)

    assert client.post(f'/api/access/{row_id}/review', json={'action': decision}).status_code == 200
    with db.Session() as s:
        row = s.get(db.AccessRequest, row_id)
        row.created = 1
        s.commit()

    assert client.post('/api/access/request', json={'email': 'TEAM@example.com'}).status_code == 200
    rows = client.get('/api/access').json()
    assert len(rows) == 1
    assert rows[0]['id'] == row_id
    assert rows[0]['status'] == 'pending'
    assert rows[0]['created'] > 1
    with db.Session() as s:
        row = s.get(db.AccessRequest, row_id)
        assert row.digest is None
        assert row.expires == 0
    if decision == 'revoke':
        assert client.post('/api/auth/login', json={
            'email': 'team@example.com', 'password': 'team-long-password',
        }).status_code == 403

def test_owner_persistent_cookie(client, monkeypatch):
    monkeypatch.setattr(settings,'owner_email','alice@example.com')
    r=client.post('/api/auth/login',json={'email':'alice@example.com','password':'test-password-long'})
    assert 'Max-Age=7776000' in r.headers['set-cookie']
