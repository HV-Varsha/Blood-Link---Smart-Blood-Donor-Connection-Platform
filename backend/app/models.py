
from datetime import datetime, timezone

from app.extensions import db


# Allowed blood groups
BLOOD_GROUPS = [
    "A+", "A-",
    "B+", "B-",
    "AB+", "AB-",
    "O+", "O-"
]


# ==========================================
# USER MODEL
# ==========================================

class User(db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    phone = db.Column(
        db.String(20),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # One user can have one donor profile
    donor_profile = db.relationship(
        "Donor",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def to_dict(self):

        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "created_at": self.created_at.isoformat()
            if self.created_at else None
        }


# ==========================================
# DONOR MODEL
# ==========================================

class Donor(db.Model):

    __tablename__ = "donors"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    blood_group = db.Column(
        db.String(5),
        nullable=False,
        index=True
    )

    area = db.Column(
        db.String(100),
        nullable=False,
        index=True
    )

    city = db.Column(
        db.String(100),
        nullable=False,
        index=True
    )

    age = db.Column(
        db.Integer,
        nullable=False
    )

    last_donation_date = db.Column(
        db.Date,
        nullable=True
    )

    is_available = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
        index=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Connect donor to user
    user = db.relationship(
        "User",
        back_populates="donor_profile"
    )

    def to_dict(self):

        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.user.name if self.user else None,
            "phone": self.user.phone if self.user else None,
            "blood_group": self.blood_group,
            "area": self.area,
            "city": self.city,
            "age": self.age,
            "last_donation_date":
                self.last_donation_date.isoformat()
                if self.last_donation_date else None,
            "is_available": self.is_available,
            "created_at": self.created_at.isoformat()
            if self.created_at else None
        }


# ==========================================
# JWT TOKEN BLOCKLIST MODEL
# ==========================================

class TokenBlocklist(db.Model):

    __tablename__ = "token_blocklist"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    jti = db.Column(
        db.String(36),
        unique=True,
        nullable=False,
        index=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


# ==========================================
# BLOOD REQUEST MODEL
# ==========================================

class BloodRequest(db.Model):

    __tablename__ = "blood_requests"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    requester_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    patient_name = db.Column(
        db.String(100),
        nullable=False
    )

    blood_group = db.Column(
        db.String(5),
        nullable=False,
        index=True
    )

    units_required = db.Column(
        db.Integer,
        nullable=False
    )

    hospital_name = db.Column(
        db.String(150),
        nullable=False
    )

    area = db.Column(
        db.String(100),
        nullable=False
    )

    city = db.Column(
        db.String(100),
        nullable=False,
        index=True
    )

    contact_number = db.Column(
        db.String(20),
        nullable=False
    )

    required_by = db.Column(
        db.Date,
        nullable=False
    )

    urgency = db.Column(
        db.String(20),
        default="normal",
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default="pending",
        nullable=False,
        index=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    requester = db.relationship(
        "User",
        backref="blood_requests"
    )

    def to_dict(self):

        return {
            "id": self.id,
            "requester_id": self.requester_id,
            "patient_name": self.patient_name,
            "blood_group": self.blood_group,
            "units_required": self.units_required,
            "hospital_name": self.hospital_name,
            "area": self.area,
            "city": self.city,
            "contact_number": self.contact_number,
            "required_by": self.required_by.isoformat(),
            "urgency": self.urgency,
            "status": self.status,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at else None
            )
        }


# ==========================================
# DONOR ALERT LOG MODEL
# ==========================================

class DonorAlertLog(db.Model):

    __tablename__ = "donor_alert_logs"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    donor_id = db.Column(
        db.Integer,
        db.ForeignKey("donors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    request_id = db.Column(
        db.Integer,
        db.ForeignKey("blood_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    sent_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    donor = db.relationship(
        "Donor",
        backref=db.backref("alert_logs", lazy=True)
    )

    blood_request = db.relationship(
        "BloodRequest",
        backref=db.backref("alert_logs", lazy=True)
    )

    def to_dict(self):

        return {

            "id": self.id,

            "donor_id": self.donor_id,

            "request_id": self.request_id,

            "sent_at": (
                self.sent_at.isoformat()
                if self.sent_at else None
            )

        }


# ==========================================
# DONATION ALLOCATION MODEL
# ==========================================

class DonationAllocation(db.Model):

    __tablename__ = "donation_allocations"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    request_id = db.Column(
        db.Integer,
        db.ForeignKey("blood_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    donor_id = db.Column(
        db.Integer,
        db.ForeignKey("donors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    assigned_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="assigned",
        index=True
    )

    assigned_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    withdrawn_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    withdrawal_reason = db.Column(
        db.String(250),
        nullable=True
    )

    donor = db.relationship(
        "Donor",
        backref=db.backref("allocations", lazy=True)
    )

    blood_request = db.relationship(
        "BloodRequest",
        backref=db.backref("allocations", lazy=True)
    )

    def to_dict(self):

        return {

            "id": self.id,

            "request_id": self.request_id,

            "donor_id": self.donor_id,

            "assigned_by": self.assigned_by,

            "status": self.status,

            "assigned_at": (
                self.assigned_at.isoformat()
                if self.assigned_at else None
            ),

            "withdrawn_at": (
                self.withdrawn_at.isoformat()
                if self.withdrawn_at else None
            ),

            "withdrawal_reason": self.withdrawal_reason

        }
