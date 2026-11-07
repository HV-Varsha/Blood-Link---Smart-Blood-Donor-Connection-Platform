
from flask import Flask

from app.config import Config
from app.extensions import db, migrate, jwt, cors


def create_app(config_class=Config):

    # Create Flask application
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config_class)

    # Initialize database
    db.init_app(app)

    # Initialize migrations
    migrate.init_app(app, db)

    # Initialize JWT
    jwt.init_app(app)

    # Initialize CORS
    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": app.config["FRONTEND_URL"]
            }
        },
        supports_credentials=False
    )

    # Import models for SQLAlchemy and migrations
    from app.models import User, Donor, TokenBlocklist

    # Register authentication blueprint
    from app.auth.auth_routes import auth_bp

    app.register_blueprint(
        auth_bp,
        url_prefix="/api/auth"
    )

    # Register donor blueprint
    from app.donors.donor_routes import donor_bp

    app.register_blueprint(
        donor_bp,
        url_prefix="/api/donors"
    )

    # Register global error handlers
    from app.error_handlers import register_error_handlers

    register_error_handlers(app)

    # Health check endpoint
    @app.route("/health", methods=["GET"])
    def health():

        return {
            "message": "BloodLink backend is running",
            "data": {
                "status": "healthy"
            }
        }, 200

    return app
