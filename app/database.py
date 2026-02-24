import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    database = os.getenv("POSTGRES_DB")

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"postgresql://{user}:{password}@db:5432/{database}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)