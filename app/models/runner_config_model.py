from pydantic import BaseModel, ConfigDict
from requests import Session
from typing import Any

class CustomBaseModel(BaseModel):
  model_config = ConfigDict(arbitrary_types_allowed=True)

class RunnerServerConfig(CustomBaseModel):
  server_id: str
  session: Session

  url: str
  api: str
  timeout: int

class RunnerRangeConfig(CustomBaseModel):
  id: str
  step_count: int
  start: int
  end: int
  step: str

class RunnerQueryConfig(CustomBaseModel):
  id: str
  expr: str
  export_labels: list[str]
  range_configs: list[RunnerRangeConfig]

class RunnerPipelineConfig(CustomBaseModel):
  id: str
  metadata: dict[str, Any]
  query: RunnerQueryConfig

class RunnerConfig(CustomBaseModel):
  servers: list[RunnerServerConfig]
  pipelines: list[RunnerPipelineConfig]
