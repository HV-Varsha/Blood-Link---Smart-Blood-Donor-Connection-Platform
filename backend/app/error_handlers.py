
from flask import jsonify
from werkzeug.exceptions import HTTPException

from app.extensions import jwt


def register_error_handlers(app):

    # General HTTP errors
    @app.errorhandler(HTTPException)
    def handle_http_error(error):

        return jsonify({
            "message": error.description,
            "data": None
        }), error.code

    # Unexpected server errors
    @app.errorhandler(Exception)
    def handle_general_error(error):

        app.logger.exception("Unexpected application error")

        return jsonify({
            "message": "Internal server error",
            "data": None
        }), 500

    # JWT: Missing token
    @jwt.unauthorized_loader
    def handle_missing_token(error):

        return jsonify({
            "message": "Authentication token is required",
            "data": None
        }), 401

    # JWT: Invalid token
    @jwt.invalid_token_loader
    def handle_invalid_token(error):

        return jsonify({
            "message": "Invalid authentication token",
            "data": None
        }), 401

    # JWT: Expired token
    @jwt.expired_token_loader
    def handle_expired_token(jwt_header, jwt_payload):

        return jsonify({
            "message": "Authentication token has expired",
            "data": None
        }), 401

    # JWT: Revoked token
    @jwt.revoked_token_loader
    def handle_revoked_token(jwt_header, jwt_payload):

        return jsonify({
            "message": "Authentication token has been revoked",
            "data": None
        }), 401
