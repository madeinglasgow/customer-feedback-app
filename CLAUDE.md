# CLAUDE.md — Instructor / Maintainer Notes

**⚠️ This file is course material, not app documentation.** It contains
spoilers for the investigation scenarios. It is excluded from Chroma
ingestion (see `ingestion/ingestion_service.py` → `IngestionConfig.exclude_files`,
which also excludes `SPEC.md` and `docs/investigation_scenarios.md`) — but it
is still on disk, so a lab agent with unrestricted filesystem tools could
read it. Keep that in mind when configuring the lab agent's file access.

## What this repo is

A small, realistic Flask customer-feedback application built as the
**investigation target** for a hands-on lab in a context-engineering /
agentic-search course. Students build a coding agent with search tools
(semantic, lexical, code-structure, filesystem — and eventually database)
and use it to answer engineering questions about this unfamiliar codebase.
It replaces the previous lab target (`github.com/lucasrct/app`, the
course's Chroma-backed code-search app).

Built from `SPEC.md`. Information is deliberately spread across code,
tests, docs, config, seed data, and logs so different questions require
different tools.

## The application

- Stack: Flask + Flask-SQLAlchemy + SQLite, Jinja templates, pytest (92 tests).
- Pipeline: submit → validate → triage (7 severity rules, max wins,
  baselines are fallbacks) → escalation policy (per-category) → outbox
  notifications (two distinct suppression paths) → dashboard workflow.
- Deliberate vocabulary drift for semantic-search realism: triage says
  *severity/priority*, models say *urgency*, notifications say
  *immediate attention*.

Commands:

```bash
source .venv/bin/activate
python scripts/init_db.py --reset && python scripts/seed_data.py  # rebuild + seed DB and logs/app.log
flask --app wsgi run                                              # /feedback, /dashboard/
pytest -q
```

## Seeded investigation scenarios (SPOILERS)

40 records seeded through the real pipeline. Planted records:

| Record | Design |
|---|---|
| Dana Whitfield (product) | "sparking and smoking" → SafetyHazardRule → critical, escalated, notified, reviewing |
| Ravi Menon (product) | "burned my fingertips" → critical, escalated, notified, **new** |
| Elena Vasquez (billing) | "did not authorize" → SuspectedFraudRule → critical, escalated, notified, **new** |
| Marcus Bell (billing ×3) | Two mild priors + third mild message → high **only via** `RepeatedBillingFailureRule.history_lookup` → `count_recent_billing_complaints` (DB-dependent classification) |
| Priya Sharma (shipping) | Churn phrase, **no order_id** → high but NOT escalated (`_escalate_shipping_high` requires order_id) |
| Jordan Okafor (shipping) | Same complaint **with** order_id → high, escalated, notified (contrast pair with Priya) |
| Tomas Lindqvist (billing) | Seeded under `NOTIFICATION_MIN_URGENCY=critical` ("June alert-volume review", see CHANGELOG 1.3.x + `.env.example` comment) → escalation with **suppressed** notification row |
| Aisha Rahman (customer_service) | Seeded under `NOTIFICATIONS_ENABLED=false` ("maintenance window") → escalation with **no notification row at all**; only a `logs/app.log` WARNING |
| Grace Liu (product) | "beautifully fired ceramic" compliment → low ("fired" ≠ "fire": word-boundary matching) |

Unresolved criticals in the seeded DB: Dana (reviewing), Elena (new), Ravi (new).

`docs/investigation_scenarios.md` lists 10 questions (no answers — safe to
hand to students). Answer chains for scenarios live in the queries below
and in the seed design table above.

## Chroma ingestion (`ingestion/`)

Pipeline ported from `lucasrct/app` (`services/ingestion_service.py` etc.)
so the collection structure matches the existing lab exactly:

- `.py` → tree-sitter AST chunks (`function_definition` / `class_definition`
  atomic — methods do NOT get their own chunks — plus `gap` chunks);
  `.md` → H1–H3 `markdown_section` chunks; `.txt` → `text_paragraph`.
- 1000-token budget (tiktoken), uuid4 IDs, batch-100 `collection.add`,
  metadata: repo-relative `path`, `start_line`, `end_line`, `symbol`,
  `chunk_type`, `language`, `ingested_at`. Embedding provider/model stored
  in collection metadata. Default collection name `code_collection`,
  persist dir `./chroma_data` (gitignored).
- Excluded from ingestion: `ingestion/` itself, `SPEC.md`,
  `docs/investigation_scenarios.md`, `CLAUDE.md`, `.venv`, `instance/`,
  `logs/`, `chroma_data/`.

```bash
pip install -r ingestion/requirements.txt
OPENAI_API_KEY=... python ingestion/ingest.py        # course configuration
python ingestion/ingest.py --provider default        # keyless local build
```

Verified corpus: 57 files → 235 chunks (60 function, 58 class, 69 gap,
45 markdown_section, 3 text_paragraph). Re-running **appends** duplicates —
`rm -rf chroma_data` first to rebuild.

## Lab queries (with answers — SPOILERS)

### Single-hop (one tool each)

1. **Semantic**: "What happens when a customer reports that a product hurt
   someone?" → `app/services/triage/rules/safety.py` (query vocabulary
   matches nothing lexically).
2. **Lexical**: "I saw `escalation skipped` in the logs — where does that
   come from?" → the one `logger.info` in `app/services/escalation_policy.py`.
3. **Hybrid**: "What does NOTIFICATION_MIN_URGENCY actually do when feedback
   gets escalated?" → identifier gives precision; semantic ranking prefers
   the behavior chunk (`OutboxNotificationService.notify_escalation`).
4. **Code-structure**: "List every class that extends SeverityRule." →
   7 rule classes in `app/services/triage/rules/`.
5. **Database**: "Which customers currently have critical feedback that
   hasn't been resolved?" → SQL only: Dana, Elena, Ravi. **Requires the DB
   tool** (see TODO).
   - Non-DB alternative single-hop: "Did any notifications get suppressed,
     and why?" → grep `logs/app.log`.

### Multi-hop

1. **Priya vs Jordan** (DB → DB → code → docs): identical messages, only
   Jordan escalated → shipping escalation requires `order_id` →
   `customer_support_process.md` corroborates.
2. **Marcus Bell** (DB → code → code → DB): mild message, high urgency →
   `history_lookup` → `count_recent_billing_complaints` → his 2 priors.
3. **Tomas** (DB → code → config → changelog): suppressed row cites
   threshold `critical` but default is `high` → CHANGELOG 1.3.0/1.3.1 +
   `.env.example` comment (June review).
4. **Aisha** (DB → code → logs): escalation with zero notification rows →
   disabled-flag branch writes no row → `logs/app.log` "notifications
   disabled" line → runbook/deployment maintenance windows.
5. **Status-change sweep** (code-structure): dashboard status route,
   escalation-resolve route, `FeedbackWorkflowService` bidirectional
   cascade, `scripts/seed_data.py`.

## How the actual lab notebook ingests (C1_M2_Lab_3)

The lab notebook does NOT use this repo's `ingestion/` pipeline or the
lucasrct/app web app. Its ingestion is `helper_utils.load_or_create_collection()`
(a file that lives with the notebook): clone repo → chunk → ChromaDB with
**sentence-transformers all-MiniLM-L6-v2** embeddings, persist dir
`lesson_example`. The original version ingested `*.py` only with no
exclusions; a modified `helper_utils.py` (2026-08) adds `.md` ingestion
(H1–H3 sections, header as `symbol`, `chunk_type='markdown_section'`) plus
`ignore_dirs=("ingestion",)` and
`exclude_files=("SPEC.md", "CLAUDE.md", "docs/investigation_scenarios.md")`.
Verified against a fresh clone of this repo: **232 chunks from 54 files**
(69 gap / 60 function / 58 class / 45 markdown_section), zero leaks.
`notes/*.txt` is NOT ingested by the notebook (py+md only). The notebook's
five tools (semantic / symbol / regex / sparse / hybrid) consume `path`,
`start_line`, `symbol` metadata — all present. Notebook swap: cell 4 clone
URL → this repo (path `feedback_app`), cell 8 collection_name →
`feedback_app_collection`, repo_path → `./feedback_app`.

## TODO for the lab

- **Add the read-only DB query tool to the notebook.** A `DatabaseQuery`
  tool matching the lab's `tool_utils.Tool` pattern has been drafted
  (2026-08): read-only URI (`file:...?mode=ro`), 50-row cap, schema
  discoverable via `sqlite_master`. To support it, the **seeded database
  snapshot is now committed at `instance/feedback.db`** (gitignore
  exception) so a fresh clone carries the data — regenerate it with the
  seed scripts after any seed change and re-commit. Without this tool,
  single-hop query #5 is unanswerable and multi-hop 1–4 degrade to
  weaker paths (reading `scripts/seed_data.py` chunks as fixtures).
- The repo's own `ingestion/` pipeline (OpenAI-embedding collection at
  `./chroma_data`) remains for a lucasrct/app-style web-app collection;
  rebuild with the OpenAI provider if used — the checked verification
  build used `--provider default` (no API key here).

## Maintainer conventions

- New `.md`/`.txt`/`.py` files are ingested automatically — never put
  scenario answers in them. Spoilers go here or in SPEC.md (both excluded).
- If you rename `ingestion/`, update `IngestionConfig.ignore_patterns`.
- After changing seed data, regenerate cleanly:
  `rm -f logs/app.log && python scripts/init_db.py --reset && python scripts/seed_data.py`,
  then verify the planted scenarios still hold (SQL checks in
  `notes/oncall-runbook.txt` are a quick smoke test).
