import logging

import pytest

from app.models import (
    Escalation,
    Feedback,
    FeedbackCategory,
    Notification,
    NotificationStatus,
    UrgencyLevel,
)
from app.services.notifications import (
    OutboxNotificationService,
    requires_immediate_attention,
)


def make_escalated_feedback(db_session, urgency=UrgencyLevel.CRITICAL):
    feedback = Feedback(
        customer_name="Test",
        customer_email="test@example.com",
        message="msg",
        category=FeedbackCategory.BILLING,
        urgency=urgency,
    )
    db_session.add(feedback)
    db_session.flush()
    escalation = Escalation(feedback_id=feedback.id, reason="test reason")
    db_session.add(escalation)
    db_session.flush()
    return feedback, escalation


def config(enabled=True, min_urgency="high", team="cs-team-inbox"):
    return {
        "NOTIFICATIONS_ENABLED": enabled,
        "NOTIFICATION_MIN_URGENCY": min_urgency,
        "SUPPORT_TEAM_ID": team,
    }


class TestRequiresImmediateAttention:
    def test_at_threshold_is_true(self):
        assert requires_immediate_attention(UrgencyLevel.HIGH, UrgencyLevel.HIGH)

    def test_above_threshold_is_true(self):
        assert requires_immediate_attention(UrgencyLevel.CRITICAL, UrgencyLevel.HIGH)

    def test_below_threshold_is_false(self):
        assert not requires_immediate_attention(UrgencyLevel.HIGH, UrgencyLevel.CRITICAL)


class TestSentPath:
    def test_sent_notification_recorded(self, db_session):
        feedback, escalation = make_escalated_feedback(db_session)
        service = OutboxNotificationService(db_session, config(team="cs-alerts"))

        notification = service.notify_escalation(escalation, feedback)

        assert notification.status == NotificationStatus.SENT
        assert notification.recipient == "cs-alerts"
        assert notification.sent_at is not None
        assert escalation.notified_at == notification.sent_at
        assert str(feedback.id) in notification.subject


class TestThresholdSuppression:
    def test_below_threshold_writes_suppressed_row(self, db_session, caplog):
        feedback, escalation = make_escalated_feedback(db_session, urgency=UrgencyLevel.HIGH)
        service = OutboxNotificationService(db_session, config(min_urgency="critical"))

        with caplog.at_level(logging.WARNING, logger="feedback.notifications"):
            notification = service.notify_escalation(escalation, feedback)

        assert notification.status == NotificationStatus.SUPPRESSED
        assert "below immediate-attention threshold critical" in notification.detail
        assert escalation.notified_at is None
        assert any("notification suppressed" in r.message for r in caplog.records)


class TestDisabledSuppression:
    def test_disabled_writes_no_row_and_logs(self, db_session, caplog):
        feedback, escalation = make_escalated_feedback(db_session)
        service = OutboxNotificationService(db_session, config(enabled=False))

        with caplog.at_level(logging.WARNING, logger="feedback.notifications"):
            result = service.notify_escalation(escalation, feedback)

        assert result is None
        assert db_session.query(Notification).count() == 0
        assert escalation.notified_at is None
        assert any(
            "notifications disabled" in r.getMessage() for r in caplog.records
        )
