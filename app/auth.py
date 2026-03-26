import os
import functools
from datetime import datetime, timedelta, timezone

import jwt
from flask import request, jsonify, g

from app.models import Admin

JWT_ALGORITHM = "HS256"
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "480"))  # 8 hours


def _get_jwt_secret():
    # Prefer FLASK_SECRET_KEY / SECRET_KEY
    secret = os.getenv("FLASK_SECRET_KEY") or os.getenv("SECRET_KEY")
    if not secret:
        # Fail safe: you MUST set this in env for real deployments
        secret = "dev-insecure-secret-change-me"
    return secret


def create_access_token(admin: Admin):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(admin.id),
        "username": admin.username,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_EXPIRES_MINUTES)).timestamp()),
    }
    token = jwt.encode(payload, _get_jwt_secret(), algorithm=JWT_ALGORITHM)
    return token


def _extract_bearer_token():
    auth = request.headers.get("Authorization", "")
    if not auth:
        return None
    parts = auth.split(" ", 1)
    if len(parts) != 2:
        return None
    scheme, token = parts[0].strip(), parts[1].strip()
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def decode_access_token(token: str):
    payload = jwt.decode(token, _get_jwt_secret(), algorithms=[JWT_ALGORITHM])
    return payload


def login_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        token = _extract_bearer_token()
        if not token:
            return jsonify({"success": False, "error": "Missing Authorization token"}), 401

        try:
            payload = decode_access_token(token)
            admin_id = int(payload.get("sub"))
        except Exception:
            return jsonify({"success": False, "error": "Invalid or expired token"}), 401

        admin = Admin.query.get(admin_id)
        if not admin:
            return jsonify({"success": False, "error": "Invalid token user"}), 401

        # Store current user for route handlers
        g.current_admin = admin
        return fn(*args, **kwargs)

    return wrapper


def admin_required(fn):
    """
    Ensures:
      - token is valid
      - admin exists
      - admin is active (approved)
    """
    @functools.wraps(fn)
    @login_required
    def wrapper(*args, **kwargs):
        admin = getattr(g, "current_admin", None)
        if not admin:
            return jsonify({"success": False, "error": "Unauthorized"}), 401

        if not admin.is_active:
            return jsonify({"success": False, "error": "Account not approved"}), 403

        return fn(*args, **kwargs)

    return wrapper