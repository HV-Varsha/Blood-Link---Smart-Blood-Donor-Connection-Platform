
from datetime import date

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import User, Donor, BLOOD_GROUPS


# Create donor blueprint
donor_bp = Blueprint("donors", __name__)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_logged_in_user():

    user_id = get_jwt_identity()

    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None


def is_valid_age(age):

    return (
        isinstance(age, int)
        and not isinstance(age, bool)
        and 18 <= age <= 65
    )


def parse_donation_date(value):

    if value is None or value == "":
        return None

    if not isinstance(value, str):
        raise ValueError("Date must be in YYYY-MM-DD format")

    try:
        donation_date = date.fromisoformat(value)
    except ValueError:
        raise ValueError("Invalid date. Use YYYY-MM-DD format")

    if donation_date > date.today():
        raise ValueError("Last donation date cannot be in the future")

    return donation_date


def donor_not_found():

    return {
        "message": "Donor profile not found",
        "data": None
    }, 404


# ==========================================
# 1. CREATE DONOR PROFILE
# POST /api/donors/profile
# ==========================================

@donor_bp.route("/profile", methods=["POST"])
@jwt_required()
def create_donor_profile():

    user = get_logged_in_user()

    if user is None:
        return {
            "message": "User not found",
            "data": None
        }, 404

    # Only donor accounts can create donor profiles
    if user.role != "donor":
        return {
            "message": "Only donor accounts can create donor profiles",
            "data": None
        }, 403

    # Check whether profile already exists
    existing_profile = Donor.query.filter_by(
        user_id=user.id
    ).first()

    if existing_profile:
        return {
            "message": "Donor profile already exists",
            "data": None
        }, 409

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {
            "message": "Request body must be valid JSON",
            "data": None
        }, 400

    # Get fields
    blood_group = data.get("blood_group")
    area = data.get("area")
    city = data.get("city")
    age = data.get("age")

    # Validate required fields
    if not all([
        isinstance(blood_group, str),
        isinstance(area, str),
        isinstance(city, str)
    ]) or age is None:

        return {
            "message": "Blood group, area, city and age are required",
            "data": None
        }, 400

    blood_group = blood_group.strip().upper()
    area = area.strip()
    city = city.strip()

    # Validate blood group
    if blood_group not in BLOOD_GROUPS:
        return {
            "message": "Invalid blood group",
            "data": {
                "allowed_blood_groups": BLOOD_GROUPS
            }
        }, 400

    # Validate area and city
    if not area or len(area) > 100:
        return {
            "message": "Area must contain 1 to 100 characters",
            "data": None
        }, 400

    if not city or len(city) > 100:
        return {
            "message": "City must contain 1 to 100 characters",
            "data": None
        }, 400

    # Validate age
    if not is_valid_age(age):
        return {
            "message": "Age must be an integer between 18 and 65",
            "data": None
        }, 400

    # Validate last donation date
    try:
        last_donation_date = parse_donation_date(
            data.get("last_donation_date")
        )
    except ValueError as error:
        return {
            "message": str(error),
            "data": None
        }, 400

    # Create donor profile
    donor = Donor(
        user_id=user.id,
        blood_group=blood_group,
        area=area,
        city=city,
        age=age,
        last_donation_date=last_donation_date,
        is_available=True
    )

    db.session.add(donor)
    db.session.commit()

    return {
        "message": "Donor profile created successfully",
        "data": {
            "donor": donor.to_dict()
        }
    }, 201


# ==========================================
# 2. VIEW OWN DONOR PROFILE
# GET /api/donors/profile
# ==========================================

@donor_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_my_donor_profile():

    user = get_logged_in_user()

    if user is None:
        return {
            "message": "User not found",
            "data": None
        }, 404

    if user.role != "donor":
        return {
            "message": "Only donors can view their donor profile",
            "data": None
        }, 403

    donor = Donor.query.filter_by(
        user_id=user.id
    ).first()

    if donor is None:
        return donor_not_found()

    return {
        "message": "Donor profile retrieved successfully",
        "data": {
            "donor": donor.to_dict()
        }
    }, 200


# ==========================================
# 3. UPDATE OWN DONOR PROFILE
# PUT /api/donors/profile
# ==========================================

@donor_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_donor_profile():

    user = get_logged_in_user()

    if user is None:
        return {
            "message": "User not found",
            "data": None
        }, 404

    if user.role != "donor":
        return {
            "message": "Only donors can update donor profiles",
            "data": None
        }, 403

    donor = Donor.query.filter_by(
        user_id=user.id
    ).first()

    if donor is None:
        return donor_not_found()

    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return {
            "message": "Provide valid JSON with fields to update",
            "data": None
        }, 400

    allowed_fields = {
        "blood_group",
        "area",
        "city",
        "age",
        "last_donation_date"
    }

    # Reject unknown fields
    unknown_fields = set(data.keys()) - allowed_fields

    if unknown_fields:
        return {
            "message": "Invalid fields provided",
            "data": {
                "invalid_fields": sorted(unknown_fields)
            }
        }, 400

    # Update blood group
    if "blood_group" in data:

        blood_group = data["blood_group"]

        if not isinstance(blood_group, str):
            return {
                "message": "Blood group must be text",
                "data": None
            }, 400

        blood_group = blood_group.strip().upper()

        if blood_group not in BLOOD_GROUPS:
            return {
                "message": "Invalid blood group",
                "data": {
                    "allowed_blood_groups": BLOOD_GROUPS
                }
            }, 400

        donor.blood_group = blood_group

    # Update area
    if "area" in data:

        area = data["area"]

        if not isinstance(area, str):
            return {
                "message": "Area must be text",
                "data": None
            }, 400

        area = area.strip()

        if not area or len(area) > 100:
            return {
                "message": "Area must contain 1 to 100 characters",
                "data": None
            }, 400

        donor.area = area

    # Update city
    if "city" in data:

        city = data["city"]

        if not isinstance(city, str):
            return {
                "message": "City must be text",
                "data": None
            }, 400

        city = city.strip()

        if not city or len(city) > 100:
            return {
                "message": "City must contain 1 to 100 characters",
                "data": None
            }, 400

        donor.city = city

    # Update age
    if "age" in data:

        age = data["age"]

        if not is_valid_age(age):
            return {
                "message": "Age must be an integer between 18 and 65",
                "data": None
            }, 400

        donor.age = age

    # Update last donation date
    if "last_donation_date" in data:

        try:
            donor.last_donation_date = parse_donation_date(
                data["last_donation_date"]
            )
        except ValueError as error:
            return {
                "message": str(error),
                "data": None
            }, 400

    db.session.commit()

    return {
        "message": "Donor profile updated successfully",
        "data": {
            "donor": donor.to_dict()
        }
    }, 200


# ==========================================
# 4. DELETE OWN DONOR PROFILE
# DELETE /api/donors/profile
# ==========================================

@donor_bp.route("/profile", methods=["DELETE"])
@jwt_required()
def delete_donor_profile():

    user = get_logged_in_user()

    if user is None:
        return {
            "message": "User not found",
            "data": None
        }, 404

    if user.role != "donor":
        return {
            "message": "Only donors can delete donor profiles",
            "data": None
        }, 403

    donor = Donor.query.filter_by(
        user_id=user.id
    ).first()

    if donor is None:
        return donor_not_found()

    db.session.delete(donor)
    db.session.commit()

    return {
        "message": "Donor profile deleted successfully",
        "data": None
    }, 200


# ==========================================
# 5. TOGGLE DONOR AVAILABILITY
# PATCH /api/donors/profile/availability
# ==========================================

@donor_bp.route("/profile/availability", methods=["PATCH"])
@jwt_required()
def update_availability():

    user = get_logged_in_user()

    if user is None:
        return {
            "message": "User not found",
            "data": None
        }, 404

    if user.role != "donor":
        return {
            "message": "Only donors can change availability",
            "data": None
        }, 403

    donor = Donor.query.filter_by(
        user_id=user.id
    ).first()

    if donor is None:
        return donor_not_found()

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {
            "message": "Request body must be valid JSON",
            "data": None
        }, 400

    is_available = data.get("is_available")

    if not isinstance(is_available, bool):
        return {
            "message": "is_available must be true or false",
            "data": None
        }, 400

    donor.is_available = is_available

    db.session.commit()

    status = "available" if is_available else "unavailable"

    return {
        "message": f"Donor is now {status}",
        "data": {
            "is_available": donor.is_available
        }
    }, 200


# ==========================================
# 6. SEARCH AVAILABLE DONORS
# GET /api/donors/search
# ==========================================

@donor_bp.route("/search", methods=["GET"])
@jwt_required()
def search_donors():

    blood_group = request.args.get("blood_group")
    area = request.args.get("area")
    city = request.args.get("city")

    # Pagination parameters
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
    except ValueError:
        return {
            "message": "Page and per_page must be integers",
            "data": None
        }, 400

    if page < 1 or per_page < 1 or per_page > 100:
        return {
            "message": "Page must be at least 1 and per_page must be between 1 and 100",
            "data": None
        }, 400

    query = Donor.query.filter_by(
        is_available=True
    )

    # Filter by blood group
    if blood_group:

        blood_group = blood_group.strip().upper()

        if blood_group not in BLOOD_GROUPS:
            return {
                "message": "Invalid blood group",
                "data": {
                    "allowed_blood_groups": BLOOD_GROUPS
                }
            }, 400

        query = query.filter(
            Donor.blood_group == blood_group
        )

    # Filter by area
    if area:

        area = area.strip()

        if area:
            query = query.filter(
                Donor.area.ilike(f"%{area}%")
            )

    # Filter by city
    if city:

        city = city.strip()

        if city:
            query = query.filter(
                Donor.city.ilike(f"%{city}%")
            )

    # Execute paginated query
    pagination = query.order_by(
        Donor.id.desc()
    ).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    donors = [
        donor.to_dict()
        for donor in pagination.items
    ]

    return {
        "message": "Donor search completed successfully",
        "data": {
            "donors": donors,
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total_donors": pagination.total,
                "total_pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_previous": pagination.has_prev
            }
        }
    }, 200


# ==========================================
# 7. VIEW SINGLE DONOR
# GET /api/donors/<donor_id>
# ==========================================

@donor_bp.route("/<int:donor_id>", methods=["GET"])
@jwt_required()
def get_single_donor(donor_id):

    user = get_logged_in_user()

    if user is None:
        return {
            "message": "User not found",
            "data": None
        }, 404

    donor = db.session.get(Donor, donor_id)

    if donor is None:
        return donor_not_found()

    return {
        "message": "Donor details retrieved successfully",
        "data": {
            "donor": donor.to_dict()
        }
    }, 200
