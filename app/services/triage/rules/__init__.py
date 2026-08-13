from typing import Callable

from app.services.triage.rules.base import SeverityRule, contains_term
from app.services.triage.rules.billing import RepeatedBillingFailureRule
from app.services.triage.rules.category_defaults import CategoryBaselineRule
from app.services.triage.rules.churn import ChurnThreatRule
from app.services.triage.rules.fraud import SuspectedFraudRule
from app.services.triage.rules.safety import SafetyHazardRule
from app.services.triage.rules.sentiment import ComplimentRule
from app.services.triage.rules.shipping import LostPackageRule


def build_default_ruleset(
    billing_history_lookup: Callable[[str], int] | None = None,
) -> list[SeverityRule]:
    """Assemble the standard rule set in evaluation order.

    ``billing_history_lookup`` maps a customer email to the count of that
    customer's recent billing complaints (see FeedbackRepository).
    """
    return [
        SafetyHazardRule(),
        SuspectedFraudRule(),
        ChurnThreatRule(),
        RepeatedBillingFailureRule(history_lookup=billing_history_lookup),
        LostPackageRule(),
        ComplimentRule(),
        CategoryBaselineRule(),
    ]


__all__ = [
    "CategoryBaselineRule",
    "ChurnThreatRule",
    "ComplimentRule",
    "LostPackageRule",
    "RepeatedBillingFailureRule",
    "SafetyHazardRule",
    "SeverityRule",
    "SuspectedFraudRule",
    "build_default_ruleset",
    "contains_term",
]
