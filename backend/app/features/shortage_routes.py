
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func

from app.models import Donor, BloodRequest, BLOOD_GROUPS


shortage_bp = Blueprint("shortage", __name__)


# ==========================================
# BLOOD SHORTAGE DASHBOARD
# GET /dashboard
# ==========================================

@shortage_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def shortage_dashboard():

    city = request.args.get("city")

    result = []

    for group in BLOOD_GROUPS:

        demand_query = BloodRequest.query.filter(
            BloodRequest.blood_group == group,
            BloodRequest.status == "pending"
        )

        supply_query = Donor.query.filter(
            Donor.blood_group == group,
            Donor.is_available.is_(True)
        )

        if city:

            demand_query = demand_query.filter(
                func.lower(BloodRequest.city)
                == city.strip().lower()
            )

            supply_query = supply_query.filter(
                func.lower(Donor.city)
                == city.strip().lower()
            )

        pending_requests = demand_query.count()

        units_needed = (
            demand_query
            .with_entities(
                func.coalesce(
                    func.sum(BloodRequest.units_required),
                    0
                )
            )
            .scalar()
        ) or 0

        donor_count = supply_query.count()

        # Calculate shortage risk.
        if units_needed == 0:
            risk = "no_pending_demand"

        elif donor_count == 0:
            risk = "critical"

        elif donor_count < units_needed:
            risk = "high"

        elif donor_count <= units_needed * 1.5:
            risk = "moderate"

        else:
            risk = "low"

        result.append({

            "blood_group": group,

            "pending_requests": pending_requests,

            "units_needed": int(units_needed),

            "available_registered_donors": donor_count,

            "risk_level": risk

        })

    return {

        "message": "Shortage dashboard generated",

        "data": {

            "city": city,

            "metrics": result,

            "note": "Registered donor counts are estimates, not confirmed blood inventory."

        }

    }, 200
