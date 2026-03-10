from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import Config

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Bitte melden Sie sich an."
login_manager.login_message_category = "info"


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # User loader handles both Benutzer (prefix 'b-') and Anbieter (prefix 'a-')
    from .models import Anbieter, Benutzer

    @login_manager.user_loader
    def load_user(user_id):
        if user_id.startswith("a-"):
            return db.session.get(Anbieter, int(user_id[2:]))
        elif user_id.startswith("b-"):
            return db.session.get(Benutzer, int(user_id[2:]))
        return None

    # Register blueprints
    from .controllers.auth import auth_bp
    from .controllers.main import main_bp
    from .controllers.fahrzeuge import fahrzeuge_bp
    from .controllers.fahrten import fahrten_bp
    from .controllers.api import api_bp
    from flask_swagger_ui import get_swaggerui_blueprint

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(fahrzeuge_bp)
    app.register_blueprint(fahrten_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    swagger_ui = get_swaggerui_blueprint(
        "/api/docs",
        "/static/swagger.yaml",
        config={"app_name": "Velostadt API"},
    )
    app.register_blueprint(swagger_ui, url_prefix="/api/docs")

    return app
