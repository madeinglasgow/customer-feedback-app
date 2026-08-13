from flask import Blueprint, current_app, redirect, render_template, request, url_for

from app.extensions import db
from app.models import FeedbackCategory
from app.services import build_intake_service
from app.services.validation import ValidationError, validate_feedback_form

public_bp = Blueprint("public", __name__)


@public_bp.get("/")
def index():
    return redirect(url_for("public.feedback_form"))


@public_bp.get("/feedback")
def feedback_form():
    return render_template(
        "public/submit_feedback.html",
        categories=list(FeedbackCategory),
        errors={},
        form={},
    )


@public_bp.post("/feedback")
def submit_feedback():
    try:
        submission = validate_feedback_form(request.form)
    except ValidationError as exc:
        return (
            render_template(
                "public/submit_feedback.html",
                categories=list(FeedbackCategory),
                errors=exc.errors,
                form=request.form,
            ),
            422,
        )

    intake = build_intake_service(db.session, current_app.config)
    intake.submit(submission)
    return redirect(url_for("public.thank_you"))


@public_bp.get("/feedback/thanks")
def thank_you():
    return render_template("public/thank_you.html")
