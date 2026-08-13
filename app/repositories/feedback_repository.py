from datetime import datetime, timedelta

from app.models import Feedback, FeedbackCategory, FeedbackStatus, UrgencyLevel


class FeedbackRepository:
    """Data access for Feedback records."""

    def __init__(self, session):
        self.session = session

    def add(self, feedback: Feedback) -> Feedback:
        self.session.add(feedback)
        self.session.flush()
        return feedback

    def get(self, feedback_id: int) -> Feedback | None:
        return self.session.get(Feedback, feedback_id)

    def search(
        self,
        category: FeedbackCategory | None = None,
        urgency: UrgencyLevel | None = None,
        status: FeedbackStatus | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[Feedback]:
        query = self.session.query(Feedback)
        if category is not None:
            query = query.filter(Feedback.category == category)
        if urgency is not None:
            query = query.filter(Feedback.urgency == urgency)
        if status is not None:
            query = query.filter(Feedback.status == status)
        if since is not None:
            query = query.filter(Feedback.created_at >= since)
        if until is not None:
            query = query.filter(Feedback.created_at <= until)
        return query.order_by(Feedback.created_at.desc()).all()

    def count_recent_billing_complaints(self, customer_email: str, days: int = 30) -> int:
        """Number of billing feedback items from this customer within the window.

        Used by triage to detect customers with repeated billing problems even
        when an individual message sounds mild.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        return (
            self.session.query(Feedback)
            .filter(
                Feedback.customer_email == customer_email,
                Feedback.category == FeedbackCategory.BILLING,
                Feedback.created_at >= cutoff,
            )
            .count()
        )
