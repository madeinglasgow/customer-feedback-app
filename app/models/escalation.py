from datetime import datetime

from app.extensions import db


class Escalation(db.Model):
    __tablename__ = "escalations"

    id = db.Column(db.Integer, primary_key=True)
    feedback_id = db.Column(
        db.Integer, db.ForeignKey("feedback.id"), nullable=False, unique=True
    )
    reason = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_resolved = db.Column(db.Boolean, nullable=False, default=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    # Timestamp of the last successful alert to the support team.
    # Null means the team was never successfully notified about this escalation.
    notified_at = db.Column(db.DateTime, nullable=True)

    feedback = db.relationship("Feedback", back_populates="escalation")
    notifications = db.relationship(
        "Notification", back_populates="escalation",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Escalation id={self.id} feedback_id={self.feedback_id} reason={self.reason!r}>"
