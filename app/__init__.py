import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy extension instance globally so models and blueprints can import it
db = SQLAlchemy()


def create_app(test_config: dict | None = None) -> Flask:
    """
    Application Factory pattern for FinTrack: Expense & Transaction Management System.
    Configures SQLAlchemy (MySQL primary with local SQLite fallback) and registers Flask Blueprints.
    """
    app = Flask(__name__)

    # Secret key for session management and security
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "fintrack-prod-secret-key-2026"
    )

    # Database Configuration:
    # Reads from environment variable DATABASE_URL.
    # Example Production MySQL URI:
    # export DATABASE_URL="mysql+pymysql://user:password@localhost/fintrack_db"
    # Defaults to local SQLite file (sqlite:///fintrack.db) so the project runs out of the box.
    default_sqlite_uri = "sqlite:///fintrack.db"
    database_url = os.environ.get("DATABASE_URL", default_sqlite_uri)

    # Normalize legacy mysql:// prefix to mysql+pymysql:// if provided
    if database_url.startswith("mysql://"):
        database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    if test_config is not None:
        app.config.update(test_config)

    # Bind SQLAlchemy instance to this Flask application
    db.init_app(app)

    with app.app_context():
        # Import models to ensure SQLAlchemy metadata registers User and Transaction tables & indexes
        from app import models  # noqa: F401

        # Register Modular Blueprints
        from app.routes.api_routes import api_bp
        from app.routes.web_routes import web_bp

        app.register_blueprint(api_bp, url_prefix="/api")
        app.register_blueprint(web_bp, url_prefix="/")

        # Create database tables and composite indexes if they don't exist yet
        db.create_all()

    return app
