from datetime import datetime

import sqlalchemy as sa

from app.extensions import db
from app.models.enums import FeedbackCategory, FeedbackStatus, UrgencyLevel


def _enum_column(enum_cls, **kwargs):
    return db.Column(
        sa.Enum(enum_cls, values_callable=lambda e: [m.value for m in e]),
        **kwargs,
    )


class Feedback(db.Model):
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120), nullable=False)
    customer_email = db.Column(db.String(254), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    category = _enum_column(FeedbackCategory, nullable=False, index=True)
    order_id = db.Column(db.String(40), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    urgency = _enum_column(
        UrgencyLevel, nullable=False, default=UrgencyLevel.NORMAL, index=True
    )
    status = _enum_column(
        FeedbackStatus, nullable=False, default=FeedbackStatus.NEW, index=True
    )

    escalation = db.relationship(
        "Escalation", back_populates="feedback", uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Feedback id={self.id} category={self.category.value} urgency={self.urgency.value}>"
