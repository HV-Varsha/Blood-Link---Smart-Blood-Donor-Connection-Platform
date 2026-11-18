
from datetime import date

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import BloodRequest, User, BLOOD_GROUPS


request_bp = Blueprint("requests", __name__)


# CREATE A BLOOD REQUEST
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
        return {"message": "Units required must be a number", "data": None}, 400

    if units <= 0:
        return {"message": "Units required must be greater than zero", "data": None}, 400

    blood_request = BloodRequest(
        requester_id=user_id,
        blood_group=blood_group,
        city=data["city"].strip(),
        units_required=units
    )

    db.session.add(blood_request)
    db.session.commit()

    return {
        "message": "Blood request created successfully",
        "data": blood_request.to_dict()
    }, 201


# VIEW ALL BLOOD REQUESTS
@request_bp.route("/", methods=["GET"])
@jwt_required()
def get_all_requests():

    requests = BloodRequest.query.order_by(
        BloodRequest.id.desc()
    ).all()

    return {
        "message": "Blood requests fetched successfully",
        "data": [item.to_dict() for item in requests]
    }, 200


# VIEW ONE BLOOD REQUEST
@request_bp.route("/<int:request_id>", methods=["GET"])
@jwt_required()
def get_request(request_id):

    blood_request = db.session.get(BloodRequest, request_id)

    if not blood_request:
        return {"message": "Blood request not found", "data": None}, 404

    return {
        "message": "Blood request fetched successfully",
        "data": blood_request.to_dict()
    }, 200


# UPDATE A BLOOD REQUEST
@request_bp.route("/<int:request_id>", methods=["PUT"])
@jwt_required()
def update_request(request_id):

    user_id = int(get_jwt_identity())

    blood_request = db.session.get(BloodRequest, request_id)

    if not blood_request:
        return {"message": "Blood request not found", "data": None}, 404

    if blood_request.requester_id != user_id:
        return {
            "message": "You can only update your own requests",
            "data": None
        }, 403

    data = request.get_json(silent=True) or {}

    if "blood_group" in data:
        blood_group = data["blood_group"].strip().upper()

        if blood_group not in BLOOD_GROUPS:
            return {"message": "Invalid blood group", "data": None}, 400

        blood_request.blood_group = blood_group

    if "city" in data:
        if not isinstance(data["city"], str) or not data["city"].strip():
            return {"message": "City cannot be empty", "data": None}, 400
        blood_request.city = data["city"].strip()

    if "units_required" in data:
        try:
            units = int(data["units_required"])
        except (ValueError, TypeError):
            return {"message": "Units required must be a number", "data": None}, 400

        if units <= 0:
            return {"message": "Units must be greater than zero", "data": None}, 400

        blood_request.units_required = units

    db.session.commit()

    return {
        "message": "Blood request updated successfully",
        "data": blood_request.to_dict()
    }, 200


# DELETE A BLOOD REQUEST
@request_bp.route("/<int:request_id>", methods=["DELETE"])
@jwt_required()
def delete_request(request_id):

    user_id = int(get_jwt_identity())

    blood_request = db.session.get(BloodRequest, request_id)

    if not blood_request:
        return {"message": "Blood request not found", "data": None}, 404

    if blood_request.requester_id != user_id:
        return {
            "message": "You can only delete your own requests",
            "data": None
        }, 403

    db.session.delete(blood_request)
    db.session.commit()

    return {
        "message": "Blood request deleted successfully",
        "data": None
    }, 200
