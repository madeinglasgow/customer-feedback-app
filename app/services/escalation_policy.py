"""Rules deciding whether classified feedback becomes an escalation.

Escalation is a separate decision from urgency. Critical items always
escalate; high-urgency items escalate only under category-specific
conditions described in docs/customer_support_process.md.
"""

import logging

from app.models import Feedback, FeedbackCategory, UrgencyLevel
from app.services.types import PriorityAssessment

logger = logging.getLogger("feedback.escalation")


def _escalate_billing_high(feedback: Feedback, assessment: PriorityAssessment) -> str | None:
    # High-urgency billing issues carry financial exposure; always escalate.
    return assessment.rationale


def _escalate_shipping_high(feedback: Feedback, assessment: PriorityAssessment) -> str | None:
    # Without an order reference the support team cannot trace a shipment,
    # so the item stays in the standard queue until the customer provides one.
    if feedback.order_id:
        return assessment.rationale
    return None


def _escalate_returns_high(feedback: Feedback, assessment: PriorityAssessment) -> str | None:
    # Routine return problems go through the standard queue; only retention
    # risks (customers threatening to leave) are escalated.
    if assessment.rule == "churn_threat":
        return assessment.rationale
    return None


def _escalate_default_high(feedback: Feedback, assessment: PriorityAssessment) -> str | None:
    # For remaining categories, escalate only for retention or safety signals.
    if assessment.rule in ("churn_threat", "safety_hazard"):
        return assessment.rationale
    return None


CATEGORY_ESCALATION_CHECKS = {
    FeedbackCategory.BILLING: _escalate_billing_high,
    FeedbackCategory.SHIPPING: _escalate_shipping_high,
    FeedbackCategory.RETURNS: _escalate_returns_high,
    FeedbackCategory.PRODUCT: _escalate_default_high,
    FeedbackCategory.CUSTOMER_SERVICE: _escalate_default_high,
    FeedbackCategory.OTHER: _escalate_default_high,
}


class EscalationPolicy:
    """Decides whether a piece of feedback warrants an escalation record."""

    def should_escalate(
        self, feedback: Feedback, assessment: PriorityAssessment
    ) -> str | None:
        """Return the escalation reason, or None if no escalation is needed."""
        if assessment.level == UrgencyLevel.CRITICAL:
            return assessment.rationale

        if assessment.level == UrgencyLevel.HIGH:
            check = CATEGORY_ESCALATION_CHECKS[feedback.category]
            reason = check(feedback, assessment)
            if reason is None:
                logger.info(
                    "escalation skipped: feedback_id=%s category=%s rule=%s",
                    feedback.id,
                    feedback.category.value,
                    assessment.rule,
                )
            return reason

        return None
