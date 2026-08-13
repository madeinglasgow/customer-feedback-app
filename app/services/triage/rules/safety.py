from app.models import FeedbackCategory, UrgencyLevel
from app.services.triage.keywords import SAFETY_TERMS
from app.services.triage.rules.base import SeverityRule, contains_term
from app.services.types import PriorityAssessment


class SafetyHazardRule(SeverityRule):
    """Physical danger or product safety problems demand immediate attention.

    Applies to every category: a safety issue reported through, say, a
    shipping complaint is still a safety issue.
    """

    name = "safety_hazard"

    def evaluate(self, message, category, order_id):
        term = contains_term(message, SAFETY_TERMS)
        if term is None:
            return None
        return PriorityAssessment(
            level=UrgencyLevel.CRITICAL,
            rule=self.name,
            rationale=f"safety_hazard: message mentions '{term}'",
        )
