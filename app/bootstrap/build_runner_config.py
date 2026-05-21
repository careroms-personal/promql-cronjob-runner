import requests
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from app.models.pipeline_config_model import LoadedConfig, RangeConfig, ServerConfig
from app.models.runner_config_model import RunnerRangeConfig, RunnerQueryConfig, RunnerServerConfig, RunnerPipelineConfig, RunnerConfig

def _parse_backward_amt(backward_amt: str) -> relativedelta:
  unit  = backward_amt[-1]   # d, m, y
  value = int(backward_amt[:-1])

  if unit == "d":
    return relativedelta(days=value)
  elif unit == "m":
    return relativedelta(months=value)
  elif unit == "y":
    return relativedelta(years=value)
  else:
    raise ValueError(f"❌ unsupported backward_amt unit: {unit}")

def _build_runner_range(range_config: RangeConfig, trigger_time: int) -> list[RunnerRangeConfig]:
  trigger_dt = datetime.fromtimestamp(trigger_time, tz=timezone.utc)
  window_size = _parse_backward_amt(range_config.backward_amt)

  runner_ranges = []

  for step in range(range_config.backward_steps):
    end_dt = trigger_dt - (window_size * step)
    start_dt = end_dt - window_size

    runner_ranges.append(RunnerRangeConfig(
      id=range_config.id,
      step_count=step + 1,
      start=int(start_dt.timestamp()),
      end=int(end_dt.timestamp()),
      step=range_config.query_step,
    ))

  return runner_ranges

def _build_runner_server(server_config: ServerConfig):
  session = requests.Session()
  session.headers.update(server_config.headers)

  # auth placeholder — extend later
  # if server_config.auth.type == "bearer": ...
  # if server_config.auth.type == "basic": ...

  return RunnerServerConfig(
    server_id = server_config.id,
    session   = session,
    url       = server_config.url,
    timeout   = server_config.timeout,
  )

def build_runner_config(loaded_config: LoadedConfig):
  trigger_ts = int(datetime.fromisoformat(loaded_config.trigger_time).timestamp())

  servers = [
    _build_runner_server(s)
    for s in loaded_config.servers
  ]

  pipelines = []
  for p in loaded_config.pipelines:
    runner_ranges = _build_runner_range(p.range_config, trigger_ts)
    runner_query  = RunnerQueryConfig(
      id            = p.promql_config.id,
      expr          = p.promql_config.expr,
      export_labels = p.promql_config.export_labels,
      range_configs = runner_ranges,
    )

    pipelines.append(RunnerPipelineConfig(
      id       = p.id,
      metadata = p.metadata,
      query    = runner_query,
    ))

  return RunnerConfig(
    servers   = servers,
    pipelines = pipelines,
  )