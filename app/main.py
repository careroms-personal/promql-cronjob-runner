import sys
from app.bootstrap.config_loader import load_config
from app.bootstrap.build_runner_config import build_runner_config


def main():
  # Phase 1 - Bootstrap
  print("starting bootstrap...")

  loaded_config = load_config()
  print(f"config loaded: {len(loaded_config.servers)} servers, {len(loaded_config.pipelines)} pipelines")

  runner_config = build_runner_config(loaded_config)
  print(f"runner config built: {len(runner_config.pipelines)} pipelines ready")

  # Phase 2 - Execute
  print("starting execution...")

  # TODO: run pipelines

  # Phase 3 - Teardown
  print("teardown...")

  for server in runner_config.servers:
    server.session.close()

  print("done")
  sys.exit(0)


if __name__ == "__main__":
  main()