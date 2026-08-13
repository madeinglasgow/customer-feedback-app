# Customer Support Process

This document describes how the customer-service team handles incoming
feedback. It reflects team policy; the application implements (most of)
this policy in code.

## Queues

Incoming feedback lands in one of two places:

- **Standard queue** — the dashboard list, reviewed during business hours,
  oldest first within each urgency band.
- **Escalations** — items that meet escalation criteria get an escalation
  record and, when configuration allows, an immediate alert to the
  on-duty team inbox.

## Escalation policy (team view)

- **Safety issues are escalated immediately, always.** Anything suggesting
  physical danger — fire, burns, electrical faults, injuries — is treated
  as critical regardless of which category the customer picked.
- **Suspected fraud or unauthorized charges are escalated immediately.**
  These are time-sensitive for the customer and for us.
- **High-urgency billing problems are always escalated** because of the
  financial exposure involved.
- **Shipping issues without an order reference stay in the standard
  queue.** Agents cannot trace a shipment without an order ID, so the first
  step is a reply asking for it; escalating before that wastes the on-duty
  team's time.
- **Return complaints are escalated only when we risk losing the
  customer.** Routine return friction is handled in the standard queue.
- Customers who explicitly threaten to leave are treated as high priority
  wherever they wrote in.

Not every high-priority item results in an escalation — the rules above are
about who needs to see something *now*, not how serious it is.

## Alerts

Escalation alerts go to the team inbox configured for the environment.
During maintenance windows the alert channel is switched off entirely;
escalations created in that window are picked up from the dashboard when
the window ends. The alert threshold has also occasionally been tuned —
during the June alert-volume review the bar for immediate alerts was
temporarily raised, then reverted.

## Resolution

Agents mark items *reviewing* while working on them and *resolved* when
done. Resolving an escalated item closes its escalation as well. Critical
items should never sit unresolved for more than one business day.
