CREATE EXTENSION IF NOT EXISTS timescaledb;

-- metrics table (populated by runner)
CREATE TABLE IF NOT EXISTS pipeline_metrics (
  ts          TIMESTAMPTZ   NOT NULL,
  pipeline_id TEXT          NOT NULL,
  server_id   TEXT          NOT NULL,
  value       DOUBLE PRECISION NOT NULL,
  labels      JSONB
);
SELECT create_hypertable('pipeline_metrics', 'ts');

-- failures table (replayable, all info needed to re-query)
CREATE TABLE IF NOT EXISTS pipeline_failures (
  ts          TIMESTAMPTZ NOT NULL,
  pipeline_id TEXT        NOT NULL,
  server_id   TEXT        NOT NULL,
  range_id    TEXT        NOT NULL,
  url         TEXT        NOT NULL,
  api         TEXT        NOT NULL,
  timeout     INTEGER     NOT NULL,
  headers     JSONB       NOT NULL,
  auth        JSONB       NOT NULL,
  start_ts    BIGINT      NOT NULL,
  end_ts      BIGINT      NOT NULL,
  step        TEXT        NOT NULL,
  expr        TEXT        NOT NULL,
  export_labels JSONB     NOT NULL,
  error_type  TEXT        NOT NULL,
  error_msg   TEXT        NOT NULL
);
SELECT create_hypertable('pipeline_failures', 'ts');