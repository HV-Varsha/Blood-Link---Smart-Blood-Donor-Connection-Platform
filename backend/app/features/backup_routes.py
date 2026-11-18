
from datetime import datetime, timezone

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.extensions import db

from app.models import (
    Donor,
    BloodRequest,
    DonationAllocation
)

from app.features.common import (
    current_user,
    compatible_donors
)


backup_bp = Blueprint("backup", __name__)


# ==========================================
# DONOR WITHDRAWAL
# POST /withdraw
# ==========================================

@backup_bp.route("/withdraw", methods=["POST"])
@jwt_required()
def withdraw_from_request():

    user = current_user()

    donor = (
        Donor.query.filter_by(user_id=user.id).first()
        if user else None
    )

    data = request.get_json(silent=True) or {}

    request_id = data.get("request_id")

    if not donor:
        return {
            "message": "Donor profile not found",
            "data": None
        }, 404

    if not isinstance(request_id, int):
        return {
            "message": "request_id must be an integer",
            "data": None
        }, 400

    allocation = DonationAllocation.query.filter_by(
        request_id=request_id,
        donor_id=donor.id,
        status="assigned"
    ).first()

    if not allocation:
        return {
            "message": "No active assignment found for this donor and request",
            "data": None
        }, 404

    allocation.status = "withdrawn"

    allocation.withdrawn_at = datetime.now(
        timezone.utc
    )

    allocation.withdrawal_reason = str(
        data.get("reason", "Not provided")
    )[:250]

    db.session.commit()

    return {

        "message": "Withdrawal recorded. Coordinator can now allocate a backup donor.",

        "data": allocation.to_dict()

    }, 200


# ==========================================
# ALLOCATE BACKUP DONOR
# POST /allocate/<request_id>
# ==========================================

@backup_bp.route("/allocate/<int:request_id>", methods=["POST"])
@jwt_required()
def allocate_backup(request_id):

    user = current_user()

    if not user or user.role not in (
        "admin", "staff", "hospital"
    ):

        return {
            "message": "Only authorised coordinators can allocate backup donors",
            "data": None
        }, 403

    blood_request = db.session.get(
        BloodRequest,
        request_id
    )

    if not blood_request:

        return {
            "message": "Blood request not found",
            "data": None
        }, 404

    excluded = {
        row.donor_id
        for row in DonationAllocation.query.filter_by(
            request_id=request_id
        ).all()
    }

    donors = compatible_donors(
        blood_request.blood_group,
        blood_request.city
    )

    candidate = next(
        (
            donor for donor in donors
            if donor.id not in excluded
        ),
        None
    )

    if not candidate:

        return {
            "message": "No eligible backup candidate currently found",
            "data": None
        }, 404

    allocation = DonationAllocation(

        request_id=request_id,

        donor_id=candidate.id,

        status="assigned",

        assigned_by=user.id

    )

    db.session.add(allocation)

    db.session.commit()

    return {

        "message": "Backup donor assigned",

        "data": {

            "allocation": allocation.to_dict(),

            "donor": candidate.to_dict()

        }

    }, 201


# ==========================================
# ASSIGN INITIAL DONOR
# POST /assign/<request_id>
# ==========================================

@backup_bp.route("/assign/<int:request_id>", methods=["POST"])
@jwt_required()
def assign_initial_donor(request_id):

    user = current_user()

    if not user or user.role not in (
        "admin", "staff", "hospital"
    ):

        return {
            "message": "Only authorised coordinators can assign donors",
            "data": None
        }, 403

    blood_request = db.session.get(
        BloodRequest,
        request_id
    )

    data = request.get_json(silent=True) or {}

    donor_id = data.get("donor_id")

    donor = (
        db.session.get(Donor, donor_id)
        if isinstance(donor_id, int)
        else None
    )

    if not blood_request or not donor:

        return {
            "message": "Blood request or donor not found",
            "data": None
        }, 404

    if donor not in compatible_donors(
        blood_request.blood_group,
        blood_request.city
    ):

        return {
            "message": "Donor is unavailable or not compatible for this request",
            "data": None
        }, 400

    existing = DonationAllocation.query.filter_by(
        request_id=request_id,
        donor_id=donor.id,
        status="assigned"
    ).first()

    if existing:

        return {
            "message": "This donor is already assigned to the request",
            "data": None
        }, 409

    allocation = DonationAllocation(

        request_id=request_id,

        donor_id=donor.id,

        status="assigned",

        assigned_by=user.id

    )

    db.session.add(allocation)

    db.session.commit()

    return {

        "message": "Donor assigned successfully",

        "data": allocation.to_dict()

    }, 201
