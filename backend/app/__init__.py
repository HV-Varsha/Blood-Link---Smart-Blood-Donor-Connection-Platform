
from flask import Flask, request
from flask_swagger_ui import get_swaggerui_blueprint

from app.config import Config
from app.extensions import db, migrate, jwt, cors


def create_app(config_class=Config):

    app = Flask(__name__)

    # 1. Load configuration
    app.config.from_object(config_class)

    # 2. Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": app.config["FRONTEND_URL"]
            }
        }
    )

    # 3. Import database models
    from app.models import (
        User,
        Donor,
        TokenBlocklist,
        BloodRequest,
        DonorAlertLog,
        DonationAllocation
    )

    # 4. Register authentication routes
    from app.auth.auth_routes import auth_bp

    app.register_blueprint(
        auth_bp,
        url_prefix="/api/auth"
    )

    # 5. Register donor routes
    from app.donors.donor_routes import donor_bp

    app.register_blueprint(
        donor_bp,
        url_prefix="/api/donors"
    )

    # 6. Register blood request routes
    from app.requests.request_routes import request_bp

    app.register_blueprint(
        request_bp,
        url_prefix="/api/requests"
    )

    # 7. Register additional feature routes

    from app.features.fatigue_routes import fatigue_bp
    from app.features.shortage_routes import shortage_bp
    from app.features.rare_blood_routes import rare_bp
    from app.features.eligibility_routes import eligibility_bp
    from app.features.backup_routes import backup_bp

    app.register_blueprint(
        fatigue_bp,
        url_prefix="/api/fatigue"
    )

    app.register_blueprint(
        shortage_bp,
        url_prefix="/api/shortage"
    )

    app.register_blueprint(
        rare_bp,
        url_prefix="/api/rare-blood"
    )

    app.register_blueprint(
        eligibility_bp,
        url_prefix="/api/eligibility"
    )

    app.register_blueprint(
        backup_bp,
        url_prefix="/api/backup"
    )

    # 8. Register error handlers
    from app.error_handlers import register_error_handlers

    register_error_handlers(app)

    # 9. Health check endpoint
    @app.route("/health", methods=["GET"])
    def health():

        return {
            "message": "BloodLink backend is running",
            "data": {
                "status": "healthy"
            }
        }, 200

    # 10. Swagger UI configuration
    swagger_blueprint = get_swaggerui_blueprint(
        "/docs",
        "/static/swagger.json",
        config={
            "app_name": "BloodLink API",
            "customCssUrl": "/static/swagger-light.css"
        }
    )

    app.register_blueprint(
        swagger_blueprint,
        url_prefix="/docs"
    )

    # 11. Apply custom light theme to Swagger UI
    @app.after_request
    def add_swagger_light_theme(response):

        if (
            request.path.startswith("/docs")
            and response.mimetype == "text/html"
        ):
            html = response.get_data(as_text=True)

            css_link = (
                '<link rel="stylesheet" '
                'href="/static/swagger-light.css">'
            )

            if css_link not in html:
                html = html.replace(
                    "</head>",
                    css_link + "</head>"
                )

            response.set_data(html)

        return response

    return app
