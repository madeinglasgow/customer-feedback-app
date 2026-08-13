from datetime import datetime, timedelta

from app.models import Feedback, FeedbackCategory, FeedbackStatus, UrgencyLevel
from app.repositories import FeedbackRepository


def add_feedback(session, days_ago=0, **overrides):
    values = dict(
        customer_name="Test",
        customer_email="test@example.com",
        message="msg",
        category=FeedbackCategory.PRODUCT,
        urgency=UrgencyLevel.NORMAL,
        status=FeedbackStatus.NEW,
        created_at=datetime.utcnow() - timedelta(days=days_ago),
    )
    values.update(overrides)
    feedback = Feedback(**values)
    session.add(feedback)
    session.flush()
    return feedback


class TestPersistence:
    def test_round_trip(self, db_session):
        feedback = add_feedback(db_session, order_id="ORD-9")
        db_session.commit()

        repository = FeedbackRepository(db_session)
        loaded = repository.get(feedback.id)
        assert loaded.order_id == "ORD-9"
        assert loaded.category == FeedbackCategory.PRODUCT
        assert loaded.status == FeedbackStatus.NEW


class TestSearch:
    def test_filter_by_category_and_status(self, db_session):
        add_feedback(db_session, category=FeedbackCategory.BILLING)
        match = add_feedback(
            db_session,
            category=FeedbackCategory.SHIPPING,
            status=FeedbackStatus.REVIEWING,
        )
        add_feedback(db_session, category=FeedbackCategory.SHIPPING)

        results = FeedbackRepository(db_session).search(
            category=FeedbackCategory.SHIPPING, status=FeedbackStatus.REVIEWING
        )
        assert [r.id for r in results] == [match.id]

    def test_filter_by_urgency(self, db_session):
        add_feedback(db_session, urgency=UrgencyLevel.CRITICAL)
        add_feedback(db_session, urgency=UrgencyLevel.LOW)

        results = FeedbackRepository(db_session).search(urgency=UrgencyLevel.CRITICAL)
        assert len(results) == 1
        assert results[0].urgency == UrgencyLevel.CRITICAL

    def test_filter_by_date_range(self, db_session):
        old = add_feedback(db_session, days_ago=10)
        recent = add_feedback(db_session, days_ago=1)

        repository = FeedbackRepository(db_session)
        since = datetime.utcnow() - timedelta(days=5)
        results = repository.search(since=since)
        assert [r.id for r in results] == [recent.id]

        results = repository.search(until=since)
        assert [r.id for r in results] == [old.id]

    def test_results_ordered_newest_first(self, db_session):
        older = add_feedback(db_session, days_ago=3)
        newer = add_feedback(db_session, days_ago=1)

        results = FeedbackRepository(db_session).search()
        assert [r.id for r in results] == [newer.id, older.id]


class TestBillingComplaintHistory:
    def test_counts_only_recent_billing_complaints_for_customer(self, db_session):
        email = "repeat@example.com"
        add_feedback(db_session, customer_email=email, category=FeedbackCategory.BILLING, days_ago=5)
        add_feedback(db_session, customer_email=email, category=FeedbackCategory.BILLING, days_ago=15)
        # Outside the 30-day window:
        add_feedback(db_session, customer_email=email, category=FeedbackCategory.BILLING, days_ago=31)
        # Different category:
        add_feedback(db_session, customer_email=email, category=FeedbackCategory.PRODUCT, days_ago=2)
        # Different customer:
        add_feedback(db_session, customer_email="other@example.com", category=FeedbackCategory.BILLING, days_ago=2)

        repository = FeedbackRepository(db_session)
        assert repository.count_recent_billing_complaints(email, days=30) == 2
