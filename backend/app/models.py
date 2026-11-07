
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
