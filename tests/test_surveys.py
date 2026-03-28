"""
Tests unitarios y de integración — Encuestas, Preguntas y Opciones
==================================================================
Unitarios:   validan la construcción de los modelos ORM directamente.
Integración: cubren el CRUD completo de encuestas, preguntas y opciones
             a través del cliente HTTP, incluyendo control de acceso e IDOR.
"""
import pytest
from tests.conftest import auth_headers, register, login


# ════════════════════════════════════════════════════════════
# TESTS UNITARIOS — app/models/survey.py
# ════════════════════════════════════════════════════════════

class TestSurveyModel:

    def test_survey_created_correctly(self, client):
        from app.models.survey import Survey
        from app.database import db

        with client.application.app_context():
            s = Survey(title="Test survey", description="desc", created_by=1)
            db.session.add(s)
            db.session.commit()
            assert s.id is not None
            assert s.title == "Test survey"
            assert s.created_at is not None

    def test_question_option_linked_to_survey(self, client):
        from app.models.survey import Survey, Question, QuestionOption
        from app.database import db

        with client.application.app_context():
            s = Survey(title="Q", created_by=1)
            db.session.add(s)
            db.session.flush()

            q = Question(survey_id=s.id, text="¿Cuál es tu lenguaje favorito?",
                         question_type="single", order=0)
            db.session.add(q)
            db.session.flush()

            opt = QuestionOption(question_id=q.id, text="Opción A")
            db.session.add(opt)
            db.session.commit()

            assert opt.question_id == q.id
            assert len(s.questions) == 1
            assert len(s.questions[0].options) == 1

    def test_vote_unique_constraint(self, client):
        from app.models.survey import Survey, Question, QuestionOption, Vote
        from app.database import db
        from sqlalchemy.exc import IntegrityError

        with client.application.app_context():
            s = Survey(title="Q", created_by=1)
            db.session.add(s)
            db.session.flush()

            q = Question(survey_id=s.id, text="¿A o B?",
                         question_type="single", order=0)
            db.session.add(q)
            db.session.flush()

            opt = QuestionOption(question_id=q.id, text="A")
            db.session.add(opt)
            db.session.flush()

            v1 = Vote(question_id=q.id, user_id=1, option_id=opt.id)
            db.session.add(v1)
            db.session.commit()

            v2 = Vote(question_id=q.id, user_id=1, option_id=opt.id)
            db.session.add(v2)
            with pytest.raises(IntegrityError):
                db.session.commit()


# ════════════════════════════════════════════════════════════
# TESTS DE INTEGRACIÓN — GET /api/surveys
# ════════════════════════════════════════════════════════════

class TestGetSurveys:

    def test_returns_empty_list_initially(self, client):
        headers = auth_headers(client)
        res = client.get("/api/surveys", headers=headers)
        assert res.status_code == 200
        assert res.get_json() == []

    def test_returns_created_survey(self, client):
        headers = auth_headers(client)
        client.post("/api/surveys", headers=headers, json={"title": "My survey"})
        res = client.get("/api/surveys", headers=headers)
        data = res.get_json()
        assert len(data) == 1
        assert data[0]["title"] == "My survey"

    def test_unauthenticated_returns_401(self, client):
        res = client.get("/api/surveys")
        assert res.status_code == 401


# ════════════════════════════════════════════════════════════
# TESTS DE INTEGRACIÓN — POST /api/surveys
# ════════════════════════════════════════════════════════════

class TestCreateSurvey:

    def test_success_returns_201_with_id(self, client):
        headers = auth_headers(client)
        res = client.post("/api/surveys", headers=headers, json={
            "title": "¿Mejor lenguaje?",
            "description": "Vota tu favorito"
        })
        assert res.status_code == 201
        data = res.get_json()
        assert "id" in data
        assert isinstance(data["id"], int)

    def test_missing_title_returns_400(self, client):
        headers = auth_headers(client)
        res = client.post("/api/surveys", headers=headers, json={
            "description": "sin título"
        })
        assert res.status_code == 400
        assert "title" in res.get_json()["error"].lower()

    def test_title_too_long_returns_400(self, client):
        headers = auth_headers(client)
        res = client.post("/api/surveys", headers=headers, json={
            "title": "x" * 201
        })
        assert res.status_code == 400

    def test_created_by_is_taken_from_jwt_not_body(self, client):
        """IDOR: el campo created_by viene del JWT, no del cuerpo de la petición."""
        headers = auth_headers(client, username="alice")
        res = client.post("/api/surveys", headers=headers, json={
            "title": "Test IDOR",
            "created_by": 9999   # debe ser ignorado
        })
        assert res.status_code == 201
        survey_id = res.get_json()["id"]

        detail = client.get(f"/api/surveys/{survey_id}", headers=headers).get_json()
        assert detail["survey"]["created_by"] != 9999

    def test_unauthenticated_returns_401(self, client):
        res = client.post("/api/surveys", json={"title": "Test"})
        assert res.status_code == 401

    def test_survey_without_description_is_ok(self, client):
        headers = auth_headers(client)
        res = client.post("/api/surveys", headers=headers, json={"title": "Solo título"})
        assert res.status_code == 201


# ════════════════════════════════════════════════════════════
# TESTS DE INTEGRACIÓN — GET /api/surveys/<id>
# ════════════════════════════════════════════════════════════

class TestGetSurveyDetail:

    def test_returns_survey_with_questions_and_options(self, client):
        headers = auth_headers(client)

        # Crear encuesta
        res = client.post("/api/surveys", headers=headers, json={"title": "Q"})
        sid = res.get_json()["id"]

        # Añadir pregunta
        qres = client.post(f"/api/surveys/{sid}/questions", headers=headers,
                           json={"text": "¿Cuál prefieres?", "type": "single"})
        assert qres.status_code == 201
        qid = qres.get_json()["id"]

        # Añadir opción a la pregunta
        client.post(f"/api/questions/{qid}/options", headers=headers,
                    json={"text": "Opción A"})

        # Verificar estructura de respuesta
        detail = client.get(f"/api/surveys/{sid}", headers=headers).get_json()
        assert detail["survey"]["title"] == "Q"
        assert len(detail["questions"]) == 1
        assert len(detail["questions"][0]["options"]) == 1
        assert detail["questions"][0]["options"][0]["text"] == "Opción A"

    def test_nonexistent_survey_returns_404(self, client):
        headers = auth_headers(client)
        res = client.get("/api/surveys/9999", headers=headers)
        assert res.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        res = client.get("/api/surveys/1")
        assert res.status_code == 401


# ════════════════════════════════════════════════════════════
# TESTS DE INTEGRACIÓN — POST /api/surveys/<id>/questions
# ════════════════════════════════════════════════════════════

class TestAddQuestion:

    def _create_survey(self, client, headers):
        res = client.post("/api/surveys", headers=headers, json={"title": "Q"})
        return res.get_json()["id"]

    def test_success_returns_201(self, client):
        headers = auth_headers(client)
        sid = self._create_survey(client, headers)
        res = client.post(f"/api/surveys/{sid}/questions", headers=headers,
                          json={"text": "¿Cuál es tu lenguaje favorito?", "type": "single"})
        assert res.status_code == 201
        assert "id" in res.get_json()

    def test_missing_text_returns_400(self, client):
        headers = auth_headers(client)
        sid = self._create_survey(client, headers)
        res = client.post(f"/api/surveys/{sid}/questions", headers=headers,
                          json={"type": "single"})
        assert res.status_code == 400

    def test_invalid_type_returns_400(self, client):
        headers = auth_headers(client)
        sid = self._create_survey(client, headers)
        res = client.post(f"/api/surveys/{sid}/questions", headers=headers,
                          json={"text": "Pregunta", "type": "invalid"})
        assert res.status_code == 400

    def test_survey_not_found_returns_404(self, client):
        headers = auth_headers(client)
        res = client.post("/api/surveys/9999/questions", headers=headers,
                          json={"text": "Pregunta", "type": "single"})
        assert res.status_code == 404

    def test_non_owner_cannot_add_question(self, client):
        """IDOR: otro usuario no puede añadir preguntas a una encuesta ajena."""
        headers_alice = auth_headers(client, username="alice")
        headers_bob   = auth_headers(client, username="bob")
        sid = self._create_survey(client, headers_alice)

        res = client.post(f"/api/surveys/{sid}/questions", headers=headers_bob,
                          json={"text": "Intruso", "type": "single"})
        assert res.status_code == 403

    def test_unauthenticated_returns_401(self, client):
        res = client.post("/api/surveys/1/questions",
                          json={"text": "Pregunta", "type": "single"})
        assert res.status_code == 401


# ════════════════════════════════════════════════════════════
# TESTS DE INTEGRACIÓN — POST /api/questions/<id>/options
# ════════════════════════════════════════════════════════════

class TestAddOption:

    def _create_survey_and_question(self, client, headers):
        sid = client.post("/api/surveys", headers=headers,
                          json={"title": "Q"}).get_json()["id"]
        qid = client.post(f"/api/surveys/{sid}/questions", headers=headers,
                          json={"text": "¿Cuál?", "type": "single"}).get_json()["id"]
        return sid, qid

    def test_success_returns_201(self, client):
        headers = auth_headers(client)
        _, qid = self._create_survey_and_question(client, headers)
        res = client.post(f"/api/questions/{qid}/options", headers=headers,
                          json={"text": "Python"})
        assert res.status_code == 201

    def test_missing_option_text_returns_400(self, client):
        headers = auth_headers(client)
        _, qid = self._create_survey_and_question(client, headers)
        res = client.post(f"/api/questions/{qid}/options", headers=headers, json={})
        assert res.status_code == 400

    def test_option_text_too_long_returns_400(self, client):
        headers = auth_headers(client)
        _, qid = self._create_survey_and_question(client, headers)
        res = client.post(f"/api/questions/{qid}/options", headers=headers,
                          json={"text": "x" * 301})
        assert res.status_code == 400

    def test_question_not_found_returns_404(self, client):
        headers = auth_headers(client)
        res = client.post("/api/questions/9999/options", headers=headers,
                          json={"text": "X"})
        assert res.status_code == 404

    def test_non_owner_cannot_add_option(self, client):
        """IDOR: otro usuario no puede añadir opciones a preguntas ajenas."""
        headers_alice = auth_headers(client, username="alice")
        headers_bob   = auth_headers(client, username="bob")
        _, qid = self._create_survey_and_question(client, headers_alice)

        res = client.post(f"/api/questions/{qid}/options", headers=headers_bob,
                          json={"text": "Intruso"})
        assert res.status_code == 403

    def test_unauthenticated_returns_401(self, client):
        res = client.post("/api/questions/1/options", json={"text": "X"})
        assert res.status_code == 401
