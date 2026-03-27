"""
Tests unitarios y de integración — Votación
============================================
Unitarios:   validan la restricción de unicidad en el modelo Vote.
Integración: cubren el flujo completo de votación, protección IDOR
             y restricción de un voto por usuario por encuesta.
"""
from tests.conftest import auth_headers, register, login


# ════════════════════════════════════════════════════════════
# Helper
# ════════════════════════════════════════════════════════════

def _setup_survey_with_options(client, headers):
    """Crea una encuesta con dos opciones y devuelve (survey_id, [option_ids])."""
    res = client.post("/api/surveys", headers=headers, json={"title": "Test vote survey"})
    sid = res.get_json()["id"]

    o1 = client.post(f"/api/surveys/{sid}/options", headers=headers,
                     json={"option_text": "Opción A"}).get_json()["id"]
    o2 = client.post(f"/api/surveys/{sid}/options", headers=headers,
                     json={"option_text": "Opción B"}).get_json()["id"]
    return sid, [o1, o2]


# ════════════════════════════════════════════════════════════
# TESTS UNITARIOS — restricción de unicidad en Vote
# ════════════════════════════════════════════════════════════

class TestVoteModel:

    def test_same_user_cannot_vote_twice_in_db(self, client):
        """La UniqueConstraint a nivel BD impide dos votos del mismo user."""
        import pytest
        from sqlalchemy.exc import IntegrityError
        from app.models.survey import Survey, SurveyOption, Vote
        from app.database import db

        with client.application.app_context():
            s = Survey(title="Q", created_by=1)
            db.session.add(s)
            db.session.flush()

            opt = SurveyOption(survey_id=s.id, option_text="A")
            db.session.add(opt)
            db.session.flush()

            db.session.add(Vote(survey_id=s.id, user_id=5, option_id=opt.id))
            db.session.commit()

            db.session.add(Vote(survey_id=s.id, user_id=5, option_id=opt.id))
            with pytest.raises(IntegrityError):
                db.session.commit()

    def test_different_users_can_vote_same_survey(self, client):
        from app.models.survey import Survey, SurveyOption, Vote
        from app.database import db

        with client.application.app_context():
            s = Survey(title="Q", created_by=1)
            db.session.add(s)
            db.session.flush()

            opt = SurveyOption(survey_id=s.id, option_text="A")
            db.session.add(opt)
            db.session.flush()

            db.session.add(Vote(survey_id=s.id, user_id=1, option_id=opt.id))
            db.session.add(Vote(survey_id=s.id, user_id=2, option_id=opt.id))
            db.session.commit()

            count = Vote.query.filter_by(survey_id=s.id).count()
            assert count == 2


# ════════════════════════════════════════════════════════════
# TESTS DE INTEGRACIÓN — POST /api/votes
# ════════════════════════════════════════════════════════════

class TestVote:

    def test_success_returns_201(self, client):
        headers = auth_headers(client)
        sid, options = _setup_survey_with_options(client, headers)
        res = client.post("/api/votes", headers=headers, json={
            "survey_id": sid,
            "option_id": options[0]
        })
        assert res.status_code == 201
        assert res.get_json()["message"] == "Vote recorded"

    def test_double_vote_returns_400(self, client):
        headers = auth_headers(client)
        sid, options = _setup_survey_with_options(client, headers)

        client.post("/api/votes", headers=headers, json={
            "survey_id": sid, "option_id": options[0]
        })
        res = client.post("/api/votes", headers=headers, json={
            "survey_id": sid, "option_id": options[1]
        })
        assert res.status_code == 400
        assert "already voted" in res.get_json()["error"].lower()

    def test_user_id_is_taken_from_jwt_not_body(self, client):
        """IDOR: enviar user_id en el body no debe afectar quién vota."""
        headers = auth_headers(client, username="alice")
        sid, options = _setup_survey_with_options(client, headers)

        res = client.post("/api/votes", headers=headers, json={
            "survey_id": sid,
            "option_id": options[0],
            "user_id": 9999          # debe ser ignorado
        })
        assert res.status_code == 201

        # Votar de nuevo con el mismo token debe fallar (ya votó)
        res2 = client.post("/api/votes", headers=headers, json={
            "survey_id": sid,
            "option_id": options[1],
        })
        assert res2.status_code == 400

    def test_two_different_users_can_vote(self, client):
        headers_a = auth_headers(client, username="alice")
        headers_b = auth_headers(client, username="bob",
                                  password="Password1")

        sid, options = _setup_survey_with_options(client, headers_a)

        res_a = client.post("/api/votes", headers=headers_a, json={
            "survey_id": sid, "option_id": options[0]
        })
        res_b = client.post("/api/votes", headers=headers_b, json={
            "survey_id": sid, "option_id": options[1]
        })
        assert res_a.status_code == 201
        assert res_b.status_code == 201

    def test_missing_survey_id_returns_400(self, client):
        headers = auth_headers(client)
        res = client.post("/api/votes", headers=headers, json={
            "option_id": 1
        })
        assert res.status_code == 400

    def test_missing_option_id_returns_400(self, client):
        headers = auth_headers(client)
        res = client.post("/api/votes", headers=headers, json={
            "survey_id": 1
        })
        assert res.status_code == 400

    def test_unauthenticated_returns_401(self, client):
        res = client.post("/api/votes", json={
            "survey_id": 1, "option_id": 1
        })
        assert res.status_code == 401


# ════════════════════════════════════════════════════════════
# TESTS DE INTEGRACIÓN — Flujo completo end-to-end
# ════════════════════════════════════════════════════════════

class TestFullVotingFlow:

    def test_register_login_create_vote(self, client):
        """Flujo completo: registro → login → crear encuesta → votar."""
        # 1. Registro
        r = client.post("/auth/register", json={
            "username": "voter",
            "email": "voter@example.com",
            "password": "Voter1234"
        })
        assert r.status_code == 201

        # 2. Login
        r = client.post("/auth/login", json={
            "username": "voter", "password": "Voter1234"
        })
        assert r.status_code == 200
        token = r.get_json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Crear encuesta
        r = client.post("/api/surveys", headers=headers,
                        json={"title": "¿Python o Java?"})
        assert r.status_code == 201
        sid = r.get_json()["id"]

        # 4. Añadir opciones
        r1 = client.post(f"/api/surveys/{sid}/options", headers=headers,
                         json={"option_text": "Python"})
        r2 = client.post(f"/api/surveys/{sid}/options", headers=headers,
                         json={"option_text": "Java"})
        assert r1.status_code == 201
        assert r2.status_code == 201
        oid = r1.get_json()["id"]

        # 5. Verificar que aparece en el listado
        surveys = client.get("/api/surveys", headers=headers).get_json()
        assert any(s["id"] == sid for s in surveys)

        # 6. Votar
        r = client.post("/api/votes", headers=headers,
                        json={"survey_id": sid, "option_id": oid})
        assert r.status_code == 201

        # 7. Segundo voto debe fallar
        r = client.post("/api/votes", headers=headers,
                        json={"survey_id": sid, "option_id": oid})
        assert r.status_code == 400
