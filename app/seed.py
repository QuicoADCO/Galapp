"""
Script para crear el usuario administrador inicial.

Ejecutar desde el contenedor web:
    docker compose exec web python app/seed.py
"""
from werkzeug.security import generate_password_hash
from app.main import create_app
from app.database import db
from app.models.user import User


def seed_admin(username="admin", email="admin@galapp.com", password="Admin1234!"):
    existing = User.query.filter_by(username=username).first()
    if existing:
        print(f"El usuario '{username}' ya existe.")
        return

    admin = User(
        username=username,
        email=email,
        password=generate_password_hash(password),
        role="admin",
    )
    db.session.add(admin)
    db.session.commit()
    print(f"Usuario admin creado:")
    print(f"  Username : {username}")
    print(f"  Email    : {email}")
    print(f"  Password : {password}")
    print(f"  Role     : admin")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed_admin()
