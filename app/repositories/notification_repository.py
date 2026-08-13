from app.models import Notification


class NotificationRepository:
    """Data access for Notification outbox records."""

    def __init__(self, session):
        self.session = session

    def add(self, notification: Notification) -> Notification:
        self.session.add(notification)
        self.session.flush()
        return notification

    def for_escalation(self, escalation_id: int) -> list[Notification]:
        return (
            self.session.query(Notification)
            .filter(Notification.escalation_id == escalation_id)
            .order_by(Notification.created_at)
            .all()
        )
