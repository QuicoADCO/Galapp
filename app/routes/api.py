from flask import Blueprint, request, jsonify, g
from app.database import db
from app.models.survey import Survey, SurveyOption, Vote
from app.utils import token_required

api_bp = Blueprint("api", __name__, url_prefix="/api")


# -----------------------
# HEALTH CHECK
# -----------------------
@api_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


# -----------------------
# GET ALL SURVEYS
# -----------------------
@api_bp.route("/surveys", methods=["GET"])
@token_required()
def get_surveys():
    surveys = Survey.query.all()
    result = [
        {
            "id": s.id,
            "title": s.title,
            "description": s.description,
            "created_by": s.created_by,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in surveys
    ]
    return jsonify(result), 200


# -----------------------
# CREATE SURVEY
# -----------------------
@api_bp.route("/surveys", methods=["POST"])
@token_required()
def create_survey():
    data = request.get_json()

    title = data.get("title", "").strip()
    description = data.get("description", "").strip()

    if not title:
        return jsonify({"error": "Title is required"}), 400
    if len(title) > 200:
        return jsonify({"error": "Title too long (max 200 chars)"}), 400

    created_by = g.current_user["id"]
    survey = Survey(title=title, description=description, created_by=created_by)
    db.session.add(survey)
    db.session.commit()

    return jsonify({"message": "Survey created", "id": survey.id}), 201


# -----------------------
# GET SURVEY WITH OPTIONS
# -----------------------
@api_bp.route("/surveys/<int:survey_id>", methods=["GET"])
@token_required()
def get_survey(survey_id):
    survey = Survey.query.get(survey_id)

    if not survey:
        return jsonify({"error": "Survey not found"}), 404

    options = [
        {"id": o.id, "option_text": o.option_text}
        for o in survey.options
    ]

    return jsonify({
        "survey": {
            "id": survey.id,
            "title": survey.title,
            "description": survey.description,
            "created_by": survey.created_by,
        },
        "options": options,
    }), 200


# -----------------------
# ADD OPTION TO SURVEY
# -----------------------
@api_bp.route("/surveys/<int:survey_id>/options", methods=["POST"])
@token_required()
def add_option(survey_id):
    survey = Survey.query.get(survey_id)
    if not survey:
        return jsonify({"error": "Survey not found"}), 404

    data = request.get_json()
    option_text = data.get("option_text", "").strip()

    if not option_text:
        return jsonify({"error": "Option text required"}), 400
    if len(option_text) > 300:
        return jsonify({"error": "Option text too long (max 300 chars)"}), 400

    option = SurveyOption(survey_id=survey_id, option_text=option_text)
    db.session.add(option)
    db.session.commit()

    return jsonify({"message": "Option added", "id": option.id}), 201


# -----------------------
# VOTE
# -----------------------
@api_bp.route("/votes", methods=["POST"])
@token_required()
def vote():
    data = request.get_json()

    survey_id = data.get("survey_id")
    option_id = data.get("option_id")
    user_id = g.current_user["id"]

    if not all([survey_id, option_id]):
        return jsonify({"error": "Missing fields"}), 400

    existing_vote = Vote.query.filter_by(survey_id=survey_id, user_id=user_id).first()
    if existing_vote:
        return jsonify({"error": "User already voted"}), 400

    new_vote = Vote(survey_id=survey_id, user_id=user_id, option_id=option_id)
    db.session.add(new_vote)
    db.session.commit()

    return jsonify({"message": "Vote recorded"}), 201
