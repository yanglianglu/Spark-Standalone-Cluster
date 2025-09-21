# Spark Standalone Connect Cluster

Local-first Spark Standalone cluster with Spark Connect and modular Docker Compose overlays. The stack targets Spark 4.0 images from Bitnami and keeps everything bind-mounted for fast iteration.

## Prerequisites

- Docker Engine 24+
- Docker Compose v2 (bundled with modern Docker Desktop)
- GNU Make (or `make` through WSL/Git Bash)
- Python 3.10+ with `pyspark==4.0.x` for the optional smoke test

## Quickstart

1. Copy or adjust the defaults in [`.env`](.env) as needed (ports, image tag, resource sizing).
2. Start the core services (master, worker, Spark Connect):
   ```sh
   make up
   ```
3. Visit the UIs:
   - Master UI: <http://localhost:${MASTER_UI_PORT:-8080}>
   - Worker UI: <http://localhost:${WORKER_UI_PORT:-8081}>
   - Spark Connect Session UI: <http://localhost:${CONNECT_UI_PORT:-4040}>
4. Drop CSV/Parquet/JSON files under `./data/` on the host. Inside containers they are reachable under `file:/opt/data/...`.

### Overlays

- Development logging (json-file rotation, extra env):
  ```sh
  make up-dev
  ```
- History server + second worker:
  ```sh
  make up-full
  ```

Use `make down` or `make down-full` with the same file combinations you used to stop the stack. The `FILES` variable lets you target a specific set of compose files:
```sh
make down FILES="-f compose.base.yml -f compose.spark.yml -f compose.history.yml"
```

## Data locations

- Host bind: `./data/`
- Container path: `/opt/data`
- Default warehouse: `file:/opt/data/warehouse`
- Event logs (named volume): `${EVENTS_VOLUME}` mounted at `/opt/spark/events`

## Smoke test (Spark Connect)

With the stack running and `pyspark` installed locally:
```sh
make smoke
```
The script connects to `sc://localhost:${CONNECT_GRPC_PORT:-15002}`, reads `data/samples/people.csv`, writes `demo.people`, and verifies the row count.

## Resetting state

To tear everything down, remove volumes, and clean the local warehouse/metastore cache:
```sh
make reset
```

## Documentation

Full requirements and architecture notes live in [`docs/requirements.md`](docs/requirements.md).
