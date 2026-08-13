"""Customer-service notification handling.

Nothing is actually emailed or posted to chat. The OutboxNotificationService
writes rows to the notifications table (the "outbox"), which downstream
tooling would deliver in a real deployment.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime

from app.models import Escalation, Feedback, Notification, NotificationStatus, UrgencyLevel
from app.services.triage.engine import SEVERITY_ORDER

logger = logging.getLogger("feedback.notifications")


def requires_immediate_attention(level: UrgencyLevel, minimum: UrgencyLevel) -> bool:
    """Whether the given urgency meets the configured immediate-attention bar."""
    return SEVERITY_ORDER[level] >= SEVERITY_ORDER[minimum]


class NotificationService(ABC):
    @abstractmethod
    def notify_escalation(
        self, escalation: Escalation, feedback: Feedback
    ) -> Notification | None:
        """Alert the support team about an escalation, if configuration allows."""


class OutboxNotificationService(NotificationService):
    """Records outgoing alerts in the notifications table.

    Behavior is controlled by configuration:

    - ``NOTIFICATIONS_ENABLED``: master switch. When off, nothing is written
      to the outbox at all; the suppression is only visible in the logs.
    - ``NOTIFICATION_MIN_URGENCY``: escalations below this urgency get a
      ``suppressed`` outbox row instead of a ``sent`` one.
    - ``SUPPORT_TEAM_ID``: recipient team identifier for sent alerts.
    """

    def __init__(self, session, config):
        self.session = session
        self.enabled = bool(config["NOTIFICATIONS_ENABLED"])
        self.support_team_id = config["SUPPORT_TEAM_ID"]
        self.min_urgency = UrgencyLevel(config["NOTIFICATION_MIN_URGENCY"])

    def notify_escalation(self, escalation, feedback):
        if not self.enabled:
            logger.warning(
                "notification suppressed: notifications disabled "
                "(escalation_id=%s feedback_id=%s)",
                escalation.id,
                feedback.id,
            )
            return None

        if not requires_immediate_attention(feedback.urgency, self.min_urgency):
            detail = (
                f"urgency {feedback.urgency.value} below immediate-attention "
                f"threshold {self.min_urgency.value}"
            )
            notification = Notification(
                escalation_id=escalation.id,
                status=NotificationStatus.SUPPRESSED,
                recipient=self.support_team_id,
                detail=detail,
            )
            self.session.add(notification)
            logger.warning(
                "notification suppressed: %s (escalation_id=%s feedback_id=%s)",
                detail,
                escalation.id,
                feedback.id,
            )
            return notification

        notification = Notification(
            escalation_id=escalation.id,
            status=NotificationStatus.SENT,
            recipient=self.support_team_id,
            subject=f"[{feedback.urgency.value.upper()}] Feedback #{feedback.id} escalated",
            body=(
                f"Feedback #{feedback.id} from {feedback.customer_name} "
                f"({feedback.category.value}) was escalated: {escalation.reason}"
            ),
            sent_at=datetime.utcnow(),
        )
        self.session.add(notification)
        escalation.notified_at = notification.sent_at
        logger.info(
            "notification dispatched to team=%s (escalation_id=%s feedback_id=%s)",
            self.support_team_id,
            escalation.id,
            feedback.id,
        )
        return notification
