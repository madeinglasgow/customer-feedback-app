from datetime import datetime

import sqlalchemy as sa

from app.extensions import db
from app.models.enums import NotificationStatus


class Notification(db.Model):
    """Outbox record of an alert to the customer-service team.

    No real email or chat message is sent; rows in this table are the
    system of record for what would have gone out.
    """

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    escalation_id = db.Column(
        db.Integer, db.ForeignKey("escalations.id"), nullable=False
    )
    channel = db.Column(db.String(20), nullable=False, default="outbox")
    recipient = db.Column(db.String(120), nullable=True)
    subject = db.Column(db.String(200), nullable=True)
    body = db.Column(db.Text, nullable=True)
    status = db.Column(
        sa.Enum(NotificationStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    # Human-readable explanation for suppressed or failed notifications.
    detail = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime, nullable=True)

    escalation = db.relationship("Escalation", back_populates="notifications")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Notification id={self.id} status={self.status.value}>"
