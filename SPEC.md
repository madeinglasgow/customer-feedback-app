Build a small but realistic **customer feedback web application** that will later be used as an unfamiliar codebase for a coding agent to investigate.

The application itself is not an AI application. It is a conventional software system for collecting customer feedback, storing it, classifying its urgency, and alerting a customer-service team when feedback requires immediate attention.

The main goal is to produce a codebase that is easy for a human to understand at a high level, but rich enough that answering engineering questions requires inspecting multiple files, following relationships across the codebase, and sometimes querying application data.

## Product overview

Customers can submit feedback through a simple web form.

Each feedback item should contain:

* customer name
* customer email
* feedback message
* category
* optional order ID
* submission timestamp

Supported categories should include:

* Product
* Shipping
* Billing
* Returns
* Customer service
* Other

After feedback is submitted, the application should:

1. Validate the submission.
2. Store it in a database.
3. Determine its urgency.
4. If appropriate, create an escalation.
5. Notify the customer-service team of urgent feedback.

The application should also provide a simple internal dashboard where customer-service staff can view submitted feedback and filter it by category, urgency, status, and date.

## Technology

Use a simple, mainstream stack that a learner can understand without needing specialized framework knowledge.

Preferred stack:

* Python
* Flask
* SQLAlchemy
* SQLite
* Server-rendered HTML using Jinja templates
* pytest for tests

Keep frontend JavaScript minimal. The educational focus will be on exploring the backend codebase.

Use a conventional project structure with clearly separated concerns.

For example:

```text
app/
  routes/
  services/
  models/
  repositories/
  templates/
  static/
  config/
tests/
docs/
scripts/
```

You may adjust this structure if another conventional organization is clearer.

## Core features

### 1. Submit customer feedback

Provide a public page containing a feedback form.

Validate:

* name is required
* email must be valid
* message must not be empty
* category must be one of the supported categories
* order ID is optional

Persist valid submissions to the database.

### 2. Feedback records

A feedback record should include at least:

* id
* customer_name
* customer_email
* message
* category
* order_id
* created_at
* urgency level
* status
* escalation reason, if any

Statuses might include:

* new
* reviewing
* resolved

Urgency levels should include:

* low
* normal
* high
* critical

### 3. Urgency classification

Implement deterministic business logic for deciding urgency. Do not use an LLM.

Make this logic non-trivial enough that engineers may need to inspect several rules to understand a classification.

For example:

* messages containing terms indicating physical danger or immediate safety problems may be `critical`
* suspected fraud or unauthorized charges may be `critical`
* repeated failed billing attempts may be `high`
* a customer explicitly threatening to leave may be `high`
* ordinary product complaints may be `normal`
* compliments may be `low`

Allow category-specific rules.

Do not put all urgency logic into one enormous function. Organize it into sensible components or rule helpers.

The resulting code should still feel like reasonable production code rather than deliberately confusing code.

### 4. Escalations

When feedback meets escalation criteria, create an escalation record.

An escalation should record:

* associated feedback ID
* escalation reason
* escalation timestamp
* notification status
* resolved status

Not every `high` urgency item necessarily needs to be escalated. Include some separate business rules controlling escalation.

For example, billing feedback might escalate under different conditions from shipping feedback.

### 5. Customer-service notifications

Implement a notification service for escalated feedback.

Do not send real email or Slack messages.

Instead, create an abstraction such as:

```python
NotificationService
```

with an implementation that records outgoing notifications to a database table, log, or local outbox.

Allow configuration such as:

* whether notifications are enabled
* customer-service recipient/team identifier
* minimum urgency required for immediate notification

This should make it possible for an engineer to investigate questions such as:

> Why was this feedback escalated but no notification was sent?

### 6. Internal dashboard

Provide a basic internal dashboard listing feedback.

Support filtering by:

* category
* urgency
* status
* date

Allow staff to open an individual feedback record and see:

* original submission
* urgency
* escalation status
* escalation reason
* notification information

Allow staff to mark feedback as reviewing or resolved.

Visual polish is not important. Keep the UI clean and functional.

## Database

Use SQLite through SQLAlchemy.

Include models for at least:

* Feedback
* Escalation
* Notification

Consider whether other models are useful, but avoid unnecessary complexity.

Include a database initialization script and seed data.

Seed the application with approximately 30–50 feedback items spanning:

* all categories
* multiple urgency levels
* escalated and non-escalated cases
* resolved and unresolved feedback

Include a few carefully chosen records that can later serve as debugging/investigation scenarios.

## Tests

Include meaningful unit and integration tests.

Tests should cover:

* form validation
* urgency rules
* escalation rules
* notification behavior
* database persistence
* important API/route behavior

Include edge cases.

Tests should be useful as an additional information source for an engineer trying to understand intended behavior.

## Documentation

Include:

### README.md

Explain:

* what the application does
* how to install it
* how to run it
* how to initialize/seed the database
* how to run tests

Keep the README useful, but **do not explain every piece of business logic in detail**.

### docs/

Include a small number of realistic documents such as:

* `architecture.md`
* `customer_support_process.md`
* `deployment.md`

These should provide useful context but should not make every engineering question trivial to answer.

For example, the customer-support process document might explain that critical safety issues should be escalated immediately without documenting the exact implementation.

## Configuration

Use environment/config settings for several behaviors, such as:

* database URL
* notifications enabled
* support-team destination
* urgency threshold
* application environment
* logging level

Provide reasonable development defaults.

Ensure configuration influences actual application behavior.

## Logging

Log important events such as:

* feedback received
* urgency classification
* escalation created
* notification attempted
* notification suppressed
* feedback resolved

Logs should be useful for diagnosing behavior.

## Design specifically for later codebase investigation

This application will be used in a course about **agentic search and context engineering**.

A coding agent will later be given tools such as lexical search, semantic search, filesystem inspection, code-structure search, and database access and asked questions about this unfamiliar repository.

Design the application so that useful engineering questions naturally require different kinds of information gathering.

Examples of questions the codebase should support include:

* Why was a particular feedback item classified as critical?
* Why was an item marked high urgency but not escalated?
* Why was an escalation created but no notification sent?
* Where is the rule for fraud-related feedback defined?
* Which parts of the application can change feedback status?
* What configuration controls customer-service notifications?
* Which tests describe expected behavior for billing complaints?
* How would we add a new feedback category?
* How would we change the rules for shipping complaints?
* Which database records show critical feedback that remains unresolved?

To support this:

### Spread relevant information naturally across the system

For example, answering why a notification wasn't sent might require understanding:

* the feedback record
* escalation logic
* notification service
* application configuration

Do not artificially hide information or make the architecture intentionally bad. The complexity should come from realistic separation of concerns.

### Preserve meaningful code structure

Keep:

* functions reasonably scoped
* classes coherent
* modules organized by responsibility

This allows structural/code-aware search to be meaningfully different from simple text search.

### Include exact identifiers worth searching for

Use meaningful:

* exception names
* model names
* service names
* configuration variables
* enum values

This gives lexical search useful targets.

### Include conceptual relationships that are not always expressed using identical terminology

For example, code involved in "urgent customer feedback" might use names such as:

* severity
* escalation
* priority
* immediate_attention

This creates realistic cases where semantic search may help discover relevant areas of the codebase.

### Include multiple information sources

The coding agent should potentially need to consult:

* source code
* tests
* documentation
* configuration
* database records
* logs

This is important. The repository should demonstrate that "searching the code" is not synonymous with "finding the right information."

## Avoid these problems

Do not:

* build semantic search, embeddings, RAG, or AI into this application
* make the app itself about search
* create dozens of unnecessary abstractions
* deliberately introduce bad code merely to make investigation harder
* create a giant README that explains the entire implementation
* put every business rule in one file
* make every question answerable by grepping one obvious string
* add a complex frontend framework unless truly necessary

The application should feel like a **small, plausible production application**, not a synthetic benchmark.

## Deliverables

Produce:

1. Complete runnable source code.
2. Dependency specification.
3. Database schema and migrations or initialization script.
4. Seed-data script.
5. Automated tests.
6. README.
7. Supporting documentation.
8. Example environment configuration.
9. A short document called `investigation_scenarios.md`.

In `investigation_scenarios.md`, list approximately 10 engineering questions that would be useful for testing a coding agent's ability to investigate the system.

For each scenario, privately design the code/data so the answer exists and can be determined from the repository, but **do not include the answer in the scenario document**.

## Quality bar

Before finishing:

* run the application
* initialize and seed the database
* run the complete test suite
* fix any failures
* verify the major user flows manually or through integration tests
* confirm that the repository contains several genuinely multi-step investigation scenarios

Favor clarity, realism, and maintainability over feature count.

