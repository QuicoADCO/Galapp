"""
Tests de integración — Endpoints de salud y error handlers
===========================================================
"""


class TestHealth:

    def test_health_returns_200(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.get_json()["status"] == "ok"

    def test_health_no_auth_required(self, client):
        """El health check debe ser público."""
        res = client.get("/api/health")
        assert res.status_code == 200


class TestErrorHandlers:

    def test_404_returns_json(self, client):
        res = client.get("/ruta/que/no/existe")
        assert res.status_code == 404
        data = res.get_json()
        assert "error" in data

    def test_404_no_stack_trace(self, client):
        """La respuesta 404 no debe filtrar información interna."""
        res = client.get("/ruta/inexistente")
        body = res.data.decode()
        assert "Traceback" not in body
        assert "File " not in body
