import pytest

from app.models import Feedback, FeedbackCategory, UrgencyLevel
from app.services.escalation_policy import EscalationPolicy
from app.services.types import PriorityAssessment


def feedback_for(category, order_id=None):
    return Feedback(
        customer_name="Test",
        customer_email="test@example.com",
        message="msg",
        category=category,
        order_id=order_id,
    )


def assessment(level, rule="test_rule", rationale="test rationale"):
    return PriorityAssessment(level=level, rule=rule, rationale=rationale)


@pytest.fixture()
def policy():
    return EscalationPolicy()


class TestCriticalAlwaysEscalates:
    @pytest.mark.parametrize("category", list(FeedbackCategory))
    def test_critical_escalates_in_every_category(self, policy, category):
        reason = policy.should_escalate(
            feedback_for(category), assessment(UrgencyLevel.CRITICAL)
        )
        assert reason == "test rationale"


class TestHighByCategory:
    def test_billing_high_always_escalates(self, policy):
        reason = policy.should_escalate(
            feedback_for(FeedbackCategory.BILLING),
            assessment(UrgencyLevel.HIGH, rule="repeated_billing_failure"),
        )
        assert reason is not None

    def test_shipping_high_with_order_id_escalates(self, policy):
        reason = policy.should_escalate(
            feedback_for(FeedbackCategory.SHIPPING, order_id="ORD-1"),
            assessment(UrgencyLevel.HIGH, rule="lost_package"),
        )
        assert reason is not None

    def test_shipping_high_without_order_id_does_not_escalate(self, policy):
        reason = policy.should_escalate(
            feedback_for(FeedbackCategory.SHIPPING),
            assessment(UrgencyLevel.HIGH, rule="churn_threat"),
        )
        assert reason is None

    def test_returns_high_escalates_only_for_churn(self, policy):
        churn = policy.should_escalate(
            feedback_for(FeedbackCategory.RETURNS),
            assessment(UrgencyLevel.HIGH, rule="churn_threat"),
        )
        other = policy.should_escalate(
            feedback_for(FeedbackCategory.RETURNS),
            assessment(UrgencyLevel.HIGH, rule="some_other_rule"),
        )
        assert churn is not None
        assert other is None

    @pytest.mark.parametrize(
        "category",
        [FeedbackCategory.PRODUCT, FeedbackCategory.CUSTOMER_SERVICE, FeedbackCategory.OTHER],
    )
    def test_default_categories_escalate_for_churn_and_safety_only(self, policy, category):
        assert (
            policy.should_escalate(
                feedback_for(category), assessment(UrgencyLevel.HIGH, rule="churn_threat")
            )
            is not None
        )
        assert (
            policy.should_escalate(
                feedback_for(category), assessment(UrgencyLevel.HIGH, rule="other_rule")
            )
            is None
        )


class TestLowerLevelsNeverEscalate:
    @pytest.mark.parametrize("level", [UrgencyLevel.NORMAL, UrgencyLevel.LOW])
    @pytest.mark.parametrize("category", list(FeedbackCategory))
    def test_normal_and_low_never_escalate(self, policy, level, category):
        assert policy.should_escalate(feedback_for(category), assessment(level)) is None
