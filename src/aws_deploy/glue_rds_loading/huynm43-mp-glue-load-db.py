import sys
from datetime import datetime
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

from commons import utils, logger
from commons.load_database import LOAD_STRATEGIES, CREATE_TABLES

logging = logger.get_logger(__name__)


def l1_to_database(bucket, table, schema, process_date, spark, db_config):
    logging.info(f"Start processing table {table} from l1/ to database")
    config = utils.load_config(bucket, table)
    key_l1 = (
        config.get("l1_layer")
        + f"/{schema}"
        + f"/{table}/"
        + process_date
        + f"/{table}.{config.get('l1_format')}"
    )
    path_l1 = f"s3://{bucket}/{key_l1}"

    logging.info(f"Loading data from {path_l1} using Spark")
    df = spark.read.parquet(path_l1)

    load_config = config["load_database"]["load_strategy"]
    load_functions = LOAD_STRATEGIES[load_config]
    create_table_functions = CREATE_TABLES[table]

    create_table_functions(db_config)
    load_functions(df, config, db_config)

    logging.info(f"\nCompleted loading into database, table {table}")


def main():
    args = getResolvedOptions(
        sys.argv,
        [
            "JOB_NAME",
            "bucket",
            "schema",
            "table",
            "process_date",
            "pg_username",
            "pg_password_s3_key",
            "pg_host",
            "pg_port",
            "pg_database",
        ],
    )

    bucket_name = args["bucket"]
    schema_name = args["schema"]
    table_name = args["table"]
    process_date = args["process_date"]
    pg_password_s3_key = args["pg_password_s3_key"]

    pg_password = utils.get_object(bucket_name, pg_password_s3_key)["Body"].read().decode("utf-8").strip()

    db_config = {
        "user": args["pg_username"],
        "password": pg_password,
        "host": args["pg_host"],
        "port": args["pg_port"],
        "database": args["pg_database"],
    }

    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    job = Job(glueContext)
    job.init(args["JOB_NAME"], args)

    start_time = datetime.now().isoformat()
    status = "RUNNING"
    error_message = None

    items = {
        "bucket_name": bucket_name,
        "table_name": table_name,
        "process_date": process_date,
        "status": status,
        "start_time": start_time,
        "end_time": None,
        "error_message": error_message,
    }

    logging.info(items)

    try:
        stage_name = "load_database"
        l1_to_database(bucket_name, table_name, schema_name, process_date, spark, db_config)

        status = "SUCCESS"
        end_time = datetime.now().isoformat()
        logging.info("Completed Processing")

    except Exception as e:
        status = "FAILED"
        end_time = datetime.now().isoformat()
        error_message = f"FAILED_AT_[{stage_name}]: {str(e)}"
        logging.error(error_message)
        raise Exception(error_message)

    finally:
        items["status"] = status
        items["end_time"] = end_time
        items["error_message"] = error_message
        logging.info(items)
        job.commit()


if __name__ == "__main__":
    main()
