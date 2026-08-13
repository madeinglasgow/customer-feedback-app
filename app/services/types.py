from dataclasses import dataclass

from app.models import FeedbackCategory, UrgencyLevel


@dataclass(frozen=True)
class FeedbackSubmission:
    """A validated customer feedback submission, ready for intake."""

    customer_name: str
    customer_email: str
    message: str
    category: FeedbackCategory
    order_id: str | None = None


@dataclass(frozen=True)
class PriorityAssessment:
    """Result of triage: how severe a piece of feedback is and why."""

    level: UrgencyLevel
    rule: str
    rationale: str
