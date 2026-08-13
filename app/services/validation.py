"""Validation of incoming feedback form submissions."""

import re

from app.models import FeedbackCategory
from app.services.types import FeedbackSubmission

# Deliberately simple: local part, @, domain with at least one dot.
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MAX_NAME_LENGTH = 120
MAX_ORDER_ID_LENGTH = 40


class ValidationError(Exception):
    """Raised when a feedback submission fails validation.

    ``errors`` maps field names to human-readable messages.
    """

    def __init__(self, errors: dict[str, str]):
        self.errors = errors
        super().__init__(f"invalid feedback submission: {', '.join(errors)}")


def validate_feedback_form(form: dict) -> FeedbackSubmission:
    """Validate raw form data and return a FeedbackSubmission.

    Raises ValidationError collecting all field problems at once.
    """
    errors: dict[str, str] = {}

    name = (form.get("customer_name") or "").strip()
    if not name:
        errors["customer_name"] = "Name is required."
    elif len(name) > MAX_NAME_LENGTH:
        errors["customer_name"] = f"Name must be at most {MAX_NAME_LENGTH} characters."

    email = (form.get("customer_email") or "").strip()
    if not email:
        errors["customer_email"] = "Email is required."
    elif not EMAIL_PATTERN.match(email):
        errors["customer_email"] = "Email address is not valid."

    message = (form.get("message") or "").strip()
    if not message:
        errors["message"] = "Message must not be empty."

    category_raw = (form.get("category") or "").strip()
    category: FeedbackCategory | None = None
    if not category_raw:
        errors["category"] = "Category is required."
    else:
        try:
            category = FeedbackCategory(category_raw)
        except ValueError:
            errors["category"] = "Category is not one of the supported categories."

    order_id = (form.get("order_id") or "").strip() or None
    if order_id and len(order_id) > MAX_ORDER_ID_LENGTH:
        errors["order_id"] = f"Order ID must be at most {MAX_ORDER_ID_LENGTH} characters."

    if errors:
        raise ValidationError(errors)

    return FeedbackSubmission(
        customer_name=name,
        customer_email=email,
        message=message,
        category=category,
        order_id=order_id,
    )
