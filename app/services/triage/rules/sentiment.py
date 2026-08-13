from app.models import UrgencyLevel
from app.services.triage.keywords import NEGATIVE_TERMS, POSITIVE_TERMS
from app.services.triage.rules.base import SeverityRule, contains_term
from app.services.types import PriorityAssessment


class ComplimentRule(SeverityRule):
    """Pure compliments can wait.

    Only fires when positive language appears with no negative language —
    "I love it but it broke" is a complaint, not a compliment.
    """

    name = "compliment"

    def evaluate(self, message, category, order_id):
        positive = contains_term(message, POSITIVE_TERMS)
        if positive is None:
            return None
        if contains_term(message, NEGATIVE_TERMS) is not None:
            return None
        return PriorityAssessment(
            level=UrgencyLevel.LOW,
            rule=self.name,
            rationale=f"compliment: positive language ('{positive}') with no complaint indicators",
        )
