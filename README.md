# Customer Feedback App

A small web application for collecting customer feedback, classifying its
urgency, and alerting the customer-service team when something needs
immediate attention.

Customers submit feedback through a public form. Each submission is
validated, stored, and classified by deterministic business rules. Items
that meet escalation criteria produce an escalation record, and — depending
on configuration — an alert to the customer-service team. Staff review
everything through an internal dashboard.

## Stack

- Python / Flask
- SQLAlchemy with SQLite
- Server-rendered Jinja templates (no frontend framework)
- pytest

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Initialize and seed the database

```bash
python scripts/init_db.py --reset
python scripts/seed_data.py
```

This creates `instance/feedback.db` and loads ~40 realistic feedback
records, including escalated, notified, and resolved cases. Seeding runs
each record through the real intake pipeline, so it also produces
application log output in `logs/app.log`.

## Run the application

```bash
flask --app wsgi run
```

- Public feedback form: http://127.0.0.1:5000/feedback
- Internal dashboard: http://127.0.0.1:5000/dashboard/

## Run the tests

```bash
pytest
```

## Configuration

Behavior is controlled through environment variables with development
defaults — see `.env.example` for the full list. Notable settings include
the database URL, whether customer-service notifications are enabled, the
destination support team, and the minimum urgency required for an
immediate alert.

## Project layout

```
app/
  config/        environment-driven settings
  models/        SQLAlchemy models and enums
  repositories/  data access
  routes/        Flask blueprints (public form, internal dashboard)
  services/      intake pipeline, triage rules, escalation policy, notifications
  templates/     Jinja templates
docs/            architecture and process documentation
scripts/         database init and seed scripts
tests/           unit and integration tests
logs/            application log output
```
