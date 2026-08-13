from app.models import Escalation


class EscalationRepository:
    """Data access for Escalation records."""

    def __init__(self, session):
        self.session = session

    def add(self, escalation: Escalation) -> Escalation:
        self.session.add(escalation)
        self.session.flush()
        return escalation

    def get(self, escalation_id: int) -> Escalation | None:
        return self.session.get(Escalation, escalation_id)

    def for_feedback(self, feedback_id: int) -> Escalation | None:
        return (
            self.session.query(Escalation)
            .filter(Escalation.feedback_id == feedback_id)
            .one_or_none()
        )
