from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from ..models import Anbieter, Benutzer
from .. import db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "benutzer")
        remember = bool(request.form.get("remember"))

        user = None
        if role == "anbieter":
            user = Anbieter.query.filter_by(e_mail=email).first()
        else:
            user = Benutzer.query.filter_by(e_mail=email).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))
        else:
            flash("E-Mail oder Passwort ist falsch.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/register/benutzer", methods=["GET", "POST"])
def register_benutzer():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        vorname = request.form.get("vorname", "").strip()
        nachname = request.form.get("nachname", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")

        if not all([vorname, nachname, email, password]):
            flash("Alle Felder sind erforderlich.", "danger")
        elif password != password2:
            flash("Passwörter stimmen nicht überein.", "danger")
        elif Benutzer.query.filter_by(e_mail=email).first():
            flash("Diese E-Mail ist bereits registriert.", "danger")
        else:
            user = Benutzer(vorname=vorname, nachname=nachname, e_mail=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Registrierung erfolgreich! Bitte melden Sie sich an.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/register_benutzer.html")


@auth_bp.route("/register/anbieter", methods=["GET", "POST"])
def register_anbieter():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")

        if not all([name, email, password]):
            flash("Alle Felder sind erforderlich.", "danger")
        elif password != password2:
            flash("Passwörter stimmen nicht überein.", "danger")
        elif Anbieter.query.filter_by(e_mail=email).first():
            flash("Diese E-Mail ist bereits registriert.", "danger")
        else:
            anbieter = Anbieter(name=name, e_mail=email)
            anbieter.set_password(password)
            db.session.add(anbieter)
            db.session.commit()
            flash("Registrierung erfolgreich! Bitte melden Sie sich an.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/register_anbieter.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sie wurden erfolgreich abgemeldet.", "info")
    return redirect(url_for("main.index"))
