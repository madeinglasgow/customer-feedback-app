"""Feedback intake pipeline: store, triage, escalate, notify."""

import logging

from app.models import Escalation, Feedback
from app.repositories import EscalationRepository, FeedbackRepository
from app.services.escalation_policy import EscalationPolicy
from app.services.notifications import NotificationService
from app.services.triage import TriageEngine
from app.services.types import FeedbackSubmission

logger = logging.getLogger("feedback.intake")


class FeedbackIntakeService:
    """Orchestrates the full intake pipeline for a validated submission.

    Validation happens before this service is called (see validation.py);
    intake assumes it receives a well-formed FeedbackSubmission.
    """

    def __init__(
        self,
        session,
        feedback_repository: FeedbackRepository,
        escalation_repository: EscalationRepository,
        triage_engine: TriageEngine,
        escalation_policy: EscalationPolicy,
        notification_service: NotificationService,
    ):
        self.session = session
        self.feedback_repository = feedback_repository
        self.escalation_repository = escalation_repository
        self.triage_engine = triage_engine
        self.escalation_policy = escalation_policy
        self.notification_service = notification_service

    def submit(self, submission: FeedbackSubmission) -> Feedback:
        # Triage runs before the record is persisted so that history-based
        # rules (e.g. repeated billing failures) only see *prior* feedback.
        assessment = self.triage_engine.assess(submission)

        feedback = Feedback(
            customer_name=submission.customer_name,
            customer_email=submission.customer_email,
            message=submission.message,
            category=submission.category,
            order_id=submission.order_id,
            urgency=assessment.level,
        )
        self.feedback_repository.add(feedback)
        logger.info(
            "feedback received: id=%s category=%s urgency=%s email=%s",
            feedback.id,
            feedback.category.value,
            feedback.urgency.value,
            feedback.customer_email,
        )

        reason = self.escalation_policy.should_escalate(feedback, assessment)
        if reason is not None:
            escalation = Escalation(feedback_id=feedback.id, reason=reason)
            self.escalation_repository.add(escalation)
            logger.info(
                "escalation created: id=%s feedback_id=%s reason=%s",
                escalation.id,
                feedback.id,
                reason,
            )
            self.notification_service.notify_escalation(escalation, feedback)

        self.session.commit()
        return feedback
