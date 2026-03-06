import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "velostadt-dev-secret-change-in-prod")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://velouser:velopass@localhost/velostadt",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET = os.environ.get("JWT_SECRET", "velostadt-jwt-secret-change-in-prod")
