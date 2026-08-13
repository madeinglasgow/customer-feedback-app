from app.models import FeedbackCategory, UrgencyLevel
from app.services.triage.rules.base import SeverityRule
from app.services.types import PriorityAssessment

#: Baseline severity when no specific rule fires.
CATEGORY_BASELINES = {
    FeedbackCategory.PRODUCT: UrgencyLevel.NORMAL,
    FeedbackCategory.SHIPPING: UrgencyLevel.NORMAL,
    FeedbackCategory.BILLING: UrgencyLevel.NORMAL,
    FeedbackCategory.RETURNS: UrgencyLevel.NORMAL,
    FeedbackCategory.CUSTOMER_SERVICE: UrgencyLevel.NORMAL,
    FeedbackCategory.OTHER: UrgencyLevel.LOW,
}


class CategoryBaselineRule(SeverityRule):
    """Fallback rule providing each category's baseline severity.

    Always fires, but as a fallback it is only consulted when no specific
    rule produced an assessment.
    """

    name = "category_baseline"
    is_fallback = True

    def evaluate(self, message, category, order_id):
        level = CATEGORY_BASELINES.get(category, UrgencyLevel.NORMAL)
        return PriorityAssessment(
            level=level,
            rule=self.name,
            rationale=f"category_baseline: default for {category.value}",
        )
