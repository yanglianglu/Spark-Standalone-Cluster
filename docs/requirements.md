# Spark Connect Standalone - Requirements Summary (Compose Spec, v2+)

## 1) Objective

Stand up a **minimal Spark Standalone cluster with Spark Connect enabled** and a **bind-mounted local data directory**, optimized for development and quick experiments. Keep it modular so optional pieces (History UI, extra workers, dev logging) can be toggled via file overlays.

## 2) Architecture (minimal core)

* **spark-master**: Spark master (RPC `7077`, UI `8080` on host).
* **spark-worker**: At least one worker (UI `8081` on host).
* **spark-connect**: Spark Connect Server (gRPC `15002`, per-session UI `4040` on host).
* **Optional**: **spark-history** (UI `18080`) if event logs are enabled.

### Networks & Volumes

* Single internal network (for example `spark-net`).
* Named volume for Spark event logs (for example `spark-events`).
* **Bind-mount** for user data: host `./data` <-> container `/opt/data`.
  * Warehouse path defaults to `file:/opt/data/warehouse`.

## 3) Compose Layout (modular)

* `compose.base.yml` - shared anchors (env, mounts), networks, volumes.
* `compose.spark.yml` - master, worker, connect.
* `compose.history.yml` - history server (optional).
* `compose.dev.yml` - dev conveniences (log rotation, extra env).
* `compose.scale-2w.yml` - a second worker (optional).
* `.env` - tunables: images, ports, worker sizing, paths.
* `Makefile` - common commands (`up`, `up-dev`, `up-full`, `down`, `reset`).

> Using Compose v2+ you omit the top-level `version:` key in all files.
> You stack files with `docker compose -f ... -f ... up -d`.

## 4) Images & Versions

* **Spark**: `bitnami/spark:4.0.x` (cluster plus Connect Server scripts baked in).
* Java baseline: **Java 17+** compatible.
* Pin exact tags in `.env` (for example `SPARK_IMAGE=bitnami/spark:4.0.0`) for repeatability.

## 5) Configuration (defaults)

* **Spark Connect Server** flags:
  * `--master spark://spark-master:7077`
  * `--conf spark.ui.enabled=true`
  * `--conf spark.sql.warehouse.dir=file:/opt/data/warehouse`
  * `--conf spark.sql.catalogImplementation=in-memory`
* **spark-defaults.conf**:
  * `spark.log.structuredLogging.enabled true`
  * `spark.sql.warehouse.dir file:/opt/data/warehouse`
  * `spark.hadoop.fs.file.impl org.apache.hadoop.fs.RawLocalFileSystem`
  * `spark.eventLog.enabled true`
  * `spark.eventLog.dir file:/opt/spark/events`
  * Reasonable memory defaults for Connect jobs (for example `spark.driver.memory 2g`, `spark.executor.memory 2g`).

## 6) Ports (host -> container)

* Master UI: `${MASTER_UI_PORT:-8080} -> 8080`
* Worker UI: `${WORKER_UI_PORT:-8081} -> 8081`
* Connect gRPC: `${CONNECT_GRPC_PORT:-15002} -> 15002`
* Connect UI: `${CONNECT_UI_PORT:-4040} -> 4040`
* History UI (optional): `${HISTORY_UI_PORT:-18080} -> 18080`

## 7) Health, Startup, & Resource Controls

* **Healthcheck** on master UI (simple HTTP GET) to gate dependent startups.
* `depends_on` with `condition: service_healthy` for worker and connect.
* **Resource limits** (`deploy.resources.limits`) on each service to avoid host overload.
* **Log rotation** (json-file driver) for dev profile to cap log growth.

## 8) Data & Warehouse

* All examples must use **container paths** (because execution happens inside containers):
  * Files: `file:/opt/data/...`
  * Warehouse: `file:/opt/data/warehouse`
* Users can drop CSV, Parquet, or JSON under `./data/` on the host and access them via `file:/opt/data/...`.

## 9) Developer UX

* **Make targets**:
  * `make up` - minimal stack (master, one worker, connect).
  * `make up-dev` - adds dev logging and extra env.
  * `make up-full` - adds history server and second worker overlay.
  * `make down`, `make reset`, `make logs`, `make ps`.
* **Environment knobs** in `.env`:
  * `SPARK_IMAGE`, `HOST_DATA_DIR`, `IN_DOCKER_DATA`, `WORKER_CORES`, `WORKER_MEMORY`, port variables.

## 10) Client Requirements (Spark Connect)

* Python: `pyspark==4.0.x` on the client machine.
* Set `SPARK_REMOTE=sc://localhost:<CONNECT_GRPC_PORT>` (default `15002`).
* Example read: `spark.read.option("header", True).csv("file:/opt/data/samples/people.csv")`.
* Example table use:
  * `CREATE DATABASE IF NOT EXISTS demo;`
  * `CREATE TABLE demo.people USING parquet AS SELECT ...;`

## 11) Security (scope for later overlays)

* Base stack is **dev-friendly** (no TLS, no auth).
* Future overlay (for example `compose.tls.yml`): TLS termination in front of Connect gRPC (Caddy or Envoy), optional basic auth or mTLS.
* Keep secrets out of Git; encourage `.env.local` for private overrides.

## 12) Observability (optional now)

* History Server enabled by overlay to visualize event logs.
* Future: add Prometheus or JMX and Grafana overlays if needed.

## 13) Acceptance Criteria (smoke test)

1. `make up` completes with 3 services healthy: master, worker, connect.
2. Master UI reachable at `http://localhost:${MASTER_UI_PORT}`.
3. From a client:
   * `SPARK_REMOTE=sc://localhost:${CONNECT_GRPC_PORT}` -> `SparkSession.builder.getOrCreate()`.
   * Read a file under `./data/samples/` via `file:/opt/data/samples/...`.
   * Create a table in `demo` DB; verify data persisted under `./data/warehouse/...`.
4. (If history overlay enabled) History UI shows the above job.

## 14) Non-Goals

* No Kubernetes or YARN; this is strictly **Spark Standalone** for local or dev usage.
* No external object store or metastore by default; everything is local file-based.

---

### Example: minimal Compose (latest spec style - no `version` key)

```yaml
# compose.spark.yml (excerpt)
services:
  spark-master:
    image: ${SPARK_IMAGE}
    environment:
      SPARK_NO_DAEMONIZE: "true"
      SPARK_LOG_JSON: "true"
      SPARK_MODE: master
      SPARK_EVENTLOG_ENABLED: "true"
      SPARK_EVENTLOG_DIR: "file:/opt/spark/events"
    ports:
      - "${MASTER_UI_PORT}:8080"
      - "7077:7077"
    volumes:
      - ${EVENTS_VOLUME}:/opt/spark/events
      - ./spark/conf:/opt/bitnami/spark/conf:ro
      - ${HOST_DATA_DIR}:${IN_DOCKER_DATA}
    networks: [spark-net]
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://localhost:8080 || exit 1"]

  spark-worker:
    image: ${SPARK_IMAGE}
    depends_on:
      spark-master:
        condition: service_healthy
    environment:
      SPARK_NO_DAEMONIZE: "true"
      SPARK_LOG_JSON: "true"
      SPARK_MODE: worker
      SPARK_MASTER_URL: spark://spark-master:7077
      SPARK_WORKER_CORES: "${WORKER_CORES}"
      SPARK_WORKER_MEMORY: "${WORKER_MEMORY}"
    ports:
      - "${WORKER_UI_PORT}:8081"
    volumes:
      - ./spark/conf:/opt/bitnami/spark/conf:ro
      - ${HOST_DATA_DIR}:${IN_DOCKER_DATA}
    networks: [spark-net]

  spark-connect:
    image: ${SPARK_IMAGE}
    depends_on:
      spark-master:
        condition: service_healthy
    command:
      [
        "/opt/bitnami/spark/sbin/start-connect-server.sh",
        "--master","spark://spark-master:7077",
        "--conf","spark.ui.enabled=true",
        "--conf","spark.sql.warehouse.dir=file:${IN_DOCKER_DATA}/warehouse",
        "--conf","spark.sql.catalogImplementation=in-memory"
      ]
    environment:
      SPARK_NO_DAEMONIZE: "true"
      SPARK_LOG_JSON: "true"
    ports:
      - "${CONNECT_GRPC_PORT}:15002"
      - "${CONNECT_UI_PORT}:4040"
    volumes:
      - ./spark/conf:/opt/bitnami/spark/conf:ro
      - ${HOST_DATA_DIR}:${IN_DOCKER_DATA}
    networks: [spark-net]

networks:
  spark-net:

volumes:
  ${EVENTS_VOLUME}:
```
