
import pytest

from app import create_app
from app.extensions import db


class TestConfig:

    TESTING = True

    SECRET_KEY = "test-secret-key"

    SQLALCHEMY_DATABASE_URI = "sqlite://"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = "test-jwt-secret-key"

    JWT_TOKEN_LOCATION = ["headers"]

    JWT_BLOCKLIST_ENABLED = True

    JWT_BLOCKLIST_TOKEN_CHECKS = ["access"]

    FRONTEND_URL = "http://localhost:5173"


@pytest.fixture
def app():

    # Create Flask application for testing
    app = create_app(TestConfig)

    # Create a fresh database
    with app.app_context():

        db.create_all()

        yield app

        # Remove database after tests
        db.session.remove()

        db.drop_all()


@pytest.fixture
def client(app):

    # Create Flask test client
    return app.test_client()


@pytest.fixture
def runner(app):

    return app.test_cli_runner()
