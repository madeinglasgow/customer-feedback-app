# Contributing

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/init_db.py --reset
python scripts/seed_data.py
flask --app wsgi run
```

Run the tests with `pytest`. The suite is fast; run it before every commit.

## Code organization

The app follows a conventional layered structure — put new code where its
responsibility lives:

- **`app/routes/`** — HTTP only. Parse input, call a service, render a
  template. No business logic in route handlers.
- **`app/services/`** — business logic. The intake pipeline, workflow
  transitions, escalation policy, and notification dispatch each have their
  own module.
- **`app/services/triage/rules/`** — one severity rule per module. A rule
  is a small class with an `applies_to()` category filter and an
  `evaluate()` method; register new rules in `rules/__init__.py`. Keyword
  lists live in `triage/keywords.py`, not inline in rules.
- **`app/repositories/`** — all SQLAlchemy queries. Services should not
  build queries inline.
- **`app/models/`** — schema and enums only; no behavior beyond simple
  properties.

## Conventions

- Enums are `str`-valued and stored as lowercase strings in SQLite; compare
  against the enum member, not the raw string.
- Log through the `feedback.*` logger hierarchy (`feedback.intake`,
  `feedback.triage`, `feedback.escalation`, `feedback.notifications`,
  `feedback.workflow`). Significant decisions — classifications,
  escalations, suppressed notifications — must be logged; the log is an
  investigation surface, not decoration.
- Configuration is environment-driven with development defaults. New
  behavior toggles belong in `app/config/settings.py` and `.env.example`,
  and must actually be read at runtime.
- Every new rule or policy branch needs tests. Tests double as behavioral
  documentation; write them so a reader can learn intended behavior from
  the test names.

## Adding a feedback category

Touch points, in order: the `FeedbackCategory` enum, the category baseline
table in `triage/rules/category_defaults.py`, the escalation-policy
dispatch table, and the tests that enumerate categories. The form and
dashboard render categories from the enum, so templates need no changes.
