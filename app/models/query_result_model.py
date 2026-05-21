from pydantic import BaseModel

class QueryResult(BaseModel):
  pipeline_id: str
  server_id: str
  ts: int
  value: float
  labels: dict

class QueryFailure(BaseModel):
  pipeline_id: str
  server_id: str
  range_id: str
  url: str
  api: str
  timeout: int
  headers: dict
  auth: dict
  start_ts: int
  end_ts: int
  step: str
  expr: str
  export_labels: list[str]
  error_type: str
  error_msg: str