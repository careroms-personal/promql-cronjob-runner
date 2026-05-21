import pytest
import requests
from dateutil.relativedelta import relativedelta

from app.bootstrap.build_runner_config import (
  _parse_backward_amt,
  _build_runner_range,
  _build_runner_server,
  build_runner_config,
)
from app.models.pipeline_config_model import (
  AuthConfig,
  ServerConfig,
  PromqlConfig,
  RangeConfig,
  PipelineConfig,
  LoadedConfig,
)
from app.models.runner_config_model import (
  RunnerRangeConfig,
  RunnerServerConfig,
  RunnerQueryConfig,
  RunnerPipelineConfig,
  RunnerConfig,
)

TRIGGER_TS  = 1779235200       # 2026-05-20 00:00:00 UTC
TRIGGER_ISO = "2026-05-20T00:00:00Z"
SEVEN_DAYS  = 7 * 86400        # 604800 seconds


@pytest.fixture
def range_cfg_7d_4_1m():
  return RangeConfig(
    id="7d_4_1m",
    backward_amt="7d",
    backward_steps=4,
    query_step="1m",
  )


@pytest.fixture
def server_cfg():
  return ServerConfig(
    id="test_server",
    url="http://localhost:9090",
    api="api/v1",
    timeout=30,
    auth=AuthConfig(type="none"),
    headers={"X-Custom-Header": "test-value"},
  )


@pytest.fixture
def loaded_cfg():
  return LoadedConfig(
    trigger_time=TRIGGER_ISO,
    servers=[ServerConfig(
      id="srv1",
      url="http://localhost:9090",
      api="api/v1",
      timeout=30,
      auth=AuthConfig(type="none"),
      headers={},
    )],
    pipelines=[PipelineConfig(
      id="pipeline1",
      metadata={"cluster_name": "test_cluster", "environment": "test"},
      promql_config=PromqlConfig(
        id="query1",
        expr='rate(node_cpu_seconds_total[10m])',
        export_labels=["instance"],
      ),
      range_config=RangeConfig(
        id="range1",
        backward_amt="7d",
        backward_steps=2,
        query_step="1m",
      ),
    )],
  )


class TestParseBackwardAmt:

  def test_days(self):
    assert _parse_backward_amt("7d") == relativedelta(days=7)

  def test_months(self):
    assert _parse_backward_amt("3m") == relativedelta(months=3)

  def test_years(self):
    assert _parse_backward_amt("1y") == relativedelta(years=1)

  def test_single_day(self):
    assert _parse_backward_amt("1d") == relativedelta(days=1)

  def test_unsupported_unit_raises(self):
    with pytest.raises(ValueError, match="unsupported backward_amt unit"):
      _parse_backward_amt("5x")


class TestBuildRunnerRange:

  def test_returns_list(self, range_cfg_7d_4_1m):
    result = _build_runner_range(range_cfg_7d_4_1m, TRIGGER_TS)
    assert isinstance(result, list)

  def test_count_matches_backward_steps(self, range_cfg_7d_4_1m):
    result = _build_runner_range(range_cfg_7d_4_1m, TRIGGER_TS)
    assert len(result) == 4

  def test_all_items_are_runner_range_config(self, range_cfg_7d_4_1m):
    result = _build_runner_range(range_cfg_7d_4_1m, TRIGGER_TS)
    assert all(isinstance(r, RunnerRangeConfig) for r in result)

  def test_step_count_increments_from_one(self, range_cfg_7d_4_1m):
    result = _build_runner_range(range_cfg_7d_4_1m, TRIGGER_TS)
    assert [r.step_count for r in result] == [1, 2, 3, 4]

  def test_id_preserved(self, range_cfg_7d_4_1m):
    result = _build_runner_range(range_cfg_7d_4_1m, TRIGGER_TS)
    assert all(r.id == "7d_4_1m" for r in result)

  def test_query_step_preserved(self, range_cfg_7d_4_1m):
    result = _build_runner_range(range_cfg_7d_4_1m, TRIGGER_TS)
    assert all(r.step == "1m" for r in result)

  def test_first_window_end_equals_trigger(self, range_cfg_7d_4_1m):
    result = _build_runner_range(range_cfg_7d_4_1m, TRIGGER_TS)
    assert result[0].end == TRIGGER_TS

  def test_window_timestamps_7d(self, range_cfg_7d_4_1m):
    result = _build_runner_range(range_cfg_7d_4_1m, TRIGGER_TS)
    assert result[0].end   == TRIGGER_TS
    assert result[0].start == TRIGGER_TS - SEVEN_DAYS
    assert result[1].end   == TRIGGER_TS - SEVEN_DAYS
    assert result[1].start == TRIGGER_TS - 2 * SEVEN_DAYS
    assert result[2].end   == TRIGGER_TS - 2 * SEVEN_DAYS
    assert result[2].start == TRIGGER_TS - 3 * SEVEN_DAYS
    assert result[3].end   == TRIGGER_TS - 3 * SEVEN_DAYS
    assert result[3].start == TRIGGER_TS - 4 * SEVEN_DAYS

  def test_windows_are_sequential(self, range_cfg_7d_4_1m):
    result = _build_runner_range(range_cfg_7d_4_1m, TRIGGER_TS)
    for i in range(len(result) - 1):
      assert result[i].start == result[i + 1].end

  def test_custom_step_count(self):
    cfg = RangeConfig(id="r", backward_amt="7d", backward_steps=2, query_step="5m")
    result = _build_runner_range(cfg, TRIGGER_TS)
    assert len(result) == 2

  def test_custom_query_step_preserved(self):
    cfg = RangeConfig(id="r", backward_amt="7d", backward_steps=1, query_step="30m")
    result = _build_runner_range(cfg, TRIGGER_TS)
    assert result[0].step == "30m"


class TestBuildRunnerServer:

  def test_returns_runner_server_config(self, server_cfg):
    result = _build_runner_server(server_cfg)
    assert isinstance(result, RunnerServerConfig)

  def test_server_id(self, server_cfg):
    result = _build_runner_server(server_cfg)
    assert result.server_id == "test_server"

  def test_url(self, server_cfg):
    result = _build_runner_server(server_cfg)
    assert result.url == "http://localhost:9090"

  def test_timeout(self, server_cfg):
    result = _build_runner_server(server_cfg)
    assert result.timeout == 30

  def test_session_is_requests_session(self, server_cfg):
    result = _build_runner_server(server_cfg)
    assert isinstance(result.session, requests.Session)

  def test_headers_applied_to_session(self, server_cfg):
    result = _build_runner_server(server_cfg)
    assert result.session.headers["X-Custom-Header"] == "test-value"


class TestBuildRunnerConfig:

  def test_returns_runner_config(self, loaded_cfg):
    result = build_runner_config(loaded_cfg)
    assert isinstance(result, RunnerConfig)

  def test_server_count(self, loaded_cfg):
    result = build_runner_config(loaded_cfg)
    assert len(result.servers) == 1

  def test_server_id(self, loaded_cfg):
    result = build_runner_config(loaded_cfg)
    assert result.servers[0].server_id == "srv1"

  def test_pipeline_count(self, loaded_cfg):
    result = build_runner_config(loaded_cfg)
    assert len(result.pipelines) == 1

  def test_pipeline_id_preserved(self, loaded_cfg):
    result = build_runner_config(loaded_cfg)
    assert result.pipelines[0].id == "pipeline1"

  def test_pipeline_metadata_preserved(self, loaded_cfg):
    result = build_runner_config(loaded_cfg)
    assert result.pipelines[0].metadata["cluster_name"] == "test_cluster"
    assert result.pipelines[0].metadata["environment"]  == "test"

  def test_pipeline_query_is_runner_query_config(self, loaded_cfg):
    result = build_runner_config(loaded_cfg)
    assert isinstance(result.pipelines[0].query, RunnerQueryConfig)

  def test_pipeline_query_id(self, loaded_cfg):
    result = build_runner_config(loaded_cfg)
    assert result.pipelines[0].query.id == "query1"

  def test_pipeline_query_expr(self, loaded_cfg):
    result = build_runner_config(loaded_cfg)
    assert result.pipelines[0].query.expr == "rate(node_cpu_seconds_total[10m])"

  def test_pipeline_query_export_labels(self, loaded_cfg):
    result = build_runner_config(loaded_cfg)
    assert result.pipelines[0].query.export_labels == ["instance"]

  def test_pipeline_range_configs_count(self, loaded_cfg):
    result = build_runner_config(loaded_cfg)
    assert len(result.pipelines[0].query.range_configs) == 2

  def test_pipeline_range_configs_first_end_equals_trigger(self, loaded_cfg):
    result = build_runner_config(loaded_cfg)
    assert result.pipelines[0].query.range_configs[0].end == TRIGGER_TS
