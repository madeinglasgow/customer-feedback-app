"""Seed the database with realistic feedback data.

Records are run through the real intake pipeline (triage, escalation policy,
notifications), so escalation and notification rows — and log lines in
logs/app.log — are produced exactly as they would be in production. After
intake, timestamps are shifted into the past to spread submissions over
recent weeks.

Two historical batches are replayed with the configuration that was active
at the time:

- "june_threshold": submissions processed while NOTIFICATION_MIN_URGENCY was
  temporarily raised to critical during the June alert-volume review.
- "maintenance_window": submissions processed while NOTIFICATIONS_ENABLED was
  off for scheduled maintenance.

Usage:
    python scripts/init_db.py --reset && python scripts/seed_data.py
"""

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Feedback, FeedbackCategory, FeedbackStatus  # noqa: E402
from app.services import build_intake_service, build_workflow_service  # noqa: E402
from app.services.types import FeedbackSubmission  # noqa: E402

BATCH_CONFIG_OVERRIDES = {
    "default": {},
    "june_threshold": {"NOTIFICATION_MIN_URGENCY": "critical"},
    "maintenance_window": {"NOTIFICATIONS_ENABLED": False},
}


@dataclass(frozen=True)
class SeedRecord:
    name: str
    email: str
    category: FeedbackCategory
    message: str
    order_id: str | None
    days_ago: int
    status: FeedbackStatus
    batch: str = "default"


C = FeedbackCategory
S = FeedbackStatus

SEED_RECORDS = [
    # --- Product ---
    SeedRecord(
        "Dana Whitfield", "dana.whitfield@example.com", C.PRODUCT,
        "Our space heater started sparking and smoking last night. We unplugged "
        "it immediately, but this seems dangerous.",
        "ORD-10231", 6, S.REVIEWING,
    ),
    SeedRecord(
        "Grace Liu", "grace.liu@example.com", C.PRODUCT,
        "The glaze on the vase is beautifully fired ceramic. I love it, thank you!",
        None, 12, S.RESOLVED,
    ),
    SeedRecord(
        "Noah Petersen", "noah.petersen@example.com", C.PRODUCT,
        "The blender lid does not seal properly and leaks when mixing.",
        "ORD-10388", 18, S.NEW,
    ),
    SeedRecord(
        "Mia Torres", "mia.torres@example.com", C.PRODUCT,
        "Product photos show four attachments but the box only contained three.",
        "ORD-10402", 9, S.REVIEWING,
    ),
    SeedRecord(
        "Ethan Caldwell", "ethan.caldwell@example.com", C.PRODUCT,
        "The desk lamp flickers at the highest brightness setting.",
        "ORD-10450", 25, S.RESOLVED,
    ),
    SeedRecord(
        "Ravi Menon", "ravi.menon@example.com", C.PRODUCT,
        "The travel charger becomes dangerously hot and burned my fingertips "
        "when I unplugged it this morning.",
        "ORD-10511", 2, S.NEW,
    ),
    SeedRecord(
        "Lena Fischer", "lena.fischer@example.com", C.PRODUCT,
        "Assembly instructions were confusing; it took two hours to build the shelf.",
        None, 30, S.RESOLVED,
    ),
    # --- Shipping ---
    SeedRecord(
        "Priya Sharma", "priya.sharma@example.com", C.SHIPPING,
        "My package never arrived and nobody can tell me where it is. If this "
        "is how deliveries go, I'm taking my business elsewhere.",
        None, 8, S.NEW,
    ),
    SeedRecord(
        "Jordan Okafor", "jordan.okafor@example.com", C.SHIPPING,
        "My package never arrived and I'm taking my business elsewhere unless "
        "someone fixes this today.",
        "ORD-77812", 8, S.RESOLVED,
    ),
    SeedRecord(
        "Sofia Marino", "sofia.marino@example.com", C.SHIPPING,
        "Delivery arrived three days later than the estimate shown at checkout.",
        "ORD-77455", 15, S.RESOLVED,
    ),
    SeedRecord(
        "Ben Whitaker", "ben.whitaker@example.com", C.SHIPPING,
        "The box was dented on arrival although the contents survived.",
        "ORD-77510", 21, S.RESOLVED,
    ),
    SeedRecord(
        "Hana Suzuki", "hana.suzuki@example.com", C.SHIPPING,
        "The tracking page has not updated since Tuesday.",
        "ORD-77609", 4, S.NEW,
    ),
    SeedRecord(
        "Igor Novak", "igor.novak@example.com", C.SHIPPING,
        "The courier left the parcel at the wrong building entrance.",
        "ORD-77633", 11, S.REVIEWING,
    ),
    SeedRecord(
        "Amara Diallo", "amara.diallo@example.com", C.SHIPPING,
        "Shipping was fast and the packaging was perfect, thanks!",
        "ORD-77701", 19, S.RESOLVED,
    ),
    # --- Billing ---
    SeedRecord(
        "Elena Vasquez", "elena.vasquez@example.com", C.BILLING,
        "There is a charge on my statement I did not authorize. I think my "
        "card details were stolen.",
        None, 3, S.NEW,
    ),
    SeedRecord(
        "Marcus Bell", "marcus.bell@example.com", C.BILLING,
        "My payment did not go through at checkout yesterday.",
        "ORD-88012", 22, S.RESOLVED,
    ),
    SeedRecord(
        "Marcus Bell", "marcus.bell@example.com", C.BILLING,
        "Payment was declined once more this week, not sure why.",
        "ORD-88077", 13, S.RESOLVED,
    ),
    SeedRecord(
        "Marcus Bell", "marcus.bell@example.com", C.BILLING,
        "The payment failed today when my subscription renewed.",
        "ORD-88150", 2, S.NEW,
    ),
    SeedRecord(
        "Tomas Lindqvist", "tomas.lindqvist@example.com", C.BILLING,
        "I was charged twice for the same order this month and support has "
        "not replied yet.",
        "ORD-88123", 45, S.REVIEWING,
        batch="june_threshold",
    ),
    SeedRecord(
        "Olivia Grant", "olivia.grant@example.com", C.BILLING,
        "The invoice PDF link on my account page returns an error.",
        None, 16, S.RESOLVED,
    ),
    SeedRecord(
        "Ken Watanabe", "ken.watanabe@example.com", C.BILLING,
        "I was billed for expedited shipping although I chose standard delivery.",
        "ORD-88240", 7, S.NEW,
    ),
    SeedRecord(
        "Fatima Zahra", "fatima.zahra@example.com", C.BILLING,
        "Please update the VAT number printed on my receipts.",
        None, 27, S.RESOLVED,
    ),
    # --- Returns ---
    SeedRecord(
        "Ryan Doyle", "ryan.doyle@example.com", C.RETURNS,
        "I have asked twice about my refund status. If this keeps up I will "
        "cancel my account.",
        "ORD-99001", 10, S.RESOLVED,
    ),
    SeedRecord(
        "Chloe Bennett", "chloe.bennett@example.com", C.RETURNS,
        "The return label QR code would not scan at the drop-off point.",
        "ORD-99012", 14, S.REVIEWING,
    ),
    SeedRecord(
        "Miguel Santos", "miguel.santos@example.com", C.RETURNS,
        "Requesting a return for a jacket that runs two sizes small.",
        "ORD-99044", 6, S.NEW,
    ),
    SeedRecord(
        "Ingrid Olsen", "ingrid.olsen@example.com", C.RETURNS,
        "Return processed smoothly, great service, thank you.",
        "ORD-99070", 20, S.RESOLVED,
    ),
    SeedRecord(
        "Tariq Aziz", "tariq.aziz@example.com", C.RETURNS,
        "It has been two weeks and my return still shows as received, pending inspection.",
        "ORD-99101", 5, S.NEW,
    ),
    SeedRecord(
        "Wei Chen", "wei.chen@example.com", C.RETURNS,
        "I sent back two items but was only refunded for one of them.",
        "ORD-99133", 9, S.REVIEWING,
    ),
    # --- Customer service ---
    SeedRecord(
        "Aisha Rahman", "aisha.rahman@example.com", C.CUSTOMER_SERVICE,
        "I waited 45 minutes on chat and was disconnected twice. I am done "
        "with this company.",
        None, 35, S.REVIEWING,
        batch="maintenance_window",
    ),
    SeedRecord(
        "Liam Murphy", "liam.murphy@example.com", C.CUSTOMER_SERVICE,
        "The support agent was wonderful and solved my issue in minutes, thank you!",
        None, 13, S.RESOLVED,
    ),
    SeedRecord(
        "Nadia Haddad", "nadia.haddad@example.com", C.CUSTOMER_SERVICE,
        "I keep getting transferred between departments without an answer.",
        None, 7, S.NEW,
    ),
    SeedRecord(
        "Oscar Vega", "oscar.vega@example.com", C.CUSTOMER_SERVICE,
        "Your phone menu has no option for order changes.",
        None, 23, S.RESOLVED,
    ),
    SeedRecord(
        "Emily Stanton", "emily.stanton@example.com", C.CUSTOMER_SERVICE,
        "An agent promised a callback that never happened.",
        None, 4, S.NEW,
    ),
    SeedRecord(
        "Dmitri Ivanov", "dmitri.ivanov@example.com", C.CUSTOMER_SERVICE,
        "Chat support closes at 5pm which is hard for my timezone.",
        None, 17, S.REVIEWING,
    ),
    # --- Other ---
    SeedRecord(
        "Paula Reyes", "paula.reyes@example.com", C.OTHER,
        "Your website's dark mode toggle resets on every visit.",
        None, 8, S.NEW,
    ),
    SeedRecord(
        "George Adebayo", "george.adebayo@example.com", C.OTHER,
        "Do you plan to open a store in Chicago?",
        None, 26, S.RESOLVED,
    ),
    SeedRecord(
        "Sara Lindgren", "sara.lindgren@example.com", C.OTHER,
        "The newsletter arrives twice each week; once would be enough.",
        None, 11, S.REVIEWING,
    ),
    SeedRecord(
        "Ahmed Karimi", "ahmed.karimi@example.com", C.OTHER,
        "I received a suspicious email claiming to be from your store asking "
        "for my password. Is this a scam?",
        None, 5, S.RESOLVED,
    ),
    SeedRecord(
        "Julia Kim", "julia.kim@example.com", C.OTHER,
        "Love the new packaging design, it looks great.",
        None, 15, S.RESOLVED,
    ),
    SeedRecord(
        "Victor Moreau", "victor.moreau@example.com", C.OTHER,
        "The size guide link returns a 404 on mobile.",
        None, 3, S.NEW,
    ),
]


def _backdate(feedback: Feedback, days_ago: int) -> None:
    """Shift a freshly created record and its children into the past."""
    created = datetime.utcnow() - timedelta(days=days_ago)
    feedback.created_at = created
    escalation = feedback.escalation
    if escalation is not None:
        escalation.created_at = created + timedelta(minutes=1)
        if escalation.notified_at is not None:
            escalation.notified_at = escalation.created_at
        for notification in escalation.notifications:
            notification.created_at = escalation.created_at
            if notification.sent_at is not None:
                notification.sent_at = escalation.created_at


def _apply_status(app, feedback: Feedback, record: SeedRecord) -> None:
    if record.status == FeedbackStatus.NEW:
        return
    workflow = build_workflow_service(db.session)
    workflow.update_status(feedback, record.status.value)
    resolved_at = feedback.created_at + timedelta(days=1)
    escalation = feedback.escalation
    if escalation is not None and escalation.resolved_at is not None:
        escalation.resolved_at = resolved_at


def main() -> None:
    app = create_app()
    with app.app_context():
        existing = db.session.query(Feedback).count()
        if existing:
            print(f"Database already contains {existing} feedback records.")
            print("Run 'python scripts/init_db.py --reset' first to reseed.")
            sys.exit(1)

        # Oldest first so record IDs roughly follow submission order.
        for record in sorted(SEED_RECORDS, key=lambda r: r.days_ago, reverse=True):
            config = dict(app.config)
            config.update(BATCH_CONFIG_OVERRIDES[record.batch])
            intake = build_intake_service(db.session, config)

            feedback = intake.submit(
                FeedbackSubmission(
                    customer_name=record.name,
                    customer_email=record.email,
                    message=record.message,
                    category=record.category,
                    order_id=record.order_id,
                )
            )
            _backdate(feedback, record.days_ago)
            _apply_status(app, feedback, record)
            db.session.commit()

        total = db.session.query(Feedback).count()
        print(f"Seeded {total} feedback records.")


if __name__ == "__main__":
    main()
