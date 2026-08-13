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

## Database query tool for the lab (status: drafted + live-tested, 2026-08-13)

The lab notebook (C1_M2_Lab_3) got a sixth tool: read-only SQL against the
seeded SQLite DB. The **seeded snapshot is committed at
`instance/feedback.db`** (gitignore exception) so a fresh clone carries the
data — regenerate with the seed scripts after any seed change and re-commit.
Without this tool, single-hop query #5 is unanswerable and multi-hop 1–4
degrade to weaker paths (reading `scripts/seed_data.py` chunks as fixtures).

### Final tool code (paste as a notebook cell; matches tool_utils.Tool)

Incorporates both fixes learned from live testing (see "Lessons" below):
the no-rows nudge and the value-vocabulary description.

```python
import sqlite3

class DatabaseQueryInput(BaseModel):
    sql: str = Field(description="A single read-only SQL SELECT statement to run against the application's SQLite database")

class DatabaseQueryOutput(BaseModel):
    results: str

class DatabaseQuery(tool_utils.Tool):
    """A tool for querying the application's live data with read-only SQL."""

    def __init__(self, db_path, include_reason=False):
        super().__init__(
            name="run_database_query",
            description=(
                "Run a read-only SQL SELECT against the application's live SQLite database "
                "(tables: feedback, escalations, notifications; up to 50 rows returned). "
                "Key columns hold lowercase string values: feedback.urgency is one of "
                "low/normal/high/critical; feedback.status is one of new/reviewing/resolved; "
                "notifications.status is one of pending/sent/suppressed/failed. "
                "Inspect the full schema with: SELECT sql FROM sqlite_master. "
                "Best for questions about actual records: counts, statuses, specific customers, "
                "which items were escalated or notified."
            ),
            input_model=DatabaseQueryInput,
            output_model=DatabaseQueryOutput,
            include_reason=include_reason,
        )
        self.db_uri = f"file:{db_path}?mode=ro"

    def __call__(self, model_args):
        try:
            args = self.input_model.model_validate_json(model_args)
            conn = sqlite3.connect(self.db_uri, uri=True)
            try:
                cursor = conn.execute(args.sql)
                columns = [d[0] for d in cursor.description] if cursor.description else []
                rows = cursor.fetchmany(50)
            finally:
                conn.close()
            if not rows:
                return DatabaseQueryOutput(results=(
                    "Query returned no rows. If this is unexpected, your filter values may not "
                    "match the data — check actual values with SELECT DISTINCT <column> FROM <table> "
                    "before concluding that no matching records exist."
                ))
            lines = [" | ".join(columns)]
            lines += [" | ".join(str(v) for v in row) for row in rows]
            return DatabaseQueryOutput(results="\n".join(lines))
        except Exception as e:
            return self.ToolError(message=f"Database query failed: {e}")

db_tool = DatabaseQuery("feedback_app/instance/feedback.db", include_reason=True)
```

### Wiring

1. Re-clone so the clone contains `instance/feedback.db`
   (`shutil.rmtree("feedback_app")` then re-run the clone cell).
2. Add `db_tool` to the `tools=[...]` list in both `Agent(...)` cells.
3. System-prompt rule: *"Search tools only see source code and
   documentation — they cannot answer questions about actual data. For
   questions about specific records, counts, current statuses, or whether
   something happened for a particular customer, use run_database_query.
   Discover the schema first if you're unsure of column names."*
4. Optional extra rule: *"An empty query result may mean your assumptions
   about the data are wrong, not that no records exist. Verify column
   values with SELECT DISTINCT before concluding absence."*

Smoke test (expect Dana Whitfield / Elena Vasquez / Ravi Menon):

```python
print(db_tool('{"sql": "SELECT customer_name, status FROM feedback WHERE urgency=\'critical\' AND status != \'resolved\'", "reason": "test"}').results)
```

### Lessons from the live gpt-4.1-mini run (keep the failing trace!)

First live run of *"Which customers currently have critical feedback that
hasn't been resolved?"* FAILED informatively — the model answered "none"
(wrong: 3 exist). What happened:

- **SQL competence was fine**: it recovered from a bad column guess,
  fetched the schema via `sqlite_master`, wrote a correct LEFT JOIN.
- **Domain semantics failed**: it filtered `status='critical'` — but
  criticality lives in `urgency`; `status` holds new/reviewing/resolved.
  DDL shows only VARCHAR; nothing conveys value vocabularies.
- **Empty-result trap**: it treated 0 rows as confirmation of absence
  instead of a signal its filter was wrong.

Fixes applied in the code above: (1) the no-rows message carries the
SELECT DISTINCT recovery hint — instructions arriving as tool output at
the moment of failure are highly effective; (2) enum vocabularies moved
into the tool description. The failing-vs-fixed trace pair is a
first-class teaching exhibit: schema ≠ semantics; empty result ≠ absence;
tool descriptions and tool outputs are engineerable context.

### Other lab-tuning findings from live testing (same session)

- Prose outranks code for NL queries under MiniLM embeddings whenever
  prose coverage exists (docs/CHANGELOG/tests). Correct behavior — makes
  doc→code chaining the lesson. For code-first demos use mechanisms with
  zero prose coverage (e.g. rule tie-breaking, engine.py docstring only).
- gpt-4.1-mini failure modes observed: natural-language sparse probes
  ($contains is case-sensitive exact substring → empty results → retries)
  and guessed symbol names (`decide_escalation` instead of copying
  `should_escalate` from results). Prompt rules that fix both: sparse =
  exact identifiers copied from results only; after a result names a
  class/function, run_symbol_search with that exact name.
- Safety-question agent run reached the right code but mis-cited the
  escalation path (credited `_escalate_default_high`'s safety clause;
  actual path is the CRITICAL always-escalate branch — the HIGH
  per-category checks are never reached for critical items). Good grading
  discriminator between surface and deep investigation.
- Stale canned queries (cells 56/61/75) target the old lucasrct/app;
  replacements suggested: safety-rule question (semantic→symbol chain),
  NOTIFICATION_MIN_URGENCY question (hybrid showcase), escalation-with-
  no-notification (multi-hop, good token-analysis subject), plus one
  native absence-proof ("where does the app retry failed notifications?"
  — it doesn't; correct answer must say so).

## TODO for the lab

- Apply the DatabaseQuery cell above (with both fixes) on the platform and
  re-run the critical-unresolved query; expect a 2–3 call trace.
- Add the two search-strategy prompt rules (sparse/symbol) and
  `n_results=5` in test cells; replace stale canned queries.
- Consider a chunk_type filter on SemanticSearch (code-only vs docs-only
  scoping) — candidate student exercise.
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
