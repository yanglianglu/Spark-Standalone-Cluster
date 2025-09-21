import os
import sys

from pyspark.sql import SparkSession


def main() -> int:
    data_root = os.environ.get("IN_DOCKER_DATA", "/opt/data")
    connect_port = os.environ.get("CONNECT_GRPC_PORT", "15002")
    connect_uri = os.environ.get("SPARK_REMOTE", f"sc://localhost:{connect_port}")
    sample_path = os.environ.get("SPARK_SAMPLE_DATA", f"file:{data_root}/samples/people.csv")
    warehouse_path = f"file:{data_root}/warehouse"

    print(f"Connecting to Spark Connect at {connect_uri}...")
    spark = SparkSession.builder.remote(connect_uri).config(
        "spark.sql.warehouse.dir", warehouse_path
    ).getOrCreate()

    try:
        print(f"Reading sample dataset from {sample_path}...")
        df = spark.read.option("header", True).csv(sample_path)
        row_count = df.count()
        if row_count == 0:
            raise RuntimeError("Sample dataset is empty")
        print(f"Loaded dataset with {row_count} records.")

        print("Ensuring demo database exists...")
        spark.sql("CREATE DATABASE IF NOT EXISTS demo")

        print("Creating demo.people table...")
        spark.sql("DROP TABLE IF EXISTS demo.people")
        df.write.mode("overwrite").saveAsTable("demo.people")

        stored_count = spark.table("demo.people").count()
        if stored_count != row_count:
            raise RuntimeError(
                f"Unexpected row count in demo.people (expected {row_count}, found {stored_count})"
            )
        print("Smoke test completed successfully.")
        return 0
    finally:
        spark.stop()


if __name__ == "__main__":
    sys.exit(main())
