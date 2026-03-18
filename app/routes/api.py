from flask import Blueprint, request, jsonify
import sqlite3

api_bp = Blueprint("api", __name__, url_prefix="/api")


# -----------------------
# DB helper
# -----------------------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


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
def get_surveys():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM surveys")
    surveys = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return jsonify(surveys), 200


# -----------------------
# CREATE SURVEY
# -----------------------
@api_bp.route("/surveys", methods=["POST"])
def create_survey():
    data = request.get_json()

    title = data.get("title")
    description = data.get("description")
    created_by = data.get("created_by")

    if not title:
        return jsonify({"error": "Title is required"}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO surveys (title, description, created_by) VALUES (?, ?, ?)",
        (title, description, created_by),
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Survey created"}), 201


# -----------------------
# ADD OPTION TO SURVEY
# -----------------------
@api_bp.route("/surveys/<int:survey_id>/options", methods=["POST"])
def add_option(survey_id):
    data = request.get_json()
    option_text = data.get("option_text")

    if not option_text:
        return jsonify({"error": "Option text required"}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO survey_options (survey_id, option_text) VALUES (?, ?)",
        (survey_id, option_text),
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Option added"}), 201


# -----------------------
# GET SURVEY WITH OPTIONS
# -----------------------
@api_bp.route("/surveys/<int:survey_id>", methods=["GET"])
def get_survey(survey_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,))
    survey = cursor.fetchone()

    if not survey:
        return jsonify({"error": "Survey not found"}), 404

    cursor.execute(
        "SELECT * FROM survey_options WHERE survey_id = ?", (survey_id,)
    )
    options = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        "survey": dict(survey),
        "options": options
    }), 200


# -----------------------
# VOTE
# -----------------------
@api_bp.route("/votes", methods=["POST"])
def vote():
    data = request.get_json()

    survey_id = data.get("survey_id")
    user_id = data.get("user_id")
    option_id = data.get("option_id")

    if not all([survey_id, user_id, option_id]):
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db()
    cursor = conn.cursor()

    # ❗ evitar votos duplicados
    cursor.execute(
        "SELECT * FROM votes WHERE survey_id = ? AND user_id = ?",
        (survey_id, user_id),
    )
    existing_vote = cursor.fetchone()

    if existing_vote:
        conn.close()
        return jsonify({"error": "User already voted"}), 400

    cursor.execute(
        "INSERT INTO votes (survey_id, user_id, option_id) VALUES (?, ?, ?)",
        (survey_id, user_id, option_id),
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Vote recorded"}), 201