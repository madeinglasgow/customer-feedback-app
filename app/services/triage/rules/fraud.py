from app.models import UrgencyLevel
from app.services.triage.keywords import FRAUD_INDICATORS
from app.services.triage.rules.base import SeverityRule, contains_term
from app.services.types import PriorityAssessment


class SuspectedFraudRule(SeverityRule):
    """Suspected fraud or unauthorized charges are treated as critical.

    Fraud reports arrive under several categories (billing, other, even
    customer service), so this rule runs for all of them.
    """

    name = "suspected_fraud"

    def evaluate(self, message, category, order_id):
        term = contains_term(message, FRAUD_INDICATORS)
        if term is None:
            return None
        return PriorityAssessment(
            level=UrgencyLevel.CRITICAL,
            rule=self.name,
            rationale=f"suspected_fraud: unauthorized charge indicators ('{term}')",
        )
