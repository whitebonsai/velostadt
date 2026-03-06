"""
Velostadt – Flask app entry point.

Run for development:
    flask run  (or)  python run.py

Seed initial vehicle type data:
    flask seed

Run with Gunicorn (production):
    gunicorn -w 4 -b 0.0.0.0:5000 "run:app"
"""

import click
from app import create_app, db
from app.models import Fahrzeugtyp

app = create_app()


@app.cli.command("seed")
def seed():
    """Insert initial Fahrzeugtyp seed data (E-Scooter, E-Bike)."""
    typen = [
        {"bezeichnung": "E-Scooter", "basispreis": 1.00, "preis_pro_min": 0.20},
        {"bezeichnung": "E-Bike", "basispreis": 1.50, "preis_pro_min": 0.25},
    ]
    inserted = 0
    for t in typen:
        if not Fahrzeugtyp.query.filter_by(bezeichnung=t["bezeichnung"]).first():
            db.session.add(Fahrzeugtyp(**t))
            inserted += 1
    db.session.commit()
    if inserted:
        click.echo(f"{inserted} Fahrzeugtyp(en) eingefügt.")
    else:
        click.echo("Fahrzeugtypen bereits vorhanden – nichts geändert.")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
