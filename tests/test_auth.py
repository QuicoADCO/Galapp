import pytest
from app.main import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


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