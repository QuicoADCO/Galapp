import os
from flask import Flask
from dotenv import load_dotenv

from app.database import init_db, db
from app.routes.auth import auth_bp
from app.routes.api import api_bp
from app.routes.frontend import frontend_bp

load_dotenv()

REQUIRED_ENV_VARS = [
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "SECRET_KEY",
    "JWT_SECRET_KEY"
]

for var in REQUIRED_ENV_VARS:
    if not os.getenv(var):
        raise RuntimeError(f"Missing required environment variable: {var}")


def create_app():

    app = Flask(__name__, template_folder="templates")

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

    # Database configuration from environment variables
    DB_USER = os.getenv("POSTGRES_USER")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    DB_HOST = os.getenv("POSTGRES_HOST")
    DB_PORT = os.getenv("POSTGRES_PORT")
    DB_NAME = os.getenv("POSTGRES_DB")

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    init_db(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(frontend_bp)

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)