
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
# POST /api/backup/withdraw
# ==========================================

@backup_bp.route("/withdraw", methods=["POST"])
@jwt_required()
def withdraw_from_request():

    user = current_user()

    if not user:
        return {
            "message": "User not found",
            "data": None
        }, 404

    donor = Donor.query.filter_by(
        user_id=user.id
    ).first()

    data = request.get_json(silent=True) or {}

    request_id = data.get("request_id")

    if not donor:
        return {
            "message": "Donor profile not found",
            "data": None
        }, 404

    try:
        request_id = int(request_id)
    except (ValueError, TypeError):
        return {
            "message": "request_id must be an integer",
            "data": None
        }, 400

    allocation = DonationAllocation.query.filter_by(
        request_id=request_id,
        donor_id=donor.id
    ).filter(
        DonationAllocation.status.in_(
            ["assigned", "accepted"]
        )
    ).first()

    if not allocation:
        return {
            "message": "No active assignment found for this donor and request",
            "data": None
        }, 404

    blood_request = db.session.get(
        BloodRequest,
        request_id
    )

    try:
        allocation.status = "withdrawn"

        allocation.withdrawn_at = datetime.now(
            timezone.utc
        )

        allocation.withdrawal_reason = str(
            data.get("reason", "Not provided")
        )[:250]

        if blood_request and blood_request.status == "matched":

            active_count = DonationAllocation.query.filter_by(
                request_id=request_id
            ).filter(
                DonationAllocation.status.in_(
                    ["accepted", "assigned"]
                )
            ).count()

            if active_count < blood_request.units_required:
                blood_request.status = "pending"

        db.session.commit()

        return {
            "message": "Withdrawal recorded successfully",
            "data": allocation.to_dict()
        }, 200

    except Exception as e:
        db.session.rollback()
        print("Withdrawal Error:", str(e))

        return {
            "message": "Unable to withdraw from request",
            "data": None
        }, 500


# ==========================================
# ALLOCATE BACKUP DONOR
# POST /api/backup/allocate/<request_id>
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

    try:
        db.session.add(allocation)
        db.session.commit()

        return {
            "message": "Backup donor assigned successfully",
            "data": {
                "allocation": allocation.to_dict(),
                "donor": candidate.to_dict()
            }
        }, 201

    except Exception as e:
        db.session.rollback()
        print("Backup Allocation Error:", str(e))

        return {
            "message": "Unable to allocate backup donor",
            "data": None
        }, 500


# ==========================================
# ASSIGN INITIAL DONOR
# POST /api/backup/assign/<request_id>
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

    if not blood_request:
        return {
            "message": "Blood request not found",
            "data": None
        }, 404

    data = request.get_json(silent=True) or {}

    donor_id = data.get("donor_id")

    try:
        donor_id = int(donor_id)
    except (ValueError, TypeError):
        return {
            "message": "Valid donor_id is required",
            "data": None
        }, 400

    donor = db.session.get(
        Donor,
        donor_id
    )

    if not donor:
        return {
            "message": "Donor not found",
            "data": None
        }, 404

    compatible = compatible_donors(
        blood_request.blood_group,
        blood_request.city
    )

    if donor.id not in [item.id for item in compatible]:
        return {
            "message": "Donor is unavailable or not compatible for this request",
            "data": None
        }, 400

    existing = DonationAllocation.query.filter_by(
        request_id=request_id,
        donor_id=donor.id
    ).filter(
        DonationAllocation.status.in_(
            ["assigned", "accepted"]
        )
    ).first()

    if existing:
        return {
            "message": "This donor is already assigned to the request",
            "data": None
        }, 409

    active_allocation = DonationAllocation.query.filter_by(
        donor_id=donor.id
    ).filter(
        DonationAllocation.status.in_(
            ["assigned", "accepted"]
        )
    ).first()

    if active_allocation:
        return {
            "message": "Donor already has an active assignment",
            "data": None
        }, 409

    allocation = DonationAllocation(
        request_id=request_id,
        donor_id=donor.id,
        status="assigned",
        assigned_by=user.id
    )

    try:
        db.session.add(allocation)
        db.session.commit()

        return {
            "message": "Donor assigned successfully",
            "data": allocation.to_dict()
        }, 201

    except Exception as e:
        db.session.rollback()
        print("Assign Donor Error:", str(e))

        return {
            "message": "Unable to assign donor",
            "data": None
        }, 500
