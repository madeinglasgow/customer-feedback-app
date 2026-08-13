# Architecture

## Overview

The application is a conventional layered Flask app:

```
routes  ->  services  ->  repositories  ->  models (SQLAlchemy / SQLite)
```

- **Routes** (`app/routes/`) handle HTTP concerns only: parsing input,
  choosing templates, redirects, and status codes. The public blueprint
  serves the feedback form; the dashboard blueprint serves staff views.
- **Services** (`app/services/`) contain the business logic.
- **Repositories** (`app/repositories/`) wrap database queries so services
  and routes don't build SQLAlchemy queries inline.
- **Models** (`app/models/`) define the schema: `Feedback`, `Escalation`,
  and `Notification`, plus the enums used across the app.

## The intake pipeline

`FeedbackIntakeService.submit()` orchestrates what happens after a valid
submission:

1. **Triage** — the `TriageEngine` (`app/services/triage/`) evaluates a set
   of severity rules and assigns an urgency level. Rules are small,
   single-purpose classes; the highest severity among the rules that fire
   wins. Some rules consult more than just the message text — for example,
   customer history in the database.
2. **Persistence** — the feedback record is stored with its urgency.
3. **Escalation** — the `EscalationPolicy` decides whether the item warrants
   an escalation record. Escalation is deliberately a separate decision from
   urgency, with category-specific conditions.
4. **Notification** — for escalated items, the `NotificationService` decides
   whether the customer-service team should be alerted immediately.
   Notifications are written to an outbox table rather than actually sent;
   configuration determines whether and when alerts go out.

A note on vocabulary: different layers grew their own terms for roughly the
same concept. The triage package speaks of *severity* and *priority*, the
data model stores *urgency*, and the notification service asks whether an
item *requires immediate attention*. They are related but not identical —
see the code for the exact mapping.

## Staff workflow

Staff use the dashboard to review feedback, filter it, and move items
through the `new → reviewing → resolved` lifecycle. Resolving feedback and
resolving an escalation are related operations handled by the
`FeedbackWorkflowService`.

## Configuration and logging

Configuration lives in `app/config/settings.py`, driven by environment
variables (see `.env.example`). Several settings change runtime behavior,
particularly around notifications.

Application events are logged under the `feedback.*` logger hierarchy to
both the console and `logs/app.log`. The log is often the quickest way to
reconstruct what the system did with a particular submission.
