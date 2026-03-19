"""
REST API Blueprint for Velostadt.

Authentication: POST /api/auth/login  →  returns a JWT token
Usage: pass token as  Authorization: Bearer <token>  header

Endpoints:
  POST /api/auth/login          – obtain JWT token
  GET  /api/fahrzeuge           – list vehicles (optional ?status= filter)
  GET  /api/fahrzeuge/<id>      – get single vehicle
  GET  /api/fahrten             – list rides (own rides for Benutzer, fleet for Anbieter)
"""

import datetime
from functools import wraps

import jwt
from flask import Blueprint, jsonify, request, current_app

from ..models import Anbieter, Benutzer, Fahrzeug, Fahrt

api_bp = Blueprint("api", __name__)


def token_required(f):
    """Function that validates the JWT Bearer token in the Authorization header."""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization-Header fehlt oder ungültig"}), 401

        token = auth_header[7:]  # strip "Bearer "
        try:
            data = jwt.decode(
                token, current_app.config["JWT_SECRET"], algorithms=["HS256"]
            )
            request.token_data = data
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token abgelaufen"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Ungültiger Token"}), 401

        return f(*args, **kwargs)

    return decorated


@api_bp.route("/auth/login", methods=["POST"])
def api_login():
    """
    Obtain a JWT token.

    Body (JSON):
      { "email": "...", "password": "...", "role": "benutzer"|"anbieter" }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON-Body erforderlich"}), 400

    email = data.get("email", "")
    password = data.get("password", "")
    role = data.get("role", "benutzer")

    user = None
    user_id = None
    if role == "anbieter":
        user = Anbieter.query.filter_by(e_mail=email).first()
        if user:
            user_id = user.anbieter_id
    else:
        user = Benutzer.query.filter_by(e_mail=email).first()
        if user:
            user_id = user.benutzer_id

    if not user or not user.check_password(password):
        return jsonify({"error": "Ungültige Anmeldedaten"}), 401

    token = jwt.encode(
        {
            "user_id": user_id,
            "role": role,
            "exp": datetime.datetime.now() + datetime.timedelta(hours=24),
        },
        current_app.config["JWT_SECRET"],
        algorithm="HS256",
    )

    return jsonify({"token": token, "role": role, "user_id": user_id})


@api_bp.route("/fahrzeuge", methods=["GET"])
@token_required
def api_fahrzeuge():
    """List all vehicles. Optional query param: ?status=verfuegbar|verliehen|in_wartung"""
    status_filter = request.args.get("status")
    query = Fahrzeug.query
    if status_filter:
        query = query.filter_by(status=status_filter)

    result = [_fahrzeug_to_dict(f) for f in query.all()]
    return jsonify(result)


@api_bp.route("/fahrzeuge/<int:id>", methods=["GET"])
@token_required
def api_fahrzeug_detail(id):
    """Get details for a single vehicle."""
    from .. import db

    fahrzeug = db.get_or_404(Fahrzeug, id)
    return jsonify(_fahrzeug_to_dict(fahrzeug))


@api_bp.route("/fahrten", methods=["GET"])
@token_required
def api_fahrten():
    """
    List rides.
    - Benutzer: sees their own rides.
    - Anbieter: sees rides on their vehicles.
    """
    data = request.token_data

    if data["role"] == "benutzer":
        fahrten = (
            Fahrt.query.filter_by(benutzer_id=data["user_id"])
            .order_by(Fahrt.startzeit.desc())
            .all()
        )
    else:
        vehicle_ids = [
            v.fahrzeug_id
            for v in Fahrzeug.query.filter_by(anbieter_id=data["user_id"]).all()
        ]
        fahrten = (
            Fahrt.query.filter(Fahrt.fahrzeug_id.in_(vehicle_ids))
            .order_by(Fahrt.startzeit.desc())
            .all()
        )

    result = [_fahrt_to_dict(f) for f in fahrten]
    return jsonify(result)


# ── helpers ──────────────────────────────────────────────────────────────────

def _fahrzeug_to_dict(f):
    return {
        "fahrzeug_id": f.fahrzeug_id,
        "typ": f.fahrzeugtyp.bezeichnung,
        "status": f.status,
        "akku_prozent": f.akku_prozent,
        "gps_lat": float(f.gps_lat) if f.gps_lat is not None else None,
        "gps_long": float(f.gps_long) if f.gps_long is not None else None,
        "qr_code": f.qr_code,
        "basispreis": float(f.fahrzeugtyp.basispreis),
        "preis_pro_min": float(f.fahrzeugtyp.preis_pro_min),
    }


def _fahrt_to_dict(f):
    return {
        "fahrt_id": f.fahrt_id,
        "fahrzeug_id": f.fahrzeug_id,
        "startzeit": f.startzeit.isoformat(),
        "endzeit": f.endzeit.isoformat() if f.endzeit else None,
        "kilometer": float(f.kilometer),
        "preis": float(f.preis),
    }
