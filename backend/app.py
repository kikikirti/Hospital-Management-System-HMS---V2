import os
import sqlite3
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from sqlalchemy import event
from sqlalchemy.engine import Engine

from config import Config, INSTANCE_DIR, EXPORT_DIR, REPORT_DIR
from models import db, ensure_default_admin, ensure_default_doctor
from routes import api, cache


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(INSTANCE_DIR, exist_ok=True)
    os.makedirs(EXPORT_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)

    db.init_app(app)
    cache.init_app(app)
    JWTManager(app)
    CORS(app, resources={r"/*": {"origins": "*"}})

    with app.app_context():
        db.create_all()
        ensure_default_admin()

        if os.environ.get("SEED_DEMO_DOCTOR", "1") == "1":
            ensure_default_doctor()

    app.register_blueprint(api, url_prefix="/api")
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)