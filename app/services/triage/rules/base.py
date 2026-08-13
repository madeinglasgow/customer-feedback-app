import re
from abc import ABC, abstractmethod

from app.models import FeedbackCategory
from app.services.types import PriorityAssessment


def contains_term(message: str, terms: list[str]) -> str | None:
    """Return the first term found in the message, or None.

    Terms are matched case-insensitively on word boundaries, so "fire" does
    not match "fired". Phrases (terms containing spaces) are matched as whole
    phrases.
    """
    lowered = message.lower()
    for term in terms:
        pattern = r"\b" + re.escape(term.lower()) + r"\b"
        if re.search(pattern, lowered):
            return term
    return None


class SeverityRule(ABC):
    """A single deterministic rule contributing to a priority assessment.

    Rules are evaluated by the TriageEngine; the highest severity among all
    applicable rules wins.
    """

    #: Stable identifier recorded in assessment rationales and logs.
    name: str = "base"

    def applies_to(self, category: FeedbackCategory) -> bool:
        """Whether this rule should run for feedback in the given category."""
        return True

    @abstractmethod
    def evaluate(
        self,
        message: str,
        category: FeedbackCategory,
        order_id: str | None,
    ) -> PriorityAssessment | None:
        """Return an assessment if this rule fires, else None."""
