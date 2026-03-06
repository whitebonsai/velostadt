import uuid
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import Fahrzeug, Fahrzeugtyp
from .. import db

fahrzeuge_bp = Blueprint("fahrzeuge", __name__)


def anbieter_required(f):
    """Decorator that restricts a route to logged-in Anbieter users."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "anbieter":
            flash("Dieser Bereich ist nur für Anbieter zugänglich.", "danger")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)

    return decorated


@fahrzeuge_bp.route("/meine-fahrzeuge")
@login_required
@anbieter_required
def meine_fahrzeuge():
    fahrzeuge = Fahrzeug.query.filter_by(
        anbieter_id=current_user.anbieter_id
    ).all()
    return render_template("fahrzeuge/list.html", fahrzeuge=fahrzeuge)


@fahrzeuge_bp.route("/fahrzeuge/neu", methods=["GET", "POST"])
@login_required
@anbieter_required
def neu():
    typen = Fahrzeugtyp.query.all()

    if request.method == "POST":
        fahrzeugtyp_id = request.form.get("fahrzeugtyp_id")
        akku_prozent = request.form.get("akku_prozent", 100)
        status = request.form.get("status", "verfuegbar")
        gps_lat = request.form.get("gps_lat") or None
        gps_long = request.form.get("gps_long") or None

        if not fahrzeugtyp_id:
            flash("Bitte wählen Sie einen Fahrzeugtyp.", "danger")
        else:
            fahrzeug = Fahrzeug(
                anbieter_id=current_user.anbieter_id,
                fahrzeugtyp_id=int(fahrzeugtyp_id),
                akku_prozent=int(akku_prozent),
                status=status,
                gps_lat=gps_lat,
                gps_long=gps_long,
                qr_code=str(uuid.uuid4()),  # auto-generate unique QR code
            )
            db.session.add(fahrzeug)
            db.session.commit()
            flash("Fahrzeug erfolgreich hinzugefügt.", "success")
            return redirect(url_for("fahrzeuge.meine_fahrzeuge"))

    return render_template("fahrzeuge/form.html", typen=typen, fahrzeug=None)


@fahrzeuge_bp.route("/fahrzeuge/<int:id>/bearbeiten", methods=["GET", "POST"])
@login_required
@anbieter_required
def bearbeiten(id):
    fahrzeug = db.get_or_404(Fahrzeug, id)

    # Ensure the vehicle belongs to the logged-in provider
    if fahrzeug.anbieter_id != current_user.anbieter_id:
        flash("Zugriff verweigert.", "danger")
        return redirect(url_for("fahrzeuge.meine_fahrzeuge"))

    typen = Fahrzeugtyp.query.all()

    if request.method == "POST":
        fahrzeug.fahrzeugtyp_id = int(request.form.get("fahrzeugtyp_id"))
        fahrzeug.akku_prozent = int(request.form.get("akku_prozent", 100))
        fahrzeug.status = request.form.get("status", "verfuegbar")
        fahrzeug.gps_lat = request.form.get("gps_lat") or None
        fahrzeug.gps_long = request.form.get("gps_long") or None
        db.session.commit()
        flash("Fahrzeug erfolgreich aktualisiert.", "success")
        return redirect(url_for("fahrzeuge.meine_fahrzeuge"))

    return render_template("fahrzeuge/form.html", typen=typen, fahrzeug=fahrzeug)


@fahrzeuge_bp.route("/fahrzeuge/<int:id>/loeschen", methods=["POST"])
@login_required
@anbieter_required
def loeschen(id):
    fahrzeug = db.get_or_404(Fahrzeug, id)

    if fahrzeug.anbieter_id != current_user.anbieter_id:
        flash("Zugriff verweigert.", "danger")
        return redirect(url_for("fahrzeuge.meine_fahrzeuge"))

    if fahrzeug.status == "verliehen":
        flash("Fahrzeug kann nicht gelöscht werden – es ist aktuell verliehen.", "danger")
        return redirect(url_for("fahrzeuge.meine_fahrzeuge"))

    db.session.delete(fahrzeug)
    db.session.commit()
    flash("Fahrzeug wurde gelöscht.", "success")
    return redirect(url_for("fahrzeuge.meine_fahrzeuge"))
