from flask import Blueprint, jsonify, request

from ..auth import signup_user, login_user


bp = Blueprint("auth", __name__)


@bp.route("/auth/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    user, token = signup_user(email, password)
    if not user:
        return jsonify({"error": token or "Signup failed"}), 400
    return jsonify({"token": token, "user": {"id": user["id"], "email": user["email"]}}), 200


@bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    user, token = login_user(email, password)
    if not user:
        return jsonify({"error": token or "Login failed"}), 401
    return jsonify({"token": token, "user": {"id": user["id"], "email": user["email"]}}), 200