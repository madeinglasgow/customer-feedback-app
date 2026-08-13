# Changelog

Notable changes to the customer feedback application.

## [1.4.0] — 2026-08-02

### Added
- Date-range filtering (`since` / `until`) on the dashboard feedback list.
- `notes/oncall-runbook.txt` so the on-call rotation stops re-learning the
  same investigations from scratch.

### Changed
- Escalation resolution from the dashboard now also resolves the underlying
  feedback record, so agents no longer have to close both by hand.

## [1.3.1] — 2026-07-08

### Changed
- Reverted the immediate-alert urgency threshold to its standard value now
  that the June alert-volume review has concluded. See the runbook for the
  review's outcome.

## [1.3.0] — 2026-06-10

### Changed
- Raised the minimum urgency for immediate customer-service alerts for the
  duration of the June alert-volume review. Escalations below the bar are
  still recorded; they simply don't page the team.

### Fixed
- Suppressed notifications now record an explanation so reviewers can tell
  *why* no alert went out instead of guessing.

## [1.2.0] — 2026-05-19

### Added
- Repeated-billing-failure detection now also considers a customer's recent
  billing complaint history, not just the wording of the current message.
- Seed script for local development databases.

### Fixed
- Keyword matching now uses word boundaries. A product review praising
  "beautifully fired ceramic" no longer trips the safety screen.

## [1.1.0] — 2026-04-28

### Added
- Category-specific escalation conditions. Not every high-priority item
  needs to interrupt the on-duty team; the policy now reflects how the
  support process actually works per category.
- Maintenance-window support: notifications can be disabled globally via
  configuration while intake keeps running.

## [1.0.0] — 2026-04-07

Initial release: public feedback form, deterministic urgency triage,
escalations, notification outbox, internal dashboard, seed data, tests.
