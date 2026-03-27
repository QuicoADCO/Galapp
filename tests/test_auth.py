"""
Tests unitarios y de integración — Autenticación
=================================================
Unitarios:   validan la lógica interna de generate_token y token_required
             sin levantar servidor HTTP.
Integración: cubren el flujo completo registro → login → acceso a la API
             a través del cliente de test Flask.
"""
import pytest
from unittest.mock import patch
from app.utils import generate_token, _get_secret
from tests.conftest import register, login, auth_headers


# ════════════════════════════════════════════════════════════
# TESTS UNITARIOS — app/utils.py
# ════════════════════════════════════════════════════════════

class TestGenerateToken:
    """Prueba la función generate_token de forma aislada."""

    def test_returns_string(self, client):
        import jwt
        # Simular un objeto user mínimo
        class FakeUser:
            id = 1
            username = "alice"
            role = "user"

        token = generate_token(FakeUser())
        assert isinstance(token, str)
        assert token.count(".") == 2  # formato JWT: header.payload.signature

    def test_payload_contains_required_claims(self, client):
        import jwt

        class FakeUser:
            id = 42
            username = "bob"
            role = "admin"

        token = generate_token(FakeUser())
        payload = jwt.decode(token, _get_secret(), algorithms=["HS256"])

        assert payload["id"] == 42
        assert payload["username"] == "bob"
        assert payload["role"] == "admin"
        assert "exp" in payload

    def test_token_expires_in_about_one_hour(self, client):
        import jwt
        from datetime import datetime, timezone

        class FakeUser:
            id = 1
            username = "x"
            role = "user"

        token = generate_token(FakeUser())
        payload = jwt.decode(token, _get_secret(), algorithms=["HS256"])
        now = datetime.now(timezone.utc).timestamp()
        delta = payload["exp"] - now
        # El token debe expirar entre 59 y 61 minutos desde ahora
        assert 3540 <= delta <= 3660


class TestGetSecret:
    """Prueba que _get_secret lanza error si la clave no está definida."""

    def test_raises_if_missing(self):
        with patch.dict("os.environ", {}, clear=True):
            import importlib
            import app.utils as utils_module
            # Parchear directamente os.getenv dentro del módulo
            with patch("app.utils.os.getenv", return_value=None):
                with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
                    utils_module._get_secret()


# ════════════════════════════════════════════════════════════
# TESTS DE INTEGRACIÓN — POST /auth/register
# ════════════════════════════════════════════════════════════

class TestRegister:

    def test_success_returns_201(self, client):
        res = register(client)
        assert res.status_code == 201
        assert res.get_json()["message"] == "User created"

    def test_missing_username_returns_400(self, client):
        res = client.post("/auth/register", json={
            "email": "x@x.com", "password": "Password1"
        })
        assert res.status_code == 400

    def test_missing_email_returns_400(self, client):
        res = client.post("/auth/register", json={
            "username": "alice", "password": "Password1"
        })
        assert res.status_code == 400

    def test_missing_password_returns_400(self, client):
        res = client.post("/auth/register", json={
            "username": "alice", "email": "alice@example.com"
        })
        assert res.status_code == 400

    def test_duplicate_username_returns_400(self, client):
        register(client)
        res = register(client)
        assert res.status_code == 400
        assert "exists" in res.get_json()["error"].lower()

    def test_duplicate_email_returns_400(self, client):
        register(client, username="alice")
        res = register(client, username="alice2")  # mismo email por defecto
        assert res.status_code == 400

    def test_weak_password_no_uppercase_returns_400(self, client):
        res = register(client, password="password1")
        assert res.status_code == 400
        assert "Password" in res.get_json()["error"]

    def test_weak_password_too_short_returns_400(self, client):
        res = register(client, password="Ab1")
        assert res.status_code == 400

    def test_weak_password_no_digit_returns_400(self, client):
        res = register(client, password="PasswordOnly")
        assert res.status_code == 400

    def test_invalid_email_returns_400(self, client):
        res = register(client, email="not-an-email")
        assert res.status_code == 400
        assert "email" in res.get_json()["error"].lower()

    def test_invalid_username_too_short_returns_400(self, client):
        res = register(client, username="ab")
        assert res.status_code == 400

    def test_invalid_username_special_chars_returns_400(self, client):
        res = register(client, username="ali ce!")
        assert res.status_code == 400

    def test_empty_body_returns_400(self, client):
        res = client.post("/auth/register", json={})
        assert res.status_code == 400


# ════════════════════════════════════════════════════════════
# TESTS DE INTEGRACIÓN — POST /auth/login
# ════════════════════════════════════════════════════════════

class TestLogin:

    def test_success_returns_token(self, client):
        register(client)
        res = login(client)
        assert res.status_code == 200
        data = res.get_json()
        assert "token" in data
        assert isinstance(data["token"], str)
        assert data["token"].count(".") == 2

    def test_wrong_password_returns_401(self, client):
        register(client)
        res = login(client, password="WrongPass1")
        assert res.status_code == 401
        assert "credentials" in res.get_json()["error"].lower()

    def test_nonexistent_user_returns_401(self, client):
        res = login(client, username="ghost")
        assert res.status_code == 401

    def test_missing_username_returns_400(self, client):
        res = client.post("/auth/login", json={"password": "Password1"})
        assert res.status_code == 400

    def test_missing_password_returns_400(self, client):
        res = client.post("/auth/login", json={"username": "alice"})
        assert res.status_code == 400

    def test_empty_body_returns_400(self, client):
        res = client.post("/auth/login", json={})
        assert res.status_code == 400

    def test_error_message_is_generic(self, client):
        """El mensaje no debe indicar si falló usuario o contraseña (A07)."""
        register(client)
        res_bad_pass = login(client, password="BadPass99")
        res_bad_user = login(client, username="nobody")
        assert res_bad_pass.get_json()["error"] == res_bad_user.get_json()["error"]


# ════════════════════════════════════════════════════════════
# TESTS DE INTEGRACIÓN — Protección JWT
# ════════════════════════════════════════════════════════════

class TestJWTProtection:

    def test_no_token_returns_401(self, client):
        res = client.get("/api/surveys")
        assert res.status_code == 401

    def test_invalid_token_returns_401(self, client):
        res = client.get("/api/surveys", headers={
            "Authorization": "Bearer token.invalido.aqui"
        })
        assert res.status_code == 401

    def test_malformed_header_returns_401(self, client):
        res = client.get("/api/surveys", headers={
            "Authorization": "SinBearer token"
        })
        assert res.status_code == 401

    def test_valid_token_grants_access(self, client):
        headers = auth_headers(client)
        res = client.get("/api/surveys", headers=headers)
        assert res.status_code == 200
