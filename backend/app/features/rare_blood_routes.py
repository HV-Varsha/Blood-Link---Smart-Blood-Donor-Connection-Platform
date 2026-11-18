
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.models import BloodRequest

from app.features.common import (
    PROJECT_RARE_GROUPS,
    compatible_donors
)


rare_bp = Blueprint("rare_blood", __name__)


# ==========================================
# GET RARE BLOOD REQUESTS
# GET /requests
# ==========================================

@rare_bp.route("/requests", methods=["GET"])
@jwt_required()
def rare_requests():

    query = BloodRequest.query.filter(
        BloodRequest.status == "pending",
        BloodRequest.blood_group.in_(
            PROJECT_RARE_GROUPS
        )
    )

    city = request.args.get("city")

    if city:
        query = query.filter(
            BloodRequest.city.ilike(
                city.strip()
            )
        )

    items = query.order_by(
        BloodRequest.required_by.asc()
    ).all()

    return {

        "message": "Priority rare-group requests",

        "data": {

            "configured_rare_groups": sorted(
                PROJECT_RARE_GROUPS
            ),

            "requests": [
                item.to_dict()
                for item in items
            ]

        }

    }, 200


# ==========================================
# FIND RARE BLOOD DONOR MATCHES
# GET /match/<request_id>
# ==========================================

@rare_bp.route("/match/<int:request_id>", methods=["GET"])
@jwt_required()
def rare_matches(request_id):

    blood_request = BloodRequest.query.get(
        request_id
    )

    if not blood_request:
        return {
            "message": "Blood request not found",
            "data": None
        }, 404

    if blood_request.blood_group not in PROJECT_RARE_GROUPS:
        return {
            "message": "This request is not in the configured rare-group list",
            "data": None
        }, 400

    donors = compatible_donors(
        blood_request.blood_group,
        blood_request.city
    )

    return {

        "message": "Compatible rare-group donor candidates",

        "data": {

            "request_id": request_id,

            "donors": [
                donor.to_dict()
                for donor in donors
            ],

            "note": "Compatibility is preliminary. Blood bank crossmatching and clinical checks are mandatory."

        }

    }, 200
