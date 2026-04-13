import os
import uuid
import logging
from flask import Blueprint, request, jsonify, g, current_app
from sqlalchemy.exc import SQLAlchemyError
from app.database import db
import re
from app.models.survey import Survey, Question, QuestionOption, Vote, AnonVote
from app.utils import token_required

log = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
MAX_IMAGE_BYTES    = 4 * 1024 * 1024  # 4 MB

# Magic-byte signatures for allowed image types (OWASP file upload validation)
_MAGIC = {
    b"\xff\xd8\xff":           "jpg",   # JPEG
    b"\x89PNG\r\n\x1a\n":     "png",   # PNG
    b"GIF87a":                 "gif",   # GIF87a
    b"GIF89a":                 "gif",   # GIF89a
    b"RIFF":                   "webp",  # WEBP (bytes 0-3; bytes 8-11 are "WEBP")
}


def _check_magic(file) -> bool:
    """Return True if the first bytes match a known image signature."""
    header = file.read(12)
    file.seek(0)
    for magic, _ in _MAGIC.items():
        if header.startswith(magic):
            # Extra check for WEBP: bytes 8-11 must be b"WEBP"
            if magic == b"RIFF":
                return header[8:12] == b"WEBP"
            return True
    return False


api_bp = Blueprint("api", __name__, url_prefix="/api")


# ── helpers ───────────────────────────────────────────────────────────────────

def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _save_image(file):
    """Validate and save an uploaded image. Returns the stored filename or raises ValueError."""
    # 1. Extension whitelist
    if not _allowed_file(file.filename):
        raise ValueError("Image type not allowed. Use JPG, PNG, GIF or WEBP.")
    # 2. Size limit
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_IMAGE_BYTES:
        raise ValueError("Image exceeds the 4 MB size limit.")
    # 3. Magic-byte validation — prevents disguised executables
    if not _check_magic(file):
        raise ValueError("File content does not match an allowed image type.")
    # 4. Store with a random UUID name (no user-controlled characters in path)
    # os.path.basename() strips directory traversal (e.g. "../../evil.jpg" → "evil.jpg")
    safe_name  = os.path.basename(file.filename)
    ext        = safe_name.rsplit(".", 1)[1].lower()
    filename   = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = os.path.join(current_app.root_path, "static", "uploads")
    try:
        os.makedirs(upload_dir, exist_ok=True)
        file.save(os.path.join(upload_dir, filename))
    except OSError as e:
        log.exception("Could not save uploaded file to %s", upload_dir)
        raise ValueError(f"No se pudo guardar la imagen: {e.strerror}") from e
    return filename


def _img_url(filename):
    # os.path.basename() strips any path traversal components stored in DB
    if not filename:
        return None
    safe = os.path.basename(filename)
    return f"/static/uploads/{safe}" if safe else None


def _question_dict(q):
    return {
        "id":    q.id,
        "text":  q.text,
        "type":  q.question_type,
        "order": q.order,
        "options": [
            {
                "id":        o.id,
                "text":      o.text,
                "image_url": _img_url(o.image_filename),
            }
            for o in q.options
        ],
    }


# ── HEALTH ────────────────────────────────────────────────────────────────────

@api_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


# ── SURVEYS ───────────────────────────────────────────────────────────────────

@api_bp.route("/surveys", methods=["GET"])
@token_required()
def get_surveys():
    """Devuelve solo las encuestas creadas por el usuario autenticado."""
    user_id = g.current_user["id"]
    surveys = Survey.query.filter_by(created_by=user_id).all()
    return jsonify([
        {
            "id":             s.id,
            "title":          s.title,
            "description":    s.description,
            "image_url":      _img_url(s.image_filename),
            "question_count": len(s.questions),
            "created_by":     s.created_by,
            "created_at":     s.created_at.isoformat() if s.created_at else None,
        }
        for s in surveys
    ]), 200


@api_bp.route("/surveys/participated", methods=["GET"])
@token_required()
def participated_surveys():
    """Encuestas en las que el usuario ha votado pero no creó."""
    user_id = g.current_user["id"]
    # Subquery: IDs de encuestas donde el usuario tiene algún voto
    voted_ids = (
        db.session.query(Question.survey_id)
        .join(Vote, Vote.question_id == Question.id)
        .filter(Vote.user_id == user_id)
        .distinct()
        .subquery()
    )
    surveys = Survey.query.filter(
        Survey.id.in_(voted_ids),
        Survey.created_by != user_id,
    ).all()
    # created_by se omite intencionalmente: el usuario no necesita saber
    # el ID interno del creador de encuestas ajenas.
    return jsonify([
        {
            "id":             s.id,
            "title":          s.title,
            "description":    s.description,
            "image_url":      _img_url(s.image_filename),
            "question_count": len(s.questions),
            "created_at":     s.created_at.isoformat() if s.created_at else None,
        }
        for s in surveys
    ]), 200


@api_bp.route("/surveys", methods=["POST"])
@token_required()
def create_survey():
    is_multipart = request.content_type and "multipart/form-data" in request.content_type
    if is_multipart:
        title       = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        image_file  = request.files.get("image")
    else:
        data        = request.get_json(silent=True) or {}
        title       = data.get("title", "").strip()
        description = data.get("description", "").strip()
        image_file  = None

    if not title:
        return jsonify({"error": "Title is required"}), 400
    if len(title) > 200:
        return jsonify({"error": "Title too long (max 200 chars)"}), 400

    image_filename = None
    if image_file and image_file.filename:
        try:
            image_filename = _save_image(image_file)
        except (ValueError, OSError) as e:
            return jsonify({"error": str(e)}), 400

    survey = Survey(
        title=title,
        description=description,
        image_filename=image_filename,
        created_by=g.current_user["id"],
    )
    db.session.add(survey)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        log.exception("Error creating survey")
        return jsonify({"error": "Database error creating survey"}), 500

    return jsonify({"message": "Survey created", "id": survey.id,
                    "image_url": _img_url(image_filename)}), 201


@api_bp.route("/surveys/<int:survey_id>", methods=["GET"])
@token_required()
def get_survey(survey_id):
    survey = db.session.get(Survey, survey_id)
    if not survey:
        return jsonify({"error": "Survey not found"}), 404

    return jsonify({
        "survey": {
            "id":          survey.id,
            "title":       survey.title,
            "description": survey.description,
            "image_url":   _img_url(survey.image_filename),
            "created_by":  survey.created_by,
        },
        "questions": [_question_dict(q) for q in survey.questions],
    }), 200


# ── QUESTIONS ─────────────────────────────────────────────────────────────────

@api_bp.route("/surveys/<int:survey_id>/questions", methods=["POST"])
@token_required()
def add_question(survey_id):
    survey = db.session.get(Survey, survey_id)
    if not survey:
        return jsonify({"error": "Survey not found"}), 404
    # IDOR prevention: only the survey creator can add questions
    if survey.created_by != g.current_user["id"]:
        return jsonify({"error": "No autorizado"}), 403

    data  = request.get_json(silent=True) or {}
    text  = (data.get("text") or "").strip()
    qtype = data.get("type", "single")

    if not text:
        return jsonify({"error": "Question text is required"}), 400
    if len(text) > 500:
        return jsonify({"error": "Question text too long (max 500 chars)"}), 400
    if qtype not in ("single", "multiple"):
        return jsonify({"error": "type must be 'single' or 'multiple'"}), 400

    order    = len(survey.questions)
    question = Question(survey_id=survey_id, text=text, question_type=qtype, order=order)
    db.session.add(question)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        log.exception("Error adding question to survey %s", survey_id)
        return jsonify({"error": "Database error adding question"}), 500

    return jsonify({"message": "Question added", "id": question.id,
                    "order": question.order}), 201


# ── OPTIONS ───────────────────────────────────────────────────────────────────

@api_bp.route("/questions/<int:question_id>/options", methods=["POST"])
@token_required()
def add_option(question_id):
    question = db.session.get(Question, question_id)
    if not question:
        return jsonify({"error": "Question not found"}), 404
    # IDOR prevention: only the survey creator can add options
    parent_survey = db.session.get(Survey, question.survey_id)
    if not parent_survey or parent_survey.created_by != g.current_user["id"]:
        return jsonify({"error": "No autorizado"}), 403

    is_multipart = request.content_type and "multipart/form-data" in request.content_type
    if is_multipart:
        text       = (request.form.get("text") or "").strip()
        image_file = request.files.get("image")
    else:
        data       = request.get_json(silent=True) or {}
        text       = (data.get("text") or "").strip()
        image_file = None

    if not text:
        return jsonify({"error": "Option text is required"}), 400
    if len(text) > 300:
        return jsonify({"error": "Option text too long (max 300 chars)"}), 400

    image_filename = None
    if image_file and image_file.filename:
        try:
            image_filename = _save_image(image_file)
        except (ValueError, OSError) as e:
            return jsonify({"error": str(e)}), 400

    option = QuestionOption(question_id=question_id, text=text,
                            image_filename=image_filename)
    db.session.add(option)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        log.exception("Error adding option to question %s", question_id)
        return jsonify({"error": "Database error adding option"}), 500

    return jsonify({"message": "Option added", "id": option.id,
                    "image_url": _img_url(image_filename)}), 201


# ── VOTES ─────────────────────────────────────────────────────────────────────

@api_bp.route("/votes", methods=["POST"])
@token_required()
def vote():
    data        = request.get_json(silent=True) or {}
    question_id = data.get("question_id")
    option_id   = data.get("option_id")
    user_id     = g.current_user["id"]

    if not question_id or not option_id:
        return jsonify({"error": "Missing fields"}), 400

    question = db.session.get(Question, question_id)
    if not question:
        return jsonify({"error": "Question not found"}), 404

    # Vote integrity: verify the option belongs to this question (prevents IDOR on votes)
    option = db.session.get(QuestionOption, option_id)
    if not option or option.question_id != question_id:
        return jsonify({"error": "Opción no válida para esta pregunta"}), 400

    # Single choice: sólo un voto por pregunta
    if question.question_type == "single":
        existing = Vote.query.filter_by(question_id=question_id, user_id=user_id).first()
        if existing:
            return jsonify({"error": "User already voted on this question"}), 400

    # Multiple choice: no votar la misma opción dos veces
    existing = Vote.query.filter_by(
        question_id=question_id, option_id=option_id, user_id=user_id
    ).first()
    if existing:
        return jsonify({"error": "User already voted this option"}), 400

    db.session.add(Vote(question_id=question_id, option_id=option_id, user_id=user_id))
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        log.exception("Error recording vote q=%s opt=%s user=%s", question_id, option_id, user_id)
        return jsonify({"error": "Database error recording vote"}), 500

    return jsonify({"message": "Vote recorded"}), 201


@api_bp.route("/surveys/<int:survey_id>/my-votes", methods=["GET"])
@token_required()
def my_votes(survey_id):
    """Devuelve los votos del usuario actual en esta encuesta."""
    survey = db.session.get(Survey, survey_id)
    if not survey:
        return jsonify({"error": "Survey not found"}), 404

    user_id  = g.current_user["id"]
    q_ids    = [q.id for q in survey.questions]
    votes    = Vote.query.filter(
        Vote.question_id.in_(q_ids),
        Vote.user_id == user_id,
    ).all()

    return jsonify([{"question_id": v.question_id, "option_id": v.option_id}
                    for v in votes]), 200


@api_bp.route("/surveys/<int:survey_id>/qr-code", methods=["GET"])
@token_required()
def survey_qr_code(survey_id):
    """Genera un QR code SVG con el enlace de votación de la encuesta."""
    import io
    import qrcode
    import qrcode.image.svg
    from flask import Response

    survey = db.session.get(Survey, survey_id)
    if not survey:
        return jsonify({"error": "Survey not found"}), 404

    # Construir la URL usando el host real de la petición (forwarded por nginx)
    vote_url = f"{request.scheme}://{request.host}/encuesta/{survey_id}"

    factory = qrcode.image.svg.SvgPathFillImage
    img = qrcode.make(vote_url, image_factory=factory, box_size=10, border=2)

    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)

    return Response(
        buf.getvalue(),
        mimetype="image/svg+xml",
        headers={"Cache-Control": "no-store"},
    )


@api_bp.route("/surveys/<int:survey_id>/results", methods=["GET"])
@token_required()
def survey_results(survey_id):
    """Resultados con conteo de votos por opción."""
    survey = db.session.get(Survey, survey_id)
    if not survey:
        return jsonify({"error": "Survey not found"}), 404

    questions = []
    for q in survey.questions:
        reg_total  = Vote.query.filter_by(question_id=q.id).count()
        anon_total = AnonVote.query.filter_by(question_id=q.id).count()
        total      = reg_total + anon_total
        options = []
        for o in q.options:
            reg_count  = Vote.query.filter_by(option_id=o.id).count()
            anon_count = AnonVote.query.filter_by(option_id=o.id).count()
            count = reg_count + anon_count
            options.append({
                "id":         o.id,
                "text":       o.text,
                "image_url":  _img_url(o.image_filename),
                "votes":      count,
                "percentage": round(count / total * 100, 1) if total else 0,
            })
        questions.append({
            "id":          q.id,
            "text":        q.text,
            "type":        q.question_type,
            "total_votes": total,
            "options":     options,
        })

    return jsonify({"questions": questions}), 200


# ── ENDPOINTS PÚBLICOS (sin JWT) — votación anónima por enlace compartido ─────

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)


def _voter_token():
    """Extrae y valida el voter_token de la cabecera X-Voter-Token."""
    token = request.headers.get("X-Voter-Token", "").strip().lower()
    if not _UUID_RE.match(token):
        return None
    return token


@api_bp.route("/public/surveys/<int:survey_id>", methods=["GET"])
def public_survey(survey_id):
    """Devuelve datos de la encuesta sin requerir autenticación."""
    survey = db.session.get(Survey, survey_id)
    if not survey:
        return jsonify({"error": "Survey not found"}), 404

    questions = []
    for q in survey.questions:
        options = [
            {
                "id":        o.id,
                "text":      o.text,
                "image_url": _img_url(o.image_filename),
            }
            for o in q.options
        ]
        questions.append({
            "id":    q.id,
            "text":  q.text,
            "type":  q.question_type,
            "order": q.order,
            "options": options,
        })

    return jsonify({
        "survey": {
            "id":          survey.id,
            "title":       survey.title,
            "description": survey.description,
            "image_url":   _img_url(survey.image_filename),
        },
        "questions": questions,
    }), 200


@api_bp.route("/public/surveys/<int:survey_id>/my-votes", methods=["GET"])
def public_my_votes(survey_id):
    """Devuelve los votos previos del votante anónimo en esta encuesta."""
    token = _voter_token()
    if not token:
        return jsonify([]), 200

    survey = db.session.get(Survey, survey_id)
    if not survey:
        return jsonify([]), 200

    q_ids = [q.id for q in survey.questions]
    votes = AnonVote.query.filter(
        AnonVote.voter_token == token,
        AnonVote.question_id.in_(q_ids),
    ).all()

    return jsonify([
        {"question_id": v.question_id, "option_id": v.option_id}
        for v in votes
    ]), 200


@api_bp.route("/public/surveys/<int:survey_id>/vote", methods=["POST"])
def public_vote(survey_id):
    """Registra un voto anónimo. Requiere X-Voter-Token (UUID)."""
    token = _voter_token()
    if not token:
        return jsonify({"error": "Voter token inválido o ausente"}), 400

    data        = request.get_json(silent=True) or {}
    question_id = data.get("question_id")
    option_id   = data.get("option_id")

    if not question_id or not option_id:
        return jsonify({"error": "question_id y option_id son requeridos"}), 400

    survey = db.session.get(Survey, survey_id)
    if not survey:
        return jsonify({"error": "Survey not found"}), 404

    question = db.session.get(Question, question_id)
    if not question or question.survey_id != survey_id:
        return jsonify({"error": "Pregunta no válida para esta encuesta"}), 400

    option = db.session.get(QuestionOption, option_id)
    if not option or option.question_id != question_id:
        return jsonify({"error": "Opción no válida para esta pregunta"}), 400

    # Unicidad: un token solo puede votar una vez por pregunta (tipo single)
    if question.question_type == "single":
        existing = AnonVote.query.filter_by(
            voter_token=token, question_id=question_id
        ).first()
        if existing:
            return jsonify({"error": "Ya votaste en esta pregunta"}), 400

    db.session.add(AnonVote(
        voter_token=token,
        question_id=question_id,
        option_id=option_id,
    ))
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        log.exception("Error recording anon vote q=%s opt=%s token=%s",
                      question_id, option_id, token)
        return jsonify({"error": "Error al registrar el voto"}), 500

    return jsonify({"message": "Vote recorded"}), 201
