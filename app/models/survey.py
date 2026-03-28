from datetime import datetime, timezone
from app.database import db


class Survey(db.Model):
    __tablename__ = "surveys"

    id             = db.Column(db.Integer, primary_key=True)
    title          = db.Column(db.String(200), nullable=False)
    description    = db.Column(db.Text)
    image_filename = db.Column(db.String(260), nullable=True)
    created_by     = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at     = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    questions = db.relationship(
        "Question", backref="survey", lazy=True,
        cascade="all, delete-orphan",
        order_by="Question.order",
    )


class Question(db.Model):
    __tablename__ = "questions"

    id            = db.Column(db.Integer, primary_key=True)
    survey_id     = db.Column(db.Integer, db.ForeignKey("surveys.id"), nullable=False)
    text          = db.Column(db.String(500), nullable=False)
    # "single" → radio (one answer)  |  "multiple" → checkboxes (many answers)
    question_type = db.Column(db.String(20), nullable=False, default="single")
    order         = db.Column(db.Integer, nullable=False, default=0)

    options = db.relationship(
        "QuestionOption", backref="question", lazy=True,
        cascade="all, delete-orphan",
    )
    votes = db.relationship(
        "Vote", backref="question", lazy=True,
        cascade="all, delete-orphan",
    )


class QuestionOption(db.Model):
    __tablename__ = "question_options"

    id             = db.Column(db.Integer, primary_key=True)
    question_id    = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    text           = db.Column(db.String(300), nullable=False)
    image_filename = db.Column(db.String(260), nullable=True)

    votes = db.relationship("Vote", backref="option", lazy=True, cascade="all, delete-orphan")


class Vote(db.Model):
    __tablename__ = "votes"

    id          = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    option_id   = db.Column(db.Integer, db.ForeignKey("question_options.id"), nullable=False)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        # Evita que el mismo usuario vote dos veces la misma opción
        db.UniqueConstraint("question_id", "option_id", "user_id", name="uq_question_option_user"),
    )


class AnonVote(db.Model):
    """Votos anónimos de personas que reciben el enlace compartido.

    Se identifican por un voter_token UUID generado en el cliente y almacenado
    en localStorage. No requieren registro ni autenticación.
    """
    __tablename__ = "anon_votes"

    id           = db.Column(db.Integer, primary_key=True)
    voter_token  = db.Column(db.String(36), nullable=False, index=True)
    question_id  = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    option_id    = db.Column(db.Integer, db.ForeignKey("question_options.id"), nullable=False)
    created_at   = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        # Un votante anónimo solo puede votar una vez por pregunta
        db.UniqueConstraint("voter_token", "question_id", name="uq_anon_voter_question"),
    )
