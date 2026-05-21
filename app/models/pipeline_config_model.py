from pydantic import BaseModel
from typing import Any

class AuthConfig(BaseModel):
  type: str = "none"

class ServerConfig(BaseModel):
  id:      str
  url:     str
  api:     str = "api/v1"
  timeout: int = 30
  auth:    AuthConfig = AuthConfig()
  headers: dict[str, str] = {}

class PromqlConfig(BaseModel):
  id:            str
  expr:          str
  export_labels: list[str] = []

class RangeConfig(BaseModel):
  id:             str
  backward_amt:   str
  backward_steps: int
  query_step:     str

class PipelineConfig(BaseModel):
  id:            str
  metadata:      dict[str, Any]
  promql_config: PromqlConfig
  range_config:  RangeConfig

class LoadedConfig(BaseModel):
  servers:      list[ServerConfig]
  pipelines:    list[PipelineConfig]
  trigger_time: str