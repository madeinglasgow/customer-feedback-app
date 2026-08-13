# Investigation Scenarios

Engineering questions about this system, suitable for exercising codebase
investigation skills. Each can be answered from the repository — source
code, tests, documentation, configuration, seed data, and logs. Some
require combining several of those sources.

1. Dana Whitfield's feedback was classified as **critical**. Which exact
   rule and which part of her message caused that classification?

2. Priya Sharma's shipping complaint is **high** urgency but was never
   escalated. Why not?

3. An escalation exists for Tomas Lindqvist's billing complaint, but the
   support team says they never received an alert about it. What happened?

4. Where is the rule that treats fraud-related feedback as urgent defined,
   and what wording in a message triggers it?

5. Which parts of the application can change a feedback item's status?

6. Marcus Bell's most recent billing message sounds mild — "The payment
   failed today when my subscription renewed" — yet it was classified as
   **high** urgency. Why?

7. What configuration controls customer-service notifications, and what
   are the effective values in a default development environment?

8. Which tests describe the expected handling of billing complaints?

9. Aisha Rahman's customer-service complaint was escalated, but there is
   no notification row for it at all — neither sent nor suppressed. What
   happened?

10. Which critical feedback items are currently unresolved, and who
    submitted them?

Follow-up exercises:

- How would you add a new feedback category (for example, "Website")?
  Which files need to change?
- How would you change the escalation rules for shipping complaints?
