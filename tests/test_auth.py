import pytest
from app.main import create_app
from app.database import db


@pytest.fixture
def client():
    app = create_app(test_config={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


def test_register(client):
    response = client.post("/auth/register", json={
        "username": "test",
        "email": "test@test.com",
        "password": "1234"
    })

    assert response.status_code == 201


def test_login(client):
    client.post("/auth/register", json={
        "username": "test2",
        "email": "test2@test.com",
        "password": "1234"
    })

    response = client.post("/auth/login", json={
        "username": "test2",
        "password": "1234"
    })

    assert response.status_code == 200
    data = response.get_json()
    assert "token" in data
