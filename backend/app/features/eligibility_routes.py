
from datetime import date, timedelta

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.features.common import (
    current_user,
    donor_for_user,
    DEFAULT_DONATION_INTERVAL_DAYS
)


eligibility_bp = Blueprint("eligibility", __name__)


# ==========================================
# CHECK DONOR ELIGIBILITY REMINDER
# GET /my-status
# ==========================================

@eligibility_bp.route("/my-status", methods=["GET"])
@jwt_required()
def my_eligibility():

    user = current_user()

    donor = donor_for_user(user)

    if not donor:
        return {
            "message": "Donor profile not found",
            "data": None
        }, 404

    try:

        interval = int(
            request.args.get(
                "interval_days",
                DEFAULT_DONATION_INTERVAL_DAYS
            )
        )

    except ValueError:

        return {
            "message": "interval_days must be an integer",
            "data": None
        }, 400

    if not 1 <= interval <= 365:

        return {
            "message": "interval_days must be between 1 and 365",
            "data": None
        }, 400

    if not donor.last_donation_date:

        return {

            "message": "No previous donation date recorded",

            "data": {

                "last_donation_date": None,

                "next_check_date": None,

                "status": "needs_review"

            }

        }, 200

    next_date = (
        donor.last_donation_date
        + timedelta(days=interval)
    )

    if date.today() >= next_date:

        status = "date_threshold_reached_check_with_clinician"

    else:

        status = "reminder_pending"

    return {

        "message": "Eligibility reminder information",

        "data": {

            "last_donation_date": donor.last_donation_date.isoformat(),

            "next_check_date": next_date.isoformat(),

            "status": status,

            "interval_days_used": interval,

            "note": "This is an informational reminder only, not medical clearance. Follow current local blood-bank eligibility rules and clinician advice."

        }

    }, 200
