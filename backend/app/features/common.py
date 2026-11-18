
from flask_jwt_extended import get_jwt_identity

from app.extensions import db
from app.models import (
    User,
    Donor,
    BloodRequest,
    BLOOD_GROUPS
)


DEFAULT_DONATION_INTERVAL_DAYS = 90


# Donor blood group -> compatible recipient groups
RBC_COMPATIBILITY = {
    "O-": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],
    "O+": ["O+", "A+", "B+", "AB+"],
    "A-": ["A-", "A+", "AB-", "AB+"],
    "A+": ["A+", "AB+"],
    "B-": ["B-", "B+", "AB-", "AB+"],
    "B+": ["B+", "AB+"],
    "AB-": ["AB-", "AB+"],
    "AB+": ["AB+"]
}


# Example project classification.
PROJECT_RARE_GROUPS = {"AB-", "B-"}


def current_user():

    try:
        user_id = int(get_jwt_identity())

        return db.session.get(
            User,
            user_id
        )

    except (TypeError, ValueError):
        return None


def donor_for_user(user):

    if not user:
        return None

    return Donor.query.filter_by(
        user_id=user.id
    ).first()


def compatible_donors(recipient_group, city=None):

    recipient_group = (
        recipient_group or ""
    ).upper()

    if recipient_group not in BLOOD_GROUPS:
        return []

    allowed_groups = [
        donor_group
        for donor_group, recipients
        in RBC_COMPATIBILITY.items()
        if recipient_group in recipients
    ]

    query = Donor.query.filter(
        Donor.is_available.is_(True),
        Donor.blood_group.in_(allowed_groups)
    )

    if city:

        query = query.filter(
            Donor.city.ilike(city.strip())
        )

    return query.order_by(
        Donor.id.asc()
    ).all()


def request_or_404(request_id):

    return db.session.get(
        BloodRequest,
        request_id
    )


def json_error(message, status):

    return {
        "message": message,
        "data": None
    }, status
