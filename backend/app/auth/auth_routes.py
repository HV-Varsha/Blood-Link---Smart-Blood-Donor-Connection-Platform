
import re

from flask import Blueprint, request

from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt,
    get_jwt_identity
)

from sqlalchemy.exc import IntegrityError

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from app.extensions import db, jwt
from app.models import User, TokenBlocklist


# ==========================================
# CREATE AUTHENTICATION BLUEPRINT
# ==========================================

auth_bp = Blueprint("auth", __name__)


# ==========================================
# 1. USER REGISTRATION
# POST /api/auth/register
# ==========================================

@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {
            "message": "Request body must be valid JSON",
            "data": None
        }, 400

    # Get registration fields
    raw_fields = [
        data.get("name"),
        data.get("email"),
        data.get("password"),
        data.get("phone"),
        data.get("role")
    ]

    # Validate field types
    if not all(isinstance(value, str) for value in raw_fields):
        return {
            "message": "All fields must contain valid text values",
            "data": None
        }, 400

    # Extract fields
    name, email, password, phone, role = raw_fields

    name = name.strip()
    email = email.strip().lower()
    phone = phone.strip()
    role = role.strip().lower()

    # Check empty fields
    if not all([name, email, password, phone, role]):
        return {
            "message": "All fields are required",
            "data": None
        }, 400

    # Validate name
    if len(name) < 2 or len(name) > 100:
        return {
            "message": "Name must contain 2 to 100 characters",
            "data": None
        }, 400

    # Validate email
    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    if not re.match(email_pattern, email):
        return {
            "message": "Please provide a valid email address",
            "data": None
        }, 400

    # Validate password
    if len(password) < 8:
        return {
            "message": "Password must contain at least 8 characters",
            "data": None
        }, 400

    if len(password) > 128:
        return {
            "message": "Password cannot exceed 128 characters",
            "data": None
        }, 400

    # Validate phone
    if not re.fullmatch(r"\+?[0-9]{7,15}", phone):
        return {
            "message": "Please provide a valid phone number",
            "data": None
        }, 400

    # Validate role
    if role not in ["donor", "recipient"]:
        return {
            "message": "Role must be donor or recipient",
            "data": None
        }, 400

    # Check duplicate email
    existing_user = User.query.filter_by(
        email=email
    ).first()

    if existing_user:
        return {
            "message": "Email is already registered",
            "data": None
        }, 409

    # Hash password
    hashed_password = generate_password_hash(password)

    # Create user
    new_user = User(
        name=name,
        email=email,
        password_hash=hashed_password,
        phone=phone,
        role=role
    )

    try:
        db.session.add(new_user)
        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        return {
            "message": "Email is already registered",
            "data": None
        }, 409

    return {
        "message": "Registration successful",
        "data": {
            "user": new_user.to_dict()
        }
    }, 201


# ==========================================
# 2. USER LOGIN
# POST /api/auth/login
# ==========================================

@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {
            "message": "Request body must be valid JSON",
            "data": None
        }, 400

    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or not isinstance(password, str):
        return {
            "message": "Email and password are required",
            "data": None
        }, 400

    email = email.strip().lower()

    if not email or not password:
        return {
            "message": "Email and password are required",
            "data": None
        }, 400

    # Find user
    user = User.query.filter_by(
        email=email
    ).first()

    # Verify password
    if user is None or not check_password_hash(
        user.password_hash, password
    ):
        return {
            "message": "Invalid email or password",
            "data": None
        }, 401

    # Generate JWT token
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role
        }
    )

    return {
        "message": "Login successful",
        "data": {
            "access_token": access_token,
            "token_type": "Bearer",
            "user": user.to_dict()
        }
    }, 200


# ==========================================
# 3. JWT TOKEN BLOCKLIST CHECK
# ==========================================

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):

    token_jti = jwt_payload["jti"]

    blocked_token = TokenBlocklist.query.filter_by(
        jti=token_jti
    ).first()

    return blocked_token is not None


# ==========================================
# 4. USER LOGOUT
# POST /api/auth/logout
# ==========================================

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():

    jwt_data = get_jwt()

    token_jti = jwt_data["jti"]

    # Add token to blocklist
    blocked_token = TokenBlocklist(
        jti=token_jti
    )

    db.session.add(blocked_token)
    db.session.commit()

    return {
        "message": "Logout successful. Token has been revoked",
        "data": None
    }, 200


# ==========================================
# 5. GET CURRENT USER
# GET /api/auth/me
# ==========================================

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():

    user_id = get_jwt_identity()

    user = db.session.get(User, int(user_id))

    if user is None:
        return {
            "message": "User not found",
            "data": None
        }, 404

    return {
        "message": "User details retrieved successfully",
        "data": {
            "user": user.to_dict()
        }
    }, 200
