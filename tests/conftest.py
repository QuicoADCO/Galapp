import os
import pytest

# Variables de entorno antes de importar la app (el módulo las valida al cargarse)
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key")

from app.main import create_app  # noqa: E402
from app.database import db      # noqa: E402


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


# ── Helpers reutilizables en los tests ──────────────────────────────────────

def register(client, username="alice", email="alice@example.com", password="Password1"):
    return client.post("/auth/register", json={
        "username": username,
        "email": email,
        "password": password,
    })


def login(client, username="alice", password="Password1"):
    return client.post("/auth/login", json={
        "username": username,
        "password": password,
    })


def auth_headers(client, username="alice", password="Password1"):
    """Registra (si no existe) y devuelve cabeceras con JWT."""
    register(client, username=username, password=password,
             email=f"{username}@example.com")
    res = login(client, username=username, password=password)
    token = res.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}
