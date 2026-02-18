import os
from flask import Flask, jsonify, render_template, request, redirect, url_for
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

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

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

# ⚠️ Simulación de base de datos temporal
users = {}


@app.route("/")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = users.get(email)

        if user and check_password_hash(user["password"], password):
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match")

        if email in users:
            return render_template("register.html", error="User already exists")

        hashed_password = generate_password_hash(password)

        users[email] = {
            "password": hashed_password
        }

        return render_template("register.html", success="Account created successfully")

    return render_template("register.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
