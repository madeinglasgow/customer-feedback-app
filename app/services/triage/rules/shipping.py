from app.models import FeedbackCategory, UrgencyLevel
from app.services.triage.rules.base import SeverityRule, contains_term
from app.services.types import PriorityAssessment

LOST_PACKAGE_TERMS = [
    "never arrived",
    "lost",
    "missing",
    "no sign of",
    "hasn't arrived",
    "has not arrived",
]


class LostPackageRule(SeverityRule):
    """Lost or missing shipments.

    With an order ID the shipment can be traced immediately, so the item is
    high priority. Without one, support cannot trace anything until the
    customer replies with more detail, so it stays at normal priority.
    """

    name = "lost_package"

    def applies_to(self, category: FeedbackCategory) -> bool:
        return category == FeedbackCategory.SHIPPING

    def evaluate(self, message, category, order_id):
        term = contains_term(message, LOST_PACKAGE_TERMS)
        if term is None:
            return None
        if order_id:
            return PriorityAssessment(
                level=UrgencyLevel.HIGH,
                rule=self.name,
                rationale=f"lost_package: traceable shipment reported '{term}'",
            )
        return PriorityAssessment(
            level=UrgencyLevel.NORMAL,
            rule=self.name,
            rationale=(
                f"lost_package: '{term}' reported without an order reference; "
                "cannot trace until customer provides one"
            ),
        )
