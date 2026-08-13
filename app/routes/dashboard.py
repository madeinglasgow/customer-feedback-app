from datetime import datetime, timedelta

from flask import Blueprint, abort, redirect, render_template, request, url_for

from app.extensions import db
from app.models import FeedbackCategory, FeedbackStatus, UrgencyLevel
from app.repositories import (
    EscalationRepository,
    FeedbackRepository,
    NotificationRepository,
)
from app.services import build_workflow_service
from app.services.workflow_service import UnknownStatusError

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def _parse_enum(enum_cls, raw: str | None):
    if not raw:
        return None
    try:
        return enum_cls(raw)
    except ValueError:
        return None


def _parse_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        return None


@dashboard_bp.get("/")
def feedback_list():
    filters = {
        "category": _parse_enum(FeedbackCategory, request.args.get("category")),
        "urgency": _parse_enum(UrgencyLevel, request.args.get("urgency")),
        "status": _parse_enum(FeedbackStatus, request.args.get("status")),
        "since": _parse_date(request.args.get("since")),
        "until": _parse_date(request.args.get("until")),
    }
    # Make the "until" date inclusive of the whole day.
    if filters["until"] is not None:
        filters["until"] = filters["until"] + timedelta(days=1)

    repository = FeedbackRepository(db.session)
    items = repository.search(**filters)

    return render_template(
        "dashboard/feedback_list.html",
        items=items,
        categories=list(FeedbackCategory),
        urgencies=list(UrgencyLevel),
        statuses=list(FeedbackStatus),
        args=request.args,
    )


@dashboard_bp.get("/feedback/<int:feedback_id>")
def feedback_detail(feedback_id: int):
    repository = FeedbackRepository(db.session)
    feedback = repository.get(feedback_id)
    if feedback is None:
        abort(404)

    notifications = []
    if feedback.escalation is not None:
        notifications = NotificationRepository(db.session).for_escalation(
            feedback.escalation.id
        )

    return render_template(
        "dashboard/feedback_detail.html",
        feedback=feedback,
        notifications=notifications,
        statuses=list(FeedbackStatus),
    )


@dashboard_bp.post("/feedback/<int:feedback_id>/status")
def update_status(feedback_id: int):
    repository = FeedbackRepository(db.session)
    feedback = repository.get(feedback_id)
    if feedback is None:
        abort(404)

    workflow = build_workflow_service(db.session)
    try:
        workflow.update_status(feedback, request.form.get("status", ""))
    except UnknownStatusError:
        abort(400)

    return redirect(url_for("dashboard.feedback_detail", feedback_id=feedback_id))


@dashboard_bp.post("/escalations/<int:escalation_id>/resolve")
def resolve_escalation(escalation_id: int):
    escalation = EscalationRepository(db.session).get(escalation_id)
    if escalation is None:
        abort(404)

    workflow = build_workflow_service(db.session)
    workflow.resolve_escalation(escalation)

    return redirect(
        url_for("dashboard.feedback_detail", feedback_id=escalation.feedback_id)
    )
