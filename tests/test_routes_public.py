from app.models import Feedback


def valid_form(**overrides):
    form = {
        "customer_name": "Ada Lovelace",
        "customer_email": "ada@example.com",
        "message": "The engine arrived with a bent frame.",
        "category": "product",
        "order_id": "ORD-1001",
    }
    form.update(overrides)
    return form


def test_get_form_renders(client):
    response = client.get("/feedback")
    assert response.status_code == 200
    assert b"Send us your feedback" in response.data


def test_root_redirects_to_form(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/feedback" in response.headers["Location"]


def test_valid_submission_persists_and_redirects(client, db_session):
    response = client.post("/feedback", data=valid_form())
    assert response.status_code == 302
    assert "/feedback/thanks" in response.headers["Location"]

    records = db_session.query(Feedback).all()
    assert len(records) == 1
    assert records[0].customer_email == "ada@example.com"


def test_invalid_submission_rerenders_with_errors(client, db_session):
    response = client.post("/feedback", data=valid_form(customer_email="nope"))
    assert response.status_code == 422
    assert b"Email address is not valid." in response.data
    assert db_session.query(Feedback).count() == 0


def test_invalid_submission_preserves_entered_values(client):
    response = client.post("/feedback", data=valid_form(customer_email=""))
    assert b"Ada Lovelace" in response.data


def test_thank_you_page(client):
    response = client.get("/feedback/thanks")
    assert response.status_code == 200
    assert b"Thank you" in response.data
