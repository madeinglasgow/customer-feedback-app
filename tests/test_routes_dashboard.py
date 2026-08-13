from datetime import datetime, timedelta

from app.models import (
    Escalation,
    Feedback,
    FeedbackCategory,
    FeedbackStatus,
    Notification,
    NotificationStatus,
    UrgencyLevel,
)


def add_feedback(session, **overrides):
    values = dict(
        customer_name="Dash Tester",
        customer_email="dash@example.com",
        message="Something happened",
        category=FeedbackCategory.PRODUCT,
        urgency=UrgencyLevel.NORMAL,
        status=FeedbackStatus.NEW,
    )
    values.update(overrides)
    feedback = Feedback(**values)
    session.add(feedback)
    session.commit()
    return feedback


def add_escalation(session, feedback, **overrides):
    values = dict(feedback_id=feedback.id, reason="test escalation reason")
    values.update(overrides)
    escalation = Escalation(**values)
    session.add(escalation)
    session.commit()
    return escalation


class TestList:
    def test_lists_feedback(self, client, db_session):
        add_feedback(db_session, customer_name="Visible Person")
        response = client.get("/dashboard/")
        assert response.status_code == 200
        assert b"Visible Person" in response.data

    def test_filter_by_category(self, client, db_session):
        add_feedback(db_session, customer_name="Billing Person", category=FeedbackCategory.BILLING)
        add_feedback(db_session, customer_name="Product Person", category=FeedbackCategory.PRODUCT)

        response = client.get("/dashboard/?category=billing")
        assert b"Billing Person" in response.data
        assert b"Product Person" not in response.data

    def test_filter_by_urgency_and_status(self, client, db_session):
        add_feedback(
            db_session,
            customer_name="Hot Item",
            urgency=UrgencyLevel.CRITICAL,
            status=FeedbackStatus.REVIEWING,
        )
        add_feedback(db_session, customer_name="Cold Item")

        response = client.get("/dashboard/?urgency=critical&status=reviewing")
        assert b"Hot Item" in response.data
        assert b"Cold Item" not in response.data

    def test_filter_by_date(self, client, db_session):
        add_feedback(
            db_session,
            customer_name="Old Item",
            created_at=datetime.utcnow() - timedelta(days=30),
        )
        add_feedback(db_session, customer_name="New Item")

        since = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        response = client.get(f"/dashboard/?since={since}")
        assert b"New Item" in response.data
        assert b"Old Item" not in response.data


class TestDetail:
    def test_detail_shows_escalation_and_notifications(self, client, db_session):
        feedback = add_feedback(db_session, urgency=UrgencyLevel.HIGH)
        escalation = add_escalation(db_session, feedback, reason="visible escalation reason")
        db_session.add(
            Notification(
                escalation_id=escalation.id,
                status=NotificationStatus.SUPPRESSED,
                detail="visible suppression detail",
            )
        )
        db_session.commit()

        response = client.get(f"/dashboard/feedback/{feedback.id}")
        assert response.status_code == 200
        assert b"visible escalation reason" in response.data
        assert b"visible suppression detail" in response.data

    def test_detail_without_escalation(self, client, db_session):
        feedback = add_feedback(db_session)
        response = client.get(f"/dashboard/feedback/{feedback.id}")
        assert b"not escalated" in response.data

    def test_missing_feedback_404s(self, client):
        assert client.get("/dashboard/feedback/9999").status_code == 404


class TestStatusUpdates:
    def test_mark_reviewing(self, client, db_session):
        feedback = add_feedback(db_session)
        response = client.post(
            f"/dashboard/feedback/{feedback.id}/status", data={"status": "reviewing"}
        )
        assert response.status_code == 302
        db_session.refresh(feedback)
        assert feedback.status == FeedbackStatus.REVIEWING

    def test_resolving_feedback_resolves_escalation(self, client, db_session):
        feedback = add_feedback(db_session, urgency=UrgencyLevel.HIGH)
        escalation = add_escalation(db_session, feedback)

        client.post(f"/dashboard/feedback/{feedback.id}/status", data={"status": "resolved"})

        db_session.refresh(feedback)
        db_session.refresh(escalation)
        assert feedback.status == FeedbackStatus.RESOLVED
        assert escalation.is_resolved is True
        assert escalation.resolved_at is not None

    def test_invalid_status_400s(self, client, db_session):
        feedback = add_feedback(db_session)
        response = client.post(
            f"/dashboard/feedback/{feedback.id}/status", data={"status": "closed"}
        )
        assert response.status_code == 400

    def test_resolve_escalation_endpoint_resolves_feedback_too(self, client, db_session):
        feedback = add_feedback(db_session, urgency=UrgencyLevel.CRITICAL)
        escalation = add_escalation(db_session, feedback)

        response = client.post(f"/dashboard/escalations/{escalation.id}/resolve")
        assert response.status_code == 302

        db_session.refresh(feedback)
        db_session.refresh(escalation)
        assert escalation.is_resolved is True
        assert feedback.status == FeedbackStatus.RESOLVED
