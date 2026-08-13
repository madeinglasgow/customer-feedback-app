"""End-to-end intake tests: submission through triage, escalation, notification."""

import logging

from app.models import (
    Escalation,
    FeedbackCategory,
    Notification,
    NotificationStatus,
    UrgencyLevel,
)
from app.services import build_intake_service
from tests.conftest import make_submission


class TestCriticalFlow:
    def test_safety_report_full_pipeline(self, app, db_session, intake, caplog):
        with caplog.at_level(logging.INFO, logger="feedback"):
            feedback = intake.submit(
                make_submission(
                    message="The space heater started sparking and smoking overnight",
                    category=FeedbackCategory.PRODUCT,
                )
            )

        assert feedback.urgency == UrgencyLevel.CRITICAL

        escalation = db_session.query(Escalation).one()
        assert escalation.feedback_id == feedback.id
        assert "safety_hazard" in escalation.reason

        notification = db_session.query(Notification).one()
        assert notification.status == NotificationStatus.SENT
        assert notification.recipient == app.config["SUPPORT_TEAM_ID"]
        assert escalation.notified_at is not None

        messages = [r.getMessage() for r in caplog.records]
        assert any("feedback received" in m for m in messages)
        assert any("priority assessed" in m for m in messages)
        assert any("escalation created" in m for m in messages)
        assert any("notification dispatched" in m for m in messages)


class TestHighNotEscalatedFlow:
    def test_shipping_churn_without_order_id_not_escalated(self, db_session, intake):
        feedback = intake.submit(
            make_submission(
                message="My order is missing and I am taking my business elsewhere",
                category=FeedbackCategory.SHIPPING,
                order_id=None,
            )
        )

        assert feedback.urgency == UrgencyLevel.HIGH
        assert db_session.query(Escalation).count() == 0

    def test_same_complaint_with_order_id_is_escalated(self, db_session, intake):
        feedback = intake.submit(
            make_submission(
                message="My order is missing and I am taking my business elsewhere",
                category=FeedbackCategory.SHIPPING,
                order_id="ORD-777",
            )
        )

        assert feedback.urgency == UrgencyLevel.HIGH
        assert db_session.query(Escalation).count() == 1


class TestBillingHistoryFlow:
    def test_third_billing_complaint_is_high_even_when_mild(self, db_session, app):
        intake = build_intake_service(db_session, app.config)
        email = "unlucky@example.com"

        first = intake.submit(
            make_submission(
                customer_email=email,
                message="My payment did not go through",
                category=FeedbackCategory.BILLING,
            )
        )
        second = intake.submit(
            make_submission(
                customer_email=email,
                message="Payment declined once more, please advise",
                category=FeedbackCategory.BILLING,
            )
        )
        third = intake.submit(
            make_submission(
                customer_email=email,
                message="The payment failed today",
                category=FeedbackCategory.BILLING,
            )
        )

        assert first.urgency == UrgencyLevel.NORMAL
        assert second.urgency == UrgencyLevel.NORMAL
        assert third.urgency == UrgencyLevel.HIGH


class TestSuppressedNotificationFlow:
    def test_high_billing_with_critical_threshold_suppressed(self, app, db_session):
        app.config["NOTIFICATION_MIN_URGENCY"] = "critical"
        intake = build_intake_service(db_session, app.config)

        feedback = intake.submit(
            make_submission(
                message="I was charged twice for the same subscription",
                category=FeedbackCategory.BILLING,
            )
        )

        assert feedback.urgency == UrgencyLevel.HIGH
        escalation = db_session.query(Escalation).one()
        notification = db_session.query(Notification).one()
        assert notification.status == NotificationStatus.SUPPRESSED
        assert "below immediate-attention threshold" in notification.detail
        assert escalation.notified_at is None

    def test_disabled_notifications_leave_no_outbox_row(self, app, db_session, caplog):
        app.config["NOTIFICATIONS_ENABLED"] = False
        intake = build_intake_service(db_session, app.config)

        with caplog.at_level(logging.WARNING, logger="feedback.notifications"):
            intake.submit(
                make_submission(
                    message="I was charged twice for the same subscription",
                    category=FeedbackCategory.BILLING,
                )
            )

        assert db_session.query(Escalation).count() == 1
        assert db_session.query(Notification).count() == 0
        assert any("notifications disabled" in r.getMessage() for r in caplog.records)
