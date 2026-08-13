"""Status transitions for feedback and escalations."""

import logging
from datetime import datetime

from app.models import Feedback, FeedbackStatus
from app.repositories import EscalationRepository, FeedbackRepository

logger = logging.getLogger("feedback.workflow")


class UnknownStatusError(ValueError):
    """Raised when a status transition targets an unknown status value."""


class FeedbackWorkflowService:
    """Handles staff actions on existing feedback records."""

    def __init__(
        self,
        session,
        feedback_repository: FeedbackRepository,
        escalation_repository: EscalationRepository,
    ):
        self.session = session
        self.feedback_repository = feedback_repository
        self.escalation_repository = escalation_repository

    def update_status(self, feedback: Feedback, status_value: str) -> Feedback:
        try:
            status = FeedbackStatus(status_value)
        except ValueError:
            raise UnknownStatusError(f"unknown feedback status: {status_value!r}") from None

        feedback.status = status
        if status == FeedbackStatus.RESOLVED:
            self._resolve_escalation_if_any(feedback)
            logger.info("feedback resolved: id=%s", feedback.id)
        else:
            logger.info(
                "feedback status changed: id=%s status=%s", feedback.id, status.value
            )
        self.session.commit()
        return feedback

    def resolve_escalation(self, escalation) -> None:
        """Resolve an escalation and its underlying feedback together."""
        escalation.is_resolved = True
        escalation.resolved_at = datetime.utcnow()
        escalation.feedback.status = FeedbackStatus.RESOLVED
        logger.info(
            "escalation resolved: id=%s feedback_id=%s",
            escalation.id,
            escalation.feedback_id,
        )
        logger.info("feedback resolved: id=%s", escalation.feedback_id)
        self.session.commit()

    def _resolve_escalation_if_any(self, feedback: Feedback) -> None:
        escalation = feedback.escalation
        if escalation is not None and not escalation.is_resolved:
            escalation.is_resolved = True
            escalation.resolved_at = datetime.utcnow()
            logger.info(
                "escalation resolved: id=%s feedback_id=%s",
                escalation.id,
                feedback.id,
            )
