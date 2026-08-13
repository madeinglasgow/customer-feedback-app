"""Service construction helpers.

Routes and scripts use these builders so services are wired consistently:
the triage engine gets its billing-history lookup from the feedback
repository, and the notification service reads the active app config.
"""

from app.repositories import (
    EscalationRepository,
    FeedbackRepository,
    NotificationRepository,
)
from app.services.escalation_policy import EscalationPolicy
from app.services.intake_service import FeedbackIntakeService
from app.services.notifications import OutboxNotificationService
from app.services.triage import TriageEngine, build_default_ruleset
from app.services.workflow_service import FeedbackWorkflowService


def build_intake_service(session, config) -> FeedbackIntakeService:
    feedback_repository = FeedbackRepository(session)
    rules = build_default_ruleset(
        billing_history_lookup=feedback_repository.count_recent_billing_complaints
    )
    return FeedbackIntakeService(
        session=session,
        feedback_repository=feedback_repository,
        escalation_repository=EscalationRepository(session),
        triage_engine=TriageEngine(rules),
        escalation_policy=EscalationPolicy(),
        notification_service=OutboxNotificationService(session, config),
    )


def build_workflow_service(session) -> FeedbackWorkflowService:
    return FeedbackWorkflowService(
        session=session,
        feedback_repository=FeedbackRepository(session),
        escalation_repository=EscalationRepository(session),
    )


__all__ = [
    "EscalationPolicy",
    "FeedbackIntakeService",
    "FeedbackWorkflowService",
    "NotificationRepository",
    "OutboxNotificationService",
    "build_intake_service",
    "build_workflow_service",
]
