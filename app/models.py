from datetime import datetime
from flask_login import UserMixin
from . import db, bcrypt


class Anbieter(UserMixin, db.Model):
    """Provider that owns and manages vehicles."""

    __tablename__ = "anbieter"

    anbieter_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    e_mail = db.Column(db.String(254), unique=True, nullable=False)
    passwort_hash = db.Column(db.String(255), nullable=False)

    fahrzeuge = db.relationship("Fahrzeug", backref="anbieter", lazy=True)

    # Flask-Login uses get_id() to identify the user in the session
    def get_id(self):
        return f"a-{self.anbieter_id}"

    @property
    def role(self):
        return "anbieter"

    def set_password(self, password):
        self.passwort_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.passwort_hash, password)


class Benutzer(UserMixin, db.Model):
    """End user who rents vehicles."""

    __tablename__ = "benutzer"

    benutzer_id = db.Column(db.Integer, primary_key=True)
    vorname = db.Column(db.String(80), nullable=False)
    nachname = db.Column(db.String(80), nullable=False)
    e_mail = db.Column(db.String(254), unique=True, nullable=False)
    passwort_hash = db.Column(db.String(255), nullable=False)

    fahrten = db.relationship("Fahrt", backref="benutzer", lazy=True)
    zahlungsmittel_list = db.relationship(
        "Zahlungsmittel", backref="benutzer", lazy=True
    )

    def get_id(self):
        return f"b-{self.benutzer_id}"

    @property
    def role(self):
        return "benutzer"

    @property
    def vollname(self):
        return f"{self.vorname} {self.nachname}"

    @property
    def aktive_fahrt(self):
        """Returns the currently active (not yet ended) ride, if any."""
        return Fahrt.query.filter_by(
            benutzer_id=self.benutzer_id, endzeit=None
        ).first()

    def set_password(self, password):
        self.passwort_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.passwort_hash, password)


class Fahrzeugtyp(db.Model):
    """Vehicle type definition with pricing (e.g. E-Scooter, E-Bike)."""

    __tablename__ = "fahrzeugtyp"

    fahrzeugtyp_id = db.Column(db.Integer, primary_key=True)
    bezeichnung = db.Column(db.String(80), nullable=False)
    basispreis = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    preis_pro_min = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)

    fahrzeuge = db.relationship("Fahrzeug", backref="fahrzeugtyp", lazy=True)


class Fahrzeug(db.Model):
    """A single rentable vehicle owned by a provider."""

    __tablename__ = "fahrzeuge"

    STATI = ["verfuegbar", "verliehen", "in_wartung"]

    fahrzeug_id = db.Column(db.Integer, primary_key=True)
    anbieter_id = db.Column(
        db.Integer, db.ForeignKey("anbieter.anbieter_id"), nullable=False
    )
    fahrzeugtyp_id = db.Column(
        db.Integer, db.ForeignKey("fahrzeugtyp.fahrzeugtyp_id"), nullable=False
    )
    akku_prozent = db.Column(db.Integer, nullable=False, default=100)
    status = db.Column(db.String(30), nullable=False, default="verfuegbar")
    gps_lat = db.Column(db.Numeric(9, 6))
    gps_long = db.Column(db.Numeric(9, 6))
    qr_code = db.Column(db.String(128), unique=True, nullable=False)

    fahrten = db.relationship("Fahrt", backref="fahrzeug", lazy=True)


class Zahlungsmittel(db.Model):
    """Payment method associated with a user."""

    __tablename__ = "zahlungsmittel"

    TYPEN = ["Kreditkarte", "Debitkarte", "PayPal", "Rechnung"]

    zahlungsmittel_id = db.Column(db.Integer, primary_key=True)
    benutzer_id = db.Column(
        db.Integer, db.ForeignKey("benutzer.benutzer_id"), nullable=False
    )
    typ = db.Column(db.String(30), nullable=False)
    details = db.Column(db.String(255))

    abrechnungen = db.relationship("Abrechnung", backref="zahlungsmittel", lazy=True)


class Fahrt(db.Model):
    """A single ride from start to finish."""

    __tablename__ = "fahrt"

    fahrt_id = db.Column(db.Integer, primary_key=True)
    fahrzeug_id = db.Column(
        db.Integer, db.ForeignKey("fahrzeuge.fahrzeug_id"), nullable=False
    )
    benutzer_id = db.Column(
        db.Integer, db.ForeignKey("benutzer.benutzer_id"), nullable=False
    )
    startzeit = db.Column(db.DateTime, nullable=False, default=datetime.now)
    endzeit = db.Column(db.DateTime)
    kilometer = db.Column(db.Numeric(10, 3), nullable=False, default=0.000)
    preis = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)

    abrechnung = db.relationship("Abrechnung", backref="fahrt", uselist=False)

    @property
    def dauer_minuten(self):
        if self.endzeit and self.startzeit:
            return (self.endzeit - self.startzeit).total_seconds() / 60
        return None

    @property
    def ist_aktiv(self):
        return self.endzeit is None


class Abrechnung(db.Model):
    """Billing record created when a ride ends."""

    __tablename__ = "abrechnung"

    transaktion_id = db.Column(db.Integer, primary_key=True)
    fahrt_id = db.Column(
        db.Integer, db.ForeignKey("fahrt.fahrt_id"), unique=True, nullable=False
    )
    zahlungsmittel_id = db.Column(
        db.Integer,
        db.ForeignKey("zahlungsmittel.zahlungsmittel_id"),
        nullable=False,
    )
    betrag = db.Column(db.Numeric(10, 2), nullable=False)
    zeitpunkt = db.Column(db.DateTime, nullable=False, default=datetime.now)
