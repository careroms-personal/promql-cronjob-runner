import psycopg2
import json
import os

from datetime import datetime, timezone
from app.models.query_result_model import QueryResult, QueryFailure

def _get_connection():
  import os
  return psycopg2.connect(
    host     = os.environ.get("POSTGRES_HOST"),
    port     = os.environ.get("POSTGRES_PORT", 5432),
    user     = os.environ.get("POSTGRES_USERNAME"),
    password = os.environ.get("POSTGRES_PASSWORD"),
    dbname   = os.environ.get("POSTGRES_DATABASE"),
  )

def write_results(conn, results: list[QueryResult]) -> None:
  if not results:
    return
  
  with conn.cursor() as cur:
    for row in results:
      cur.execute(
        """
        INSERT INTO pipeline_metrics (
          ts, pipeline_id, server_id, range_id,
          start_ts, end_ts, step, expr,
          value, labels
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
          datetime.fromtimestamp(row.ts, tz=timezone.utc),
          row.pipeline_id,
          row.server_id,
          row.range_id,
          row.start_ts,
          row.end_ts,
          row.step,
          row.expr,
          row.value,
          json.dumps(row.labels),
        )
      )
  conn.commit()

def write_failures(conn, failures: list[QueryFailure]) -> None:
  if not failures:
    return

  with conn.cursor() as cur:
    for row in failures:
      cur.execute(
        """
        INSERT INTO pipeline_failures (
          ts, pipeline_id, server_id, range_id,
          url, api, timeout, headers, auth,
          start_ts, end_ts, step, expr, export_labels,
          error_type, error_msg
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
          datetime.now(tz=timezone.utc),
          row.pipeline_id,
          row.server_id,
          row.range_id,
          row.url,
          row.api,
          row.timeout,
          json.dumps(row.headers),
          json.dumps(row.auth),
          row.start_ts,
          row.end_ts,
          row.step,
          row.expr,
          json.dumps(row.export_labels),
          row.error_type,
          row.error_msg,
        )
      )
  conn.commit()

def connect_db():
  import sys
  try:
    conn = _get_connection()
    print("✅ db connected")
    return conn
  except Exception as e:
    print(f"❌ db connection failed: {e}")
    sys.exit(1)