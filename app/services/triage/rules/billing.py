from typing import Callable

from app.models import FeedbackCategory, UrgencyLevel
from app.services.triage.keywords import BILLING_RETRY_PHRASES
from app.services.triage.rules.base import SeverityRule, contains_term
from app.services.types import PriorityAssessment

#: Prior billing complaints (within the lookback window) at or above which a
#: new billing complaint is treated as part of a repeated-failure pattern.
REPEAT_COMPLAINT_THRESHOLD = 2


class RepeatedBillingFailureRule(SeverityRule):
    """Repeated billing failures get high priority.

    Fires in two situations:
    - the message itself describes repeated charging problems, or
    - the customer has a recent history of billing complaints, even when the
      current message sounds mild. History is looked up through the injected
      ``history_lookup`` callable (customer email -> count of recent billing
      complaints).
    """

    name = "repeated_billing_failure"

    def __init__(self, history_lookup: Callable[[str], int] | None = None):
        self.history_lookup = history_lookup
        self._current_email: str | None = None

    def applies_to(self, category: FeedbackCategory) -> bool:
        return category == FeedbackCategory.BILLING

    def bind_customer(self, customer_email: str) -> None:
        """Tell the rule which customer the next evaluation concerns."""
        self._current_email = customer_email

    def evaluate(self, message, category, order_id):
        phrase = contains_term(message, BILLING_RETRY_PHRASES)
        if phrase is not None:
            return PriorityAssessment(
                level=UrgencyLevel.HIGH,
                rule=self.name,
                rationale=f"repeated_billing_failure: message indicates repetition ('{phrase}')",
            )

        if self.history_lookup is not None and self._current_email:
            prior = self.history_lookup(self._current_email)
            if prior >= REPEAT_COMPLAINT_THRESHOLD:
                return PriorityAssessment(
                    level=UrgencyLevel.HIGH,
                    rule=self.name,
                    rationale=(
                        f"repeated_billing_failure: {prior} recent billing complaints "
                        "on file for this customer"
                    ),
                )
        return None
