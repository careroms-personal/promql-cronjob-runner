# AI-PROJECT-STRUCTURE.md
<!-- last ai update: 2026-05-20 -->

## Overview

`promql-cronjob-runner` is a Python application designed to run as a Kubernetes CronJob. It reads a pipeline config YAML, queries one or more Prometheus servers using PromQL, and processes the results. The execution model follows a 3-phase architecture (Bootstrap → Execute → Teardown).

---

## Directory Layout

```
promql-cronjob-runner/
├── .ai/                                      # AI-managed docs (Claude Code owned)
│   └── AI-PROJECT-STRUCTURE.md
├── app/
│   ├── main.py                               # Entry point — 3-phase orchestrator
│   ├── requirements.txt                      # Runtime dependencies
│   ├── bootstrap/
│   │   └── config_loader.py                  # Phase 1: env var + YAML config loading
│   └── models/
│       └── pipeline_config_model.py          # Pydantic config models
├── tests/
│   └── sandbox_prometheus_query_pipeline.yaml  # Example pipeline config for testing
├── Dockerfile
├── vibe-code-rule.yaml                       # Project coding rules
└── README.md
```

---

## Entry Point

**[app/main.py](../app/main.py)**

Three-phase orchestrator (currently Phase 1 only is implemented):

| Phase | Responsibility | Status |
|---|---|---|
| Bootstrap | Load env vars and validate pipeline config YAML | Implemented |
| Execute | Query Prometheus servers, process results | Not implemented |
| Teardown | Cleanup | Not implemented |

---

## Bootstrap Phase

**[app/bootstrap/config_loader.py](../app/bootstrap/config_loader.py)** — `load_config()`

**Required environment variables:**

| Variable | Description |
|---|---|
| `TRIGGER_TIME` | ISO timestamp of when the CronJob triggered |
| `PIPELINE_CONFIG_PATH` | Absolute path to the pipeline config YAML file |

**Steps:**
1. Read and validate env vars — exits with `❌` + `sys.exit(1)` if missing
2. Parse YAML with `yaml.safe_load()`
3. Validate `servers` section — at least 1 required
4. Validate `pipelines` section — at least 1 required
5. Return `LoadedConfig` pydantic object

---

## Data Models

**[app/models/pipeline_config_model.py](../app/models/pipeline_config_model.py)**

All models are Pydantic. Inter-phase data must always use these typed models — never plain dicts.

```
LoadedConfig
├── servers: list[ServerConfig]
├── pipelines: list[PipelineConfig]
└── trigger_time: str

ServerConfig
├── id: str
├── url: str
├── api: str              (default: "api/v1")
├── timeout: int          (default: 30)
├── auth: AuthConfig
│   └── type: str         (default: "none")
└── headers: dict[str, str]

PipelineConfig
├── id: str
├── metadata: dict[str, Any]   (e.g. cluster_name, environment)
├── promql_config: PromqlConfig
│   ├── id: str
│   ├── expr: str              (PromQL expression)
│   └── export_labels: list[str]
└── range_config: RangeConfig
    ├── id: str
    ├── backward_amt: str      (e.g. "7d")
    ├── backward_steps: int    (e.g. 4)
    └── query_step: str        (e.g. "1m", "5m", "30m", "60m")
```

---

## Pipeline Config YAML Format

Reference: [tests/sandbox_prometheus_query_pipeline.yaml](../tests/sandbox_prometheus_query_pipeline.yaml)

```yaml
servers:
  - id: <server-id>
    url: http://<host>:<port>
    api: api/v1
    timeout: 30
    auth:
      type: none
    headers: {}

pipelines:
  - id: <pipeline-id>
    metadata:
      cluster_name: <cluster>
      environment: <env>
    promql_config:
      id: <query-id>
      expr: '<promql expression>'
      export_labels: []
    range_config:
      id: <range-id>
      backward_amt: "7d"
      backward_steps: 4
      query_step: "1m"
```

---

## Dependencies

From `app/requirements.txt`:

| Package | Purpose |
|---|---|
| `pydantic` | Config validation and typed models |
| `PyYAML` | YAML parsing (`yaml.safe_load()` only) |

---

## Key Rules (from vibe-code-rule.yaml)

- 2-space indentation in all Python files
- Error messages: `❌` prefix + `sys.exit(1)`
- `yaml.safe_load()` exclusively — `yaml.load()` is forbidden
- Never print/log config values (treat all as potentially secret)
- Ask before creating any new module, subpackage, or executor
- `AI-*` files are Claude Code owned — update "last ai update" header on every edit