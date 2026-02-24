from flask import Blueprint, render_template

frontend_bp = Blueprint("frontend", __name__)


@frontend_bp.route("/")
def home():
    return render_template("login.html")


@frontend_bp.route("/login")
def login_view():
    return render_template("login.html")


@frontend_bp.route("/register")
def register_view():
    return render_template("register.html")


@frontend_bp.route("/dashboard")
def dashboard_view():
    return render_template("dashboard.html")