import os
import sys
import yaml
from app.models.pipeline_config_model import (
  AuthConfig,
  ServerConfig,
  PromqlConfig,
  RangeConfig,
  PipelineConfig,
  LoadedConfig,
)

def load_config() -> LoadedConfig:
  # --- load env vars ---
  trigger_time = os.environ.get("TRIGGER_TIME")
  config_path  = os.environ.get("PIPELINE_CONFIG_PATH")

  if not trigger_time:
    print("❌ missing env var: TRIGGER_TIME")
    sys.exit(1)

  if not config_path:
    print("❌ missing env var: PIPELINE_CONFIG_PATH")
    sys.exit(1)

  # --- load yaml ---
  try:
    with open(config_path, "r") as f:
      raw = yaml.safe_load(f)
  except FileNotFoundError:
    print(f"❌ config file not found: {config_path}")
    sys.exit(1)
  except yaml.YAMLError as e:
    print(f"❌ failed to parse config file: {e}")
    sys.exit(1)

  # --- parse servers ---
  raw_servers = raw.get("servers", [])
  if not raw_servers:
    print("❌ no servers found in config file")
    sys.exit(1)

  servers = [
    ServerConfig(
      id      = s["id"],
      url     = s["url"],
      api     = s.get("api", "api/v1"),
      timeout = s.get("timeout", 30),
      auth    = AuthConfig(type=s.get("auth", {}).get("type", "none")),
      headers = s.get("headers", {}),
    )
    for s in raw_servers
  ]

  # --- parse pipelines ---
  raw_pipelines = raw.get("pipelines", [])
  if not raw_pipelines:
    print("❌ no pipelines found in config file")
    sys.exit(1)

  pipelines = [
    PipelineConfig(
      id            = p["id"],
      metadata      = p.get("metadata", {}),
      promql_config = PromqlConfig(**p["promql_config"]),
      range_config  = RangeConfig(**p["range_config"]),
    )
    for p in raw_pipelines
  ]

  return LoadedConfig(
    servers      = servers,
    pipelines    = pipelines,
    trigger_time = trigger_time,
  )