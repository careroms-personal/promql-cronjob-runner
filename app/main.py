import sys
from itertools import product
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.bootstrap.config_loader import load_config
from app.bootstrap.build_runner_config import build_runner_config
from app.core.query_executor import execute_query
from app.writer.db_writer import connect_db, write_results, write_failures


def main():
  # Phase 1 - Bootstrap
  print("starting bootstrap...")

  loaded_config = load_config()
  print(f"config loaded: {len(loaded_config.servers)} servers, {len(loaded_config.pipelines)} pipelines")

  runner_config = build_runner_config(loaded_config)
  print(f"runner config built: {len(runner_config.servers)} servers, {len(runner_config.pipelines)} pipelines ready")

  conn = connect_db()

  # Phase 2 - Execute
  print("starting execution...")

  all_results = []
  all_failures = []

  with ThreadPoolExecutor() as executor:
    futures = {
      executor.submit(execute_query, server, pipeline): (server.server_id, pipeline.id)
      for server, pipeline in product(runner_config.servers, runner_config.pipelines)
    }

  for future in as_completed(futures):
    server_id, pipeline_id = futures[future]
    
    try:
      results, failures = future.result()
      print(f"✅ done: server={server_id} pipeline={pipeline_id} rows={len(results)} failures={len(failures)}")

      all_results.extend(results)
      all_failures.extend(failures)
      
    except Exception as e:
      print(f"❌ unexpected error: server={server_id} pipeline={pipeline_id} error={e}")
  
  write_results(conn, all_results)
  write_failures(conn, all_failures)

  # Phase 3 - Teardown
  print("teardown...")

  for server in runner_config.servers:
    server.session.close()

  conn.close()

  if all_failures:
    print(f"❌ completed with {len(all_failures)} failures, {len(all_results)} rows written")
    sys.exit(1)

  print(f"✅ completed: {len(all_results)} rows written")
  sys.exit(0)

if __name__ == "__main__":
  main()