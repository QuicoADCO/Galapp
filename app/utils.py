import os
import jwt
from functools import wraps
from flask import request, jsonify

SECRET = os.getenv("JWT_SECRET_KEY")


def generate_token(user):
    payload = {
        "id": user.id,
        "username": user.username,
        "role": user.role
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def token_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = request.headers.get("Authorization")

            if not token:
                return jsonify({"error": "Token missing"}), 401

            try:
                token = token.split(" ")[1]
                data = jwt.decode(token, SECRET, algorithms=["HS256"])
            except:
                return jsonify({"error": "Invalid token"}), 401

            if role and data["role"] != role:
                return jsonify({"error": "Unauthorized"}), 403

            return f(*args, **kwargs)

        return wrapper
    return decorator