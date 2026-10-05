import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from friday import db
from friday.api import app
from friday.config import settings


@pytest.fixture(autouse=True)
def database(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'registration_open', True)
    engine = db.make_engine('sqlite:///' + str(tmp_path / 'test.db'))
    db.Base.metadata.create_all(engine)
    monkeypatch.setattr(db, 'engine', engine)
    monkeypatch.setattr(db, 'Session', sessionmaker(engine, expire_on_commit=False))
    monkeypatch.setattr(settings, 'api_key', 'test-fixture-not-a-key')
    monkeypatch.setattr(settings, 'search_key', 'test-fixture-not-a-key')
    monkeypatch.setattr(settings, 'model', 'fixture-model')
    monkeypatch.setattr(settings, 'origin', 'http://testserver')
    yield
    engine.dispose()


@pytest.fixture
def client():
    with TestClient(app, headers={'Origin': 'http://testserver', 'X-Friday-Request': '1'}) as c:
        result = c.post('/api/auth/register', json={'email': 'alice@example.com', 'password': 'test-password-long'})
        assert result.status_code == 201
        yield c
