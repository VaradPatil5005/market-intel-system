-- ============================================================================
-- Multi-Agent Market Intelligence System — SQL schema
-- SQLite-friendly by default; portable to PostgreSQL (see notes below).
--   - AUTOINCREMENT / TEXT PKs work on both; on Postgres swap TEXT PK to
--     use gen_random_uuid() or keep client-generated string IDs (used here).
--   - All timestamps are stored as ISO-8601 text for engine portability.
-- ============================================================================

CREATE TABLE IF NOT EXISTS raw_sources (
    id              TEXT PRIMARY KEY,
    source_name     TEXT NOT NULL,
    source_type     TEXT NOT NULL,           -- rss | api | scrape | mock
    url             TEXT,
    title           TEXT,
    content         TEXT,
    published_at    TEXT,
    fetched_at      TEXT NOT NULL,
    credibility_score REAL,
    credibility_explanation TEXT,
    is_rejected     INTEGER DEFAULT 0,
    raw_metadata    TEXT                     -- JSON blob
);
CREATE INDEX IF NOT EXISTS idx_raw_sources_source_name ON raw_sources(source_name);
CREATE INDEX IF NOT EXISTS idx_raw_sources_published_at ON raw_sources(published_at);

CREATE TABLE IF NOT EXISTS entities (
    id              TEXT PRIMARY KEY,
    canonical_name  TEXT NOT NULL,
    entity_type     TEXT NOT NULL,           -- company | product | person | topic
    aliases         TEXT,                    -- JSON array of alias strings
    source_id       TEXT REFERENCES raw_sources(id),
    first_seen_at   TEXT NOT NULL,
    last_seen_at    TEXT NOT NULL,
    mention_count   INTEGER DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_entities_canonical_name ON entities(canonical_name);

CREATE TABLE IF NOT EXISTS sentiment_results (
    id              TEXT PRIMARY KEY,
    source_id       TEXT REFERENCES raw_sources(id),
    entity_id       TEXT REFERENCES entities(id),
    sentiment_label TEXT NOT NULL,           -- positive | negative | neutral
    polarity_score  REAL NOT NULL,
    subject         TEXT,
    explanation     TEXT,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sentiment_entity ON sentiment_results(entity_id);

CREATE TABLE IF NOT EXISTS trend_results (
    id              TEXT PRIMARY KEY,
    topic           TEXT NOT NULL,
    trend_label     TEXT NOT NULL,           -- rising | falling | stable | anomalous
    current_score   REAL NOT NULL,
    historical_avg  REAL,
    change_pct      REAL,
    window_days     INTEGER DEFAULT 7,
    ewma_mean       REAL,
    ewma_std        REAL,
    z_score         REAL,
    is_anomalous    INTEGER DEFAULT 0,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_trend_topic ON trend_results(topic);

CREATE TABLE IF NOT EXISTS insights (
    id              TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL,
    category        TEXT NOT NULL,           -- trend | sentiment | competitor | risk | rag
    text            TEXT NOT NULL,
    related_entity_id TEXT REFERENCES entities(id),
    supporting_source_ids TEXT,              -- JSON array of raw_source ids
    -- Taxonomy: fact | analysis | prediction | recommendation
    insight_type    TEXT NOT NULL DEFAULT 'analysis',
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_insights_run_id ON insights(run_id);

CREATE TABLE IF NOT EXISTS confidence_scores (
    id              TEXT PRIMARY KEY,
    insight_id      TEXT REFERENCES insights(id),
    score           REAL NOT NULL,
    source_quality_component REAL,
    agreement_component REAL,
    recency_component REAL,
    completeness_component REAL,
    is_flagged      INTEGER DEFAULT 0,
    flag_reason     TEXT,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_confidence_insight ON confidence_scores(insight_id);

CREATE TABLE IF NOT EXISTS audit_logs (
    id              TEXT PRIMARY KEY,
    agent_name      TEXT NOT NULL,
    step            TEXT NOT NULL,
    action          TEXT NOT NULL,
    input_summary   TEXT,
    output_summary  TEXT,
    score           REAL,
    decision        TEXT,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_agent ON audit_logs(agent_name);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at);

CREATE TABLE IF NOT EXISTS checkpoints (
    id              TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL,
    node_name       TEXT NOT NULL,
    state_snapshot  TEXT NOT NULL,           -- JSON blob of graph state
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_checkpoints_run_id ON checkpoints(run_id);

CREATE TABLE IF NOT EXISTS report_exports (
    id              TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL,
    report_title    TEXT NOT NULL,
    executive_summary TEXT,
    full_report_json TEXT NOT NULL,
    approved        INTEGER DEFAULT 0,
    approved_by     TEXT,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_metrics (
    id              TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL,
    agent_name      TEXT NOT NULL,
    step            TEXT NOT NULL,
    duration_seconds REAL NOT NULL,
    success         INTEGER NOT NULL,
    error_message   TEXT,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_agent_metrics_run_id ON agent_metrics(run_id);


-- ============================================================================
-- v2 tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS forecast_results (
    id              TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL,
    entity_id       TEXT,
    entity_name     TEXT NOT NULL,
    predicted_direction TEXT NOT NULL,       -- up | down | stable
    predicted_magnitude REAL,
    observations_used INTEGER DEFAULT 0,
    model_used      TEXT NOT NULL,
    confidence      REAL,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_forecast_run_id ON forecast_results(run_id);

CREATE TABLE IF NOT EXISTS user_queries (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL,
    query_text      TEXT NOT NULL,
    extracted_entities TEXT,                 -- JSON list
    intent_category TEXT,
    run_id          TEXT,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_user_queries_user_id ON user_queries(user_id);

CREATE TABLE IF NOT EXISTS user_interest_profiles (
    user_id         TEXT PRIMARY KEY,
    watchlist_override TEXT,                 -- JSON list
    risk_appetite   TEXT DEFAULT 'moderate',
    preferred_depth TEXT DEFAULT 'standard',
    top_categories  TEXT,                    -- JSON list
    query_count     INTEGER DEFAULT 0,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_learnings (
    id              TEXT PRIMARY KEY,
    source_insight_id TEXT,
    entity_name     TEXT,
    category        TEXT,
    human_action    TEXT NOT NULL,           -- reject | modify
    reviewer_note   TEXT,
    lesson_text     TEXT NOT NULL,
    lesson_type     TEXT,
    lesson_embedding TEXT,                   -- JSON float list
    is_active       INTEGER DEFAULT 1,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS grounding_records (
    id              TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL,
    claim_text      TEXT NOT NULL,
    claimed_value   TEXT NOT NULL,
    verdict         TEXT NOT NULL,           -- verified | flagged | redacted
    nearest_observed_value TEXT,
    evidence_source TEXT,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_grounding_run_id ON grounding_records(run_id);

CREATE TABLE IF NOT EXISTS price_snapshots (
    id              TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL,
    entity_id       TEXT,
    entity_name     TEXT NOT NULL,
    ticker          TEXT NOT NULL,
    current_price   REAL,
    price_7d_return_pct REAL,
    price_30d_return_pct REAL,
    volatility_30d  REAL,
    rsi_14          REAL,
    bb_squeeze      INTEGER DEFAULT 0,
    volume_anomaly  INTEGER DEFAULT 0,
    data_source     TEXT DEFAULT 'yfinance',
    fetched_at      TEXT NOT NULL,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_price_snapshots_run_id ON price_snapshots(run_id);

CREATE TABLE IF NOT EXISTS review_queue (
    id              TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'PENDING',  -- PENDING | APPROVED | REJECTED
    flagged_count   INTEGER DEFAULT 0,
    avg_confidence  REAL,
    summary_json    TEXT,                    -- JSON snapshot of flagged insights
    reviewer_notes  TEXT,
    reviewed_by     TEXT,
    created_at      TEXT NOT NULL,
    resolved_at     TEXT
);
CREATE INDEX IF NOT EXISTS idx_review_queue_run_id ON review_queue(run_id);
