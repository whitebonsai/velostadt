from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    # Anbieter goes directly to their vehicle list
    if current_user.role == "anbieter":
        return redirect(url_for("fahrzeuge.meine_fahrzeuge"))

    # Benutzer sees their dashboard with active ride info
    aktive_fahrt = current_user.aktive_fahrt
    return render_template("dashboard.html", aktive_fahrt=aktive_fahrt)
