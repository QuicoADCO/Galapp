"""
Script para crear el usuario administrador inicial.
Se ejecuta automáticamente en el entrypoint del contenedor (idempotente).

La contraseña se toma de la variable de entorno ADMIN_PASSWORD.
Si no está definida, se usa 'Admin1234!' como valor por defecto
(solo recomendado para desarrollo local).
"""
import os
import logging
from werkzeug.security import generate_password_hash
from app.main import create_app
from app.database import db
from app.models.user import User

log = logging.getLogger(__name__)

_DEFAULT_PASSWORD = "Admin1234!"


def seed_admin(username="admin", email="admin@galapp.com", password=None):
    if password is None:
        password = os.getenv("ADMIN_PASSWORD", _DEFAULT_PASSWORD)

    if password == _DEFAULT_PASSWORD:
        log.warning(
            "ADMIN_PASSWORD no definida — usando contraseña por defecto. "
            "Define ADMIN_PASSWORD en .env para producción."
        )

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
    print("Usuario admin creado:")
    print(f"  Username : {username}")
    print(f"  Email    : {email}")
    print(f"  Password : {password}")
    print("  Role     : admin")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed_admin()
