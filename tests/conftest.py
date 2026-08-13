import pytest

from app import create_app
from app.extensions import db as _db
from app.models import FeedbackCategory
from app.services import build_intake_service
from app.services.types import FeedbackSubmission


@pytest.fixture()
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def db_session(app):
    return _db.session


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def intake(app, db_session):
    """A fully wired intake service against the test database."""
    return build_intake_service(db_session, app.config)


def make_submission(**overrides) -> FeedbackSubmission:
    defaults = dict(
        customer_name="Test Customer",
        customer_email="customer@example.com",
        message="The product works as described.",
        category=FeedbackCategory.PRODUCT,
        order_id=None,
    )
    defaults.update(overrides)
    return FeedbackSubmission(**defaults)
