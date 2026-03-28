import os
import logging
import traceback
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.database import init_db, db
from app.routes.auth import auth_bp
from app.routes.api import api_bp
from app.routes.frontend import frontend_bp

limiter = Limiter(key_func=get_remote_address, default_limits=[])

load_dotenv()

REQUIRED_ENV_VARS = [
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "SECRET_KEY",
    "JWT_SECRET_KEY"
]

for var in REQUIRED_ENV_VARS:
    if not os.getenv(var):
        raise RuntimeError(f"Missing required environment variable: {var}")


def create_app(test_config=None):

    app = Flask(__name__, template_folder="templates")

    # Structured logging to stdout (readable via `docker compose logs web`)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app.logger.setLevel(logging.INFO)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # Enforce upload size limit at Flask level (belt-and-suspenders with nginx)
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB

    if test_config:
        app.config.update(test_config)
    else:
        DB_USER = os.getenv("POSTGRES_USER")
        DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
        DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
        DB_PORT = os.getenv("POSTGRES_PORT", "5432")
        DB_NAME = os.getenv("POSTGRES_DB")

        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )

    init_db(app)
    limiter.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(frontend_bp)

    # Import models so SQLAlchemy registers them before create_all
    from app.models import user, survey  # noqa: F401

    # Apply rate limits to auth and sensitive API endpoints
    limiter.limit("10 per minute")(app.view_functions["auth.login"])
    limiter.limit("5 per minute")(app.view_functions["auth.register"])
    limiter.limit("20 per minute")(app.view_functions["api.create_survey"])
    limiter.limit("60 per minute")(app.view_functions["api.vote"])
    # Votos anónimos — más restrictivo para evitar flood sin autenticación
    limiter.limit("30 per minute")(app.view_functions["api.public_vote"])
    # Listados — la consulta participated hace un JOIN; se limita para evitar abuso
    limiter.limit("60 per minute")(app.view_functions["api.get_surveys"])
    limiter.limit("30 per minute")(app.view_functions["api.participated_surveys"])

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(413)
    def payload_too_large(e):
        return jsonify({"error": "Payload too large (max 5 MB)"}), 413

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({"error": "Too many requests, please try again later"}), 429

    @app.errorhandler(500)
    def internal_error(e):
        # Log the real error with traceback — never expose it to the client
        app.logger.error(
            "500 on %s %s\n%s",
            request.method,
            request.path,
            traceback.format_exc(),
        )
        return jsonify({"error": "An internal error occurred"}), 500

    if not test_config:
        with app.app_context():
            db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8000)
