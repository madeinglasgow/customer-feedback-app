# Deployment

## Environments

The app runs in three environments selected by `APP_ENV`:

| Environment  | Purpose            | Notes                                   |
| ------------ | ------------------ | --------------------------------------- |
| development  | local work         | SQLite file DB, verbose defaults        |
| testing      | automated tests    | in-memory SQLite, file logging disabled |
| production   | live service       | all secrets/URLs must come from env     |

## Configuration

All runtime configuration is environment-driven; see `.env.example`.
Production deployments must set at least:

- `SECRET_KEY`
- `DATABASE_URL`
- `SUPPORT_TEAM_ID` (the escalation alert destination for that region)

Notification behavior (`NOTIFICATIONS_ENABLED`, `NOTIFICATION_MIN_URGENCY`)
is intentionally configurable per environment. Staging typically runs with
notifications disabled so test submissions don't page the support team.

## Process

The app is a standard WSGI application (`wsgi:app`). Any WSGI server works;
we use gunicorn:

```bash
gunicorn -w 2 -b 0.0.0.0:8000 wsgi:app
```

## Database

SQLite is sufficient at current volume. `scripts/init_db.py` creates the
schema. There is no migration tooling; schema changes are applied by
resetting and reseeding in non-production environments and by hand in
production.

## Logs

Application logs are written to the path in `LOG_FILE` (rotated at ~1 MB)
and to stdout. Operational investigations usually start from these logs —
they record intake, classification, escalation, and notification decisions
including suppressions.

## Maintenance windows

For planned maintenance, set `NOTIFICATIONS_ENABLED=false` and restart the
app rather than stopping it, so customers can keep submitting feedback
while the alert channel is quiet. Remember to re-enable it afterwards.
