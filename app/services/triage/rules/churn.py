from app.models import UrgencyLevel
from app.services.triage.keywords import CHURN_PHRASES
from app.services.triage.rules.base import SeverityRule, contains_term
from app.services.types import PriorityAssessment


class ChurnThreatRule(SeverityRule):
    """A customer explicitly threatening to leave gets high priority."""

    name = "churn_threat"

    def evaluate(self, message, category, order_id):
        phrase = contains_term(message, CHURN_PHRASES)
        if phrase is None:
            return None
        return PriorityAssessment(
            level=UrgencyLevel.HIGH,
            rule=self.name,
            rationale=f"churn_threat: customer threatening to leave ('{phrase}')",
        )
