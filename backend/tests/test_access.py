import time
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

def test_owner_persistent_cookie(client, monkeypatch):
    monkeypatch.setattr(settings,'owner_email','alice@example.com')
    r=client.post('/api/auth/login',json={'email':'alice@example.com','password':'test-password-long'})
    assert 'Max-Age=7776000' in r.headers['set-cookie']
