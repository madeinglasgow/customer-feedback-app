import logging

from app.models import UrgencyLevel
from app.services.triage.rules.base import SeverityRule
from app.services.types import FeedbackSubmission, PriorityAssessment

logger = logging.getLogger("feedback.triage")

#: Ordering used to compare severities; higher value wins.
SEVERITY_ORDER = {
    UrgencyLevel.LOW: 0,
    UrgencyLevel.NORMAL: 1,
    UrgencyLevel.HIGH: 2,
    UrgencyLevel.CRITICAL: 3,
}


class TriageEngine:
    """Runs every applicable severity rule and keeps the highest assessment.

    Ties between rules producing the same severity go to the rule registered
    first, so registration order in DEFAULT_RULESET matters.
    """

    def __init__(self, rules: list[SeverityRule]):
        self.rules = rules

    def assess(self, submission: FeedbackSubmission) -> PriorityAssessment:
        best: PriorityAssessment | None = None
        for rule in self.rules:
            if not rule.applies_to(submission.category):
                continue
            if hasattr(rule, "bind_customer"):
                rule.bind_customer(submission.customer_email)
            assessment = rule.evaluate(
                submission.message, submission.category, submission.order_id
            )
            if assessment is None:
                continue
            if best is None or SEVERITY_ORDER[assessment.level] > SEVERITY_ORDER[best.level]:
                best = assessment

        if best is None:  # cannot happen while CategoryBaselineRule is registered
            best = PriorityAssessment(
                level=UrgencyLevel.NORMAL, rule="fallback", rationale="no rule fired"
            )

        logger.info(
            "priority assessed: level=%s rule=%s category=%s",
            best.level.value,
            best.rule,
            submission.category.value,
        )
        return best
