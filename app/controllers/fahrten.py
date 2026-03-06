import decimal
from datetime import datetime
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import Fahrzeug, Fahrt, Zahlungsmittel, Abrechnung
from .. import db

fahrten_bp = Blueprint("fahrten", __name__)


def benutzer_required(f):
    """Decorator that restricts a route to logged-in Benutzer users."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "benutzer":
            flash("Dieser Bereich ist nur für Nutzer zugänglich.", "danger")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)

    return decorated


@fahrten_bp.route("/fahrzeuge")
@login_required
@benutzer_required
def verfuegbare_fahrzeuge():
    """Show all available vehicles that can be rented."""
    fahrzeuge = Fahrzeug.query.filter_by(status="verfuegbar").all()
    return render_template("fahrten/verfuegbar.html", fahrzeuge=fahrzeuge)


@fahrten_bp.route("/fahrt/start/<int:fahrzeug_id>", methods=["POST"])
@login_required
@benutzer_required
def fahrt_start(fahrzeug_id):
    """Start a new ride on the given vehicle."""
    # Prevent starting a second ride while one is active
    aktive = Fahrt.query.filter_by(
        benutzer_id=current_user.benutzer_id, endzeit=None
    ).first()
    if aktive:
        flash("Sie haben bereits eine aktive Fahrt.", "warning")
        return redirect(url_for("main.dashboard"))

    fahrzeug = db.get_or_404(Fahrzeug, fahrzeug_id)
    if fahrzeug.status != "verfuegbar":
        flash("Dieses Fahrzeug ist leider nicht verfügbar.", "danger")
        return redirect(url_for("fahrten.verfuegbare_fahrzeuge"))

    fahrt = Fahrt(
        fahrzeug_id=fahrzeug_id,
        benutzer_id=current_user.benutzer_id,
        startzeit=datetime.utcnow(),
    )
    fahrzeug.status = "verliehen"
    db.session.add(fahrt)
    db.session.commit()
    flash("Fahrt gestartet – gute Fahrt!", "success")
    return redirect(url_for("main.dashboard"))


@fahrten_bp.route("/fahrt/stop/<int:fahrt_id>", methods=["POST"])
@login_required
@benutzer_required
def fahrt_stop(fahrt_id):
    """End a ride and calculate the price."""
    fahrt = db.get_or_404(Fahrt, fahrt_id)

    if fahrt.benutzer_id != current_user.benutzer_id:
        flash("Zugriff verweigert.", "danger")
        return redirect(url_for("main.dashboard"))

    if fahrt.endzeit:
        flash("Diese Fahrt ist bereits beendet.", "warning")
        return redirect(url_for("fahrten.meine_fahrten"))

    # Parse kilometers from form (user enters distance driven)
    try:
        kilometer = decimal.Decimal(request.form.get("kilometer", "0"))
        if kilometer < 0:
            kilometer = decimal.Decimal("0")
    except decimal.InvalidOperation:
        kilometer = decimal.Decimal("0")

    endzeit = datetime.utcnow()
    dauer_min = decimal.Decimal(
        str((endzeit - fahrt.startzeit).total_seconds() / 60)
    )

    # Price = base price + (duration in minutes * price per minute)
    typ = fahrt.fahrzeug.fahrzeugtyp
    preis = typ.basispreis + (dauer_min * typ.preis_pro_min)
    preis = preis.quantize(decimal.Decimal("0.01"))

    fahrt.endzeit = endzeit
    fahrt.kilometer = kilometer
    fahrt.preis = preis
    fahrt.fahrzeug.status = "verfuegbar"

    # Create billing record if the user has a stored payment method
    zahlungsmittel = Zahlungsmittel.query.filter_by(
        benutzer_id=current_user.benutzer_id
    ).first()
    if zahlungsmittel:
        abrechnung = Abrechnung(
            fahrt_id=fahrt.fahrt_id,
            zahlungsmittel_id=zahlungsmittel.zahlungsmittel_id,
            betrag=preis,
            zeitpunkt=datetime.utcnow(),
        )
        db.session.add(abrechnung)
    else:
        flash(
            "Kein Zahlungsmittel hinterlegt – bitte fügen Sie eines hinzu.",
            "warning",
        )

    db.session.commit()
    flash(f"Fahrt beendet. Kosten: CHF {preis:.2f}", "success")
    return redirect(url_for("fahrten.fahrt_detail", fahrt_id=fahrt.fahrt_id))


@fahrten_bp.route("/meine-fahrten")
@login_required
@benutzer_required
def meine_fahrten():
    fahrten = (
        Fahrt.query.filter_by(benutzer_id=current_user.benutzer_id)
        .order_by(Fahrt.startzeit.desc())
        .all()
    )
    return render_template("fahrten/list.html", fahrten=fahrten)


@fahrten_bp.route("/fahrt/<int:fahrt_id>")
@login_required
@benutzer_required
def fahrt_detail(fahrt_id):
    fahrt = db.get_or_404(Fahrt, fahrt_id)
    if fahrt.benutzer_id != current_user.benutzer_id:
        flash("Zugriff verweigert.", "danger")
        return redirect(url_for("fahrten.meine_fahrten"))
    return render_template("fahrten/detail.html", fahrt=fahrt)


@fahrten_bp.route("/zahlungsmittel", methods=["GET", "POST"])
@login_required
@benutzer_required
def zahlungsmittel():
    """Add a payment method to the user's account."""
    if request.method == "POST":
        typ = request.form.get("typ", "").strip()
        details = request.form.get("details", "").strip()

        if not typ:
            flash("Bitte wählen Sie einen Zahlungstyp.", "danger")
        else:
            zm = Zahlungsmittel(
                benutzer_id=current_user.benutzer_id,
                typ=typ,
                details=details,
            )
            db.session.add(zm)
            db.session.commit()
            flash("Zahlungsmittel erfolgreich hinzugefügt.", "success")
            return redirect(url_for("main.dashboard"))

    return render_template(
        "fahrten/zahlungsmittel.html", typen=Zahlungsmittel.TYPEN
    )
