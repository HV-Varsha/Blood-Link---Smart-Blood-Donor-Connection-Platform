
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models import Donor, DonorAlertLog

from app.features.common import current_user, donor_for_user


fatigue_bp = Blueprint("fatigue", __name__)


# ==========================================
# CHECK DONOR FATIGUE
# GET /check
# ==========================================

@fatigue_bp.route("/check", methods=["GET"])
@jwt_required()
def check_fatigue():

    user = current_user()
    donor = donor_for_user(user)

    if not user or not donor:
        return {
            "message": "Donor profile not found",
            "data": None
        }, 404

    try:
        days = int(
            request.args.get("cooldown_days", 7)
        )

    except ValueError:
        return {
            "message": "cooldown_days must be an integer",
            "data": None
        }, 400

    if not 1 <= days <= 60:
        return {
            "message": "cooldown_days must be between 1 and 60",
            "data": None
        }, 400

    cutoff = datetime.now(timezone.utc) - timedelta(
        days=days
    )

    recent = DonorAlertLog.query.filter(
        DonorAlertLog.donor_id == donor.id,
        DonorAlertLog.sent_at >= cutoff
    ).count()

    return {
        "message": "Donor fatigue status",
        "data": {
            "donor_id": donor.id,
            "alerts_in_cooldown": recent,
            "cooldown_days": days,
            "eligible_for_new_alert": recent == 0
        }
    }, 200


# ==========================================
# RECORD DONOR ALERT
# POST /record-alert
# ==========================================

@fatigue_bp.route("/record-alert", methods=["POST"])
@jwt_required()
def record_alert():

    user = current_user()

    if not user or user.role not in (
        "admin", "staff", "hospital"
    ):
        return {
            "message": "Only authorised coordinators can record alerts",
            "data": None
        }, 403

    data = request.get_json(silent=True) or {}

    donor_id = data.get("donor_id")
    request_id = data.get("request_id")

    if not isinstance(donor_id, int) or not isinstance(request_id, int):
        return {
            "message": "donor_id and request_id must be integers",
            "data": None
        }, 400

    donor = db.session.get(Donor, donor_id)

    if not donor:
        return {
            "message": "Donor not found",
            "data": None
        }, 404

    # Check cooldown before recording another alert.
    cooldown_days = 7
    cutoff = datetime.now(timezone.utc) - timedelta(
        days=cooldown_days
    )

    recent = DonorAlertLog.query.filter(
        DonorAlertLog.donor_id == donor.id,
        DonorAlertLog.sent_at >= cutoff
    ).count()

    if recent > 0:
        return {
            "message": "Donor is in the alert cooldown period",
            "data": {
                "eligible_for_new_alert": False,
                "cooldown_days": cooldown_days
            }
        }, 409

    log = DonorAlertLog(
        donor_id=donor_id,
        request_id=request_id
    )

    db.session.add(log)
    db.session.commit()

    return {
        "message": "Alert recorded successfully",
        "data": log.to_dict()
    }, 201
