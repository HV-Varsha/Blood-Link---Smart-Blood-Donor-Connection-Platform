
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db

from app.models import (
    BloodRequest,
    User,
    Donor,
    DonationAllocation,
    BLOOD_GROUPS
)

from app.features.common import compatible_donors


request_bp = Blueprint("requests", __name__)


# ==========================================
# CREATE A BLOOD REQUEST
# POST /api/requests/
# ==========================================

@request_bp.route("/", methods=["POST"])
@jwt_required()
def create_request():

    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)

    if not user:
        return {"message": "User not found", "data": None}, 404

    data = request.get_json(silent=True) or {}

    required_fields = ["blood_group", "city", "units_required"]

    for field in required_fields:
        if not data.get(field):
            return {
                "message": f"{field} is required",
                "data": None
            }, 400

    blood_group = data["blood_group"].strip().upper()

    if blood_group not in BLOOD_GROUPS:
        return {"message": "Invalid blood group", "data": None}, 400

    try:
        units = int(data["units_required"])
    except (ValueError, TypeError):
        return {
            "message": "Units required must be a number",
            "data": None
        }, 400

    if units <= 0:
        return {
            "message": "Units required must be greater than zero",
            "data": None
        }, 400

    blood_request = BloodRequest(
        requester_id=user_id,
        blood_group=blood_group,
        city=data["city"].strip(),
        units_required=units
    )

    try:
        db.session.add(blood_request)
        db.session.commit()

        return {
            "message": "Blood request created successfully",
            "data": blood_request.to_dict()
        }, 201

    except Exception as e:
        db.session.rollback()
        print("Create Request Error:", str(e))

        return {
            "message": "Unable to create blood request",
            "data": None
        }, 500


# ==========================================
# GET ALL BLOOD REQUESTS
# GET /api/requests/
# ==========================================

@request_bp.route("/", methods=["GET"])
@jwt_required()
def get_all_requests():

    try:
        requests = BloodRequest.query.order_by(
            BloodRequest.id.desc()
        ).all()

        return {
            "message": "Blood requests fetched successfully",
            "data": [item.to_dict() for item in requests]
        }, 200

    except Exception as e:
        print("Get Requests Error:", str(e))

        return {
            "message": "Unable to fetch blood requests",
            "data": None
        }, 500


# ==========================================
# GET BLOOD REQUEST BY ID
# GET /api/requests/<request_id>
# ==========================================

@request_bp.route("/<int:request_id>", methods=["GET"])
@jwt_required()
def get_request(request_id):

    blood_request = db.session.get(
        BloodRequest,
        request_id
    )

    if not blood_request:
        return {
            "message": "Blood request not found",
            "data": None
        }, 404

    return {
        "message": "Blood request fetched successfully",
        "data": blood_request.to_dict()
    }, 200


# ==========================================
# UPDATE BLOOD REQUEST
# PUT /api/requests/<request_id>
# ==========================================

@request_bp.route("/<int:request_id>", methods=["PUT"])
@jwt_required()
def update_request(request_id):

    user_id = int(get_jwt_identity())

    blood_request = db.session.get(
        BloodRequest,
        request_id
    )

    if not blood_request:
        return {
            "message": "Blood request not found",
            "data": None
        }, 404

    if blood_request.requester_id != user_id:
        return {
            "message": "You can only update your own requests",
            "data": None
        }, 403

    data = request.get_json(silent=True) or {}

    if "blood_group" in data:

        if not isinstance(data["blood_group"], str):
            return {
                "message": "Invalid blood group",
                "data": None
            }, 400

        blood_group = data["blood_group"].strip().upper()

        if blood_group not in BLOOD_GROUPS:
            return {
                "message": "Invalid blood group",
                "data": None
            }, 400

        blood_request.blood_group = blood_group

    if "city" in data:

        if not isinstance(data["city"], str) or not data["city"].strip():
            return {
                "message": "City cannot be empty",
                "data": None
            }, 400

        blood_request.city = data["city"].strip()

    if "units_required" in data:

        try:
            units = int(data["units_required"])
        except (ValueError, TypeError):
            return {
                "message": "Units required must be a number",
                "data": None
            }, 400

        if units <= 0:
            return {
                "message": "Units must be greater than zero",
                "data": None
            }, 400

        blood_request.units_required = units

    try:
        db.session.commit()

        return {
            "message": "Blood request updated successfully",
            "data": blood_request.to_dict()
        }, 200

    except Exception as e:
        db.session.rollback()
        print("Update Request Error:", str(e))

        return {
            "message": "Unable to update blood request",
            "data": None
        }, 500


# ==========================================
# DELETE BLOOD REQUEST
# DELETE /api/requests/<request_id>
# ==========================================

@request_bp.route("/<int:request_id>", methods=["DELETE"])
@jwt_required()
def delete_request(request_id):

    user_id = int(get_jwt_identity())

    blood_request = db.session.get(
        BloodRequest,
        request_id
    )

    if not blood_request:
        return {
            "message": "Blood request not found",
            "data": None
        }, 404

    if blood_request.requester_id != user_id:
        return {
            "message": "You can only delete your own requests",
            "data": None
        }, 403

    try:
        db.session.delete(blood_request)
        db.session.commit()

        return {
            "message": "Blood request deleted successfully",
            "data": None
        }, 200

    except Exception as e:
        db.session.rollback()
        print("Delete Request Error:", str(e))

        return {
            "message": "Unable to delete blood request",
            "data": None
        }, 500


# ==========================================
# DONOR ACCEPTS A BLOOD REQUEST
# POST /api/requests/<request_id>/accept
# ==========================================

@request_bp.route("/<int:request_id>/accept", methods=["POST"])
@jwt_required()
def accept_blood_request(request_id):

    user_id = int(get_jwt_identity())

    user = db.session.get(User, user_id)

    if not user:
        return {
            "message": "User not found",
            "data": None
        }, 404

    if user.role != "donor":
        return {
            "message": "Only donors can accept blood requests",
            "data": None
        }, 403

    donor = Donor.query.filter_by(
        user_id=user_id
    ).first()

    if not donor:
        return {
            "message": "Please create your donor profile first",
            "data": None
        }, 404

    if not donor.is_available:
        return {
            "message": "You are currently unavailable for donation",
            "data": None
        }, 400

    blood_request = db.session.get(
        BloodRequest,
        request_id
    )

    if not blood_request:
        return {
            "message": "Blood request not found",
            "data": None
        }, 404

    if blood_request.requester_id == user_id:
        return {
            "message": "You cannot accept your own blood request",
            "data": None
        }, 400

    if blood_request.status != "pending":
        return {
            "message": "This request is no longer accepting donors",
            "data": None
        }, 400

    # Check donor compatibility
    compatible = compatible_donors(
        blood_request.blood_group,
        blood_request.city
    )

    if donor.id not in [item.id for item in compatible]:
        return {
            "message": "You are not compatible with this blood request",
            "data": None
        }, 400

    # Check duplicate acceptance
    existing = DonationAllocation.query.filter_by(
        request_id=request_id,
        donor_id=donor.id
    ).filter(
        DonationAllocation.status.in_(
            ["accepted", "assigned"]
        )
    ).first()

    if existing:
        return {
            "message": "You have already accepted this request",
            "data": None
        }, 409

    # Donor can have only one active allocation
    active_allocation = DonationAllocation.query.filter_by(
        donor_id=donor.id
    ).filter(
        DonationAllocation.status.in_(
            ["accepted", "assigned"]
        )
    ).first()

    if active_allocation:
        return {
            "message": "You already have an active donation assignment",
            "data": None
        }, 409

    # Count active allocations for this request
    active_count = DonationAllocation.query.filter_by(
        request_id=request_id
    ).filter(
        DonationAllocation.status.in_(
            ["accepted", "assigned"]
        )
    ).count()

    if active_count >= blood_request.units_required:
        return {
            "message": "Required donor count has already been reached",
            "data": None
        }, 409

    allocation = DonationAllocation(
        request_id=request_id,
        donor_id=donor.id,
        assigned_by=None,
        status="accepted"
    )

    try:
        db.session.add(allocation)
        db.session.flush()

        if active_count + 1 >= blood_request.units_required:
            blood_request.status = "matched"

        db.session.commit()

        return {
            "message": "Blood request accepted successfully",
            "data": {
                "allocation": allocation.to_dict(),
                "request": blood_request.to_dict()
            }
        }, 201

    except Exception as e:
        db.session.rollback()
        print("Accept Request Error:", str(e))

        return {
            "message": "Unable to accept this blood request",
            "data": None
        }, 500


# ==========================================
# DONOR VIEWS ACCEPTED REQUESTS
# GET /api/requests/my-accepted
# ==========================================

@request_bp.route("/my-accepted", methods=["GET"])
@jwt_required()
def get_my_accepted_requests():

    user_id = int(get_jwt_identity())

    user = db.session.get(User, user_id)

    if not user:
        return {
            "message": "User not found",
            "data": None
        }, 404

    if user.role != "donor":
        return {
            "message": "Only donors can view accepted requests",
            "data": None
        }, 403

    donor = Donor.query.filter_by(
        user_id=user_id
    ).first()

    if not donor:
        return {
            "message": "Donor profile not found",
            "data": None
        }, 404

    try:
        allocations = DonationAllocation.query.filter_by(
            donor_id=donor.id
        ).filter(
            DonationAllocation.status == "accepted"
        ).order_by(
            DonationAllocation.assigned_at.desc()
        ).all()

        result = []

        for allocation in allocations:

            blood_request = db.session.get(
                BloodRequest,
                allocation.request_id
            )

            if blood_request:
                result.append({
                    "allocation": allocation.to_dict(),
                    "request": blood_request.to_dict()
                })

        return {
            "message": "Accepted requests retrieved successfully",
            "data": result
        }, 200

    except Exception as e:
        print("Accepted Requests Error:", str(e))

        return {
            "message": "Unable to fetch accepted requests",
            "data": None
        }, 500
