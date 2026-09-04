import os
from urllib.parse import quote_plus

from flask import Flask
from dotenv import load_dotenv

from app.config.database import db


load_dotenv()


def create_app():
    app = Flask(__name__)

    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = quote_plus(os.getenv("DB_NAME"))

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}"
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    return app