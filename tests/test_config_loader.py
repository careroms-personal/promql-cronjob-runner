import pytest
from pathlib import Path

from app.bootstrap.config_loader import load_config
from app.models.pipeline_config_model import LoadedConfig

SANDBOX_YAML = str(Path(__file__).parent / "sandbox_prometheus_query_pipeline.yaml")
TRIGGER_TIME = "2026-05-20T00:00:00Z"


@pytest.fixture
def env_sandbox(monkeypatch):
  monkeypatch.setenv("TRIGGER_TIME", TRIGGER_TIME)
  monkeypatch.setenv("PIPELINE_CONFIG_PATH", SANDBOX_YAML)


class TestLoadConfigHappyPath:

  def test_returns_loaded_config_type(self, env_sandbox):
    result = load_config()
    assert isinstance(result, LoadedConfig)

  def test_trigger_time_preserved(self, env_sandbox):
    result = load_config()
    assert result.trigger_time == TRIGGER_TIME

  def test_server_count(self, env_sandbox):
    result = load_config()
    assert len(result.servers) == 1

  def test_server_fields(self, env_sandbox):
    result = load_config()
    s = result.servers[0]
    assert s.id        == "sandbox_prometheus"
    assert s.url       == "http://localhost:9090"
    assert s.api       == "api/v1"
    assert s.timeout   == 30
    assert s.auth.type == "none"
    assert s.headers   == {}

  def test_pipeline_count(self, env_sandbox):
    result = load_config()
    assert len(result.pipelines) == 8

  def test_pipeline_ids_present(self, env_sandbox):
    result = load_config()
    ids = [p.id for p in result.pipelines]
    assert "node_cpu_rate_query_10m_windows_size__node_cpu_usage_rate_10m__7d_4_1m" in ids
    assert "node_memory_active_usage__node_memory_usage__7d_4_60m" in ids

  def test_pipeline_metadata(self, env_sandbox):
    result = load_config()
    p = result.pipelines[0]
    assert p.metadata["cluster_name"] == "sandbox_cluster"
    assert p.metadata["environment"]  == "sandbox"

  def test_promql_config_first_pipeline(self, env_sandbox):
    result = load_config()
    pq = result.pipelines[0].promql_config
    assert pq.id            == "node_cpu_usage_rate_10m"
    assert "rate(node_cpu_seconds_total" in pq.expr
    assert pq.export_labels == ["instance"]

  def test_range_config_first_pipeline(self, env_sandbox):
    result = load_config()
    rc = result.pipelines[0].range_config
    assert rc.id             == "7d_4_1m"
    assert rc.backward_amt   == "7d"
    assert rc.backward_steps == 4
    assert rc.query_step     == "1m"


class TestLoadConfigErrors:

  def test_missing_trigger_time_exits(self, monkeypatch):
    monkeypatch.delenv("TRIGGER_TIME", raising=False)
    monkeypatch.setenv("PIPELINE_CONFIG_PATH", SANDBOX_YAML)
    with pytest.raises(SystemExit) as exc:
      load_config()
    assert exc.value.code == 1

  def test_missing_config_path_exits(self, monkeypatch):
    monkeypatch.setenv("TRIGGER_TIME", TRIGGER_TIME)
    monkeypatch.delenv("PIPELINE_CONFIG_PATH", raising=False)
    with pytest.raises(SystemExit) as exc:
      load_config()
    assert exc.value.code == 1

  def test_file_not_found_exits(self, monkeypatch):
    monkeypatch.setenv("TRIGGER_TIME", TRIGGER_TIME)
    monkeypatch.setenv("PIPELINE_CONFIG_PATH", "/nonexistent/config.yaml")
    with pytest.raises(SystemExit) as exc:
      load_config()
    assert exc.value.code == 1

  def test_invalid_yaml_exits(self, monkeypatch, tmp_path):
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text(":\ninvalid: yaml:\n  - [unclosed")
    monkeypatch.setenv("TRIGGER_TIME", TRIGGER_TIME)
    monkeypatch.setenv("PIPELINE_CONFIG_PATH", str(bad_file))
    with pytest.raises(SystemExit) as exc:
      load_config()
    assert exc.value.code == 1

  def test_empty_servers_exits(self, monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("servers: []\npipelines:\n- id: x\n")
    monkeypatch.setenv("TRIGGER_TIME", TRIGGER_TIME)
    monkeypatch.setenv("PIPELINE_CONFIG_PATH", str(cfg))
    with pytest.raises(SystemExit) as exc:
      load_config()
    assert exc.value.code == 1

  def test_empty_pipelines_exits(self, monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("servers:\n- id: s\n  url: http://x\npipelines: []\n")
    monkeypatch.setenv("TRIGGER_TIME", TRIGGER_TIME)
    monkeypatch.setenv("PIPELINE_CONFIG_PATH", str(cfg))
    with pytest.raises(SystemExit) as exc:
      load_config()
    assert exc.value.code == 1