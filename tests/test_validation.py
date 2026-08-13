import pytest

from app.models import FeedbackCategory
from app.services.validation import ValidationError, validate_feedback_form


def valid_form(**overrides):
    form = {
        "customer_name": "Ada Lovelace",
        "customer_email": "ada@example.com",
        "message": "The analytical engine arrived damaged.",
        "category": "product",
        "order_id": "ORD-1001",
    }
    form.update(overrides)
    return form


def test_valid_form_returns_submission():
    submission = validate_feedback_form(valid_form())
    assert submission.customer_name == "Ada Lovelace"
    assert submission.category == FeedbackCategory.PRODUCT
    assert submission.order_id == "ORD-1001"


def test_name_is_required():
    with pytest.raises(ValidationError) as exc:
        validate_feedback_form(valid_form(customer_name="   "))
    assert "customer_name" in exc.value.errors


@pytest.mark.parametrize(
    "email",
    ["", "not-an-email", "missing@tld", "@nodomain.com", "spaces in@example.com"],
)
def test_invalid_emails_rejected(email):
    with pytest.raises(ValidationError) as exc:
        validate_feedback_form(valid_form(customer_email=email))
    assert "customer_email" in exc.value.errors


def test_message_must_not_be_empty():
    with pytest.raises(ValidationError) as exc:
        validate_feedback_form(valid_form(message="  \n "))
    assert "message" in exc.value.errors


def test_unknown_category_rejected():
    with pytest.raises(ValidationError) as exc:
        validate_feedback_form(valid_form(category="complaints"))
    assert "category" in exc.value.errors


def test_order_id_is_optional():
    submission = validate_feedback_form(valid_form(order_id=""))
    assert submission.order_id is None


def test_overlong_order_id_rejected():
    with pytest.raises(ValidationError) as exc:
        validate_feedback_form(valid_form(order_id="X" * 41))
    assert "order_id" in exc.value.errors


def test_multiple_errors_collected_together():
    with pytest.raises(ValidationError) as exc:
        validate_feedback_form(
            {"customer_name": "", "customer_email": "bad", "message": "", "category": ""}
        )
    assert set(exc.value.errors) == {
        "customer_name",
        "customer_email",
        "message",
        "category",
    }
