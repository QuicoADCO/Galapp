from datetime import datetime, timezone
from app.database import db


class Survey(db.Model):
    __tablename__ = "surveys"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    options = db.relationship("SurveyOption", backref="survey", lazy=True, cascade="all, delete-orphan")
    votes = db.relationship("Vote", backref="survey", lazy=True, cascade="all, delete-orphan")


class SurveyOption(db.Model):
    __tablename__ = "survey_options"

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey("surveys.id"), nullable=False)
    option_text = db.Column(db.String(500), nullable=False)


class Vote(db.Model):
    __tablename__ = "votes"

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey("surveys.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey("survey_options.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint("survey_id", "user_id", name="uq_survey_user_vote"),
    )
