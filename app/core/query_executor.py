import requests
from app.models.runner_config_model import RunnerServerConfig, RunnerPipelineConfig, RunnerRangeConfig
from app.models.query_result_model import QueryFailure, QueryResult

def _build_url(server: RunnerServerConfig) -> str:
  return f"{server.url}/{server.api}/query_range"

def _filter_labels(metric: dict, export_labels: list[str]) -> dict:
  if not export_labels:
    return metric
  return {k: v for k, v in metric.items() if k in export_labels}

def _query_range(
  server: RunnerServerConfig,
  pipeline: RunnerPipelineConfig,
  range_config: RunnerRangeConfig,
) -> tuple[list[QueryResult], QueryFailure | None]:
  
  url = _build_url(server)
  params = {
    "query": pipeline.query.expr,
    "start": range_config.start,
    "end": range_config.end,
    "step": range_config.step,
  }

  try:
    response = server.session.get(url, params=params, timeout=server.timeout)
    response.raise_for_status()
    data = response.json()
  
  except requests.exceptions.Timeout as e:
    return [], QueryFailure(
      pipeline_id=pipeline.id,
      server_id=server.server_id,
      range_id=range_config.id,
      url=server.url,
      api=server.api,
      timeout=server.timeout,
      headers=dict(server.session.headers),
      auth=dict(server.session.auth),
      start_ts=range_config.start,
      end_ts=range_config.end,
      step=range_config.step,
      expr=pipeline.query.expr,
      export_labels=pipeline.query.export_labels,
      error_type="timeout",
      error_msg=str(e)
    )
  
  except requests.exceptions.HTTPError as e:
    return [], QueryFailure(
      pipeline_id=pipeline.id,
      server_id=server.server_id,
      range_id=range_config.id,
      url=server.url,
      api=server.api,
      timeout=server.timeout,
      headers=dict(server.session.headers),
      auth=dict(server.session.auth),
      start_ts=range_config.start,
      end_ts=range_config.end,
      step=range_config.step,
      expr=pipeline.query.expr,
      export_labels=pipeline.query.export_labels,
      error_type="http_error",
      error_msg=str(e)
    )
  
  except requests.exceptions.ConnectionError as e:
    return [], QueryFailure(
      pipeline_id=pipeline.id,
      server_id=server.server_id,
      range_id=range_config.id,
      url=server.url,
      api=server.api,
      timeout=server.timeout,
      headers=dict(server.session.headers),
      auth=dict(server.session.auth),
      start_ts=range_config.start,
      end_ts=range_config.end,
      step=range_config.step,
      expr=pipeline.query.expr,
      export_labels=pipeline.query.export_labels,
      error_type="connection_error",
      error_msg=str(e)
    )
  
  results = []

  for series in data.get("data", {}).get("result", []):
    labels = _filter_labels(series.get("metric", {}), pipeline.query.export_labels)

    for ts, value in series.get("values", []):
      results.append(QueryResult(
        pipeline_id=pipeline.id,
        server_id=server.server_id,
        ts=int(ts),
        value=float(value),
        labels=labels,
      ))

  if not results:
    print(f"⚠️  no data returned: pipeline={pipeline.id} server={server.server_id} range={range_config.id}")

  return results, None

def execute_query(
  server: RunnerServerConfig,
  pipeline: RunnerPipelineConfig,
) -> tuple[list[QueryResult], list[QueryFailure]]:
  all_results = []
  all_failures = []

  for range_config in pipeline.query.range_configs:
    results, failure = _query_range(server, pipeline, range_config)

    if failure:
      print(f"❌ query failed: pipeline={pipeline.id} server={server.server_id} range={range_config.id} error={failure.error_type}")
      all_failures.append(failure)
    else:
      all_results.extend(results)

  return all_results, all_failures
