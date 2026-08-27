import sys
from datetime import datetime
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

from commons import validations, transformations, utils, logger

logging = logger.get_logger(__name__)


def rcv_to_l0(schema, table, bucket, process_date, spark):
    logging.info(f"Start processing table {table} from rcv/ to l0/")
    config = utils.load_config(bucket, table)
    key_rcv = (
        config.get("rcv_layer")
        + f"/{schema}/{table}/"
        + process_date
        + f"/{table}.{config.get('rcv_format')}"
    )
    path_rcv = f"s3://{bucket}/{key_rcv}"
    key_l0 = (
        config.get("l0_layer")
        + f"/{schema}/{table}/"
        + process_date
        + f"/{table}.{config.get('l0_format')}"
    )
    path_l0 = f"s3://{bucket}/{key_l0}"

    context = {
        "df": None,
        "file_path": path_rcv,
        "layer": "rcv_to_l0",
        "config": config,
        "spark": spark,
    }

    logging.info(f"Validating table {table} from {context['file_path']}")
    validations.validate_rcv_to_l0(context)
    logging.info(f"Transforming table {table} from {context['file_path']}")
    context["df"] = transformations.transform(context)

    utils.write_file(context["df"], path_l0, config["l0_format"])
    logging.info(f"\nCompleted process from rcv to l0, table {table}")


def l0_to_l1(schema, table, bucket, process_date, spark):
    logging.info(f"Start processing table {table} from l0/ to l1/")
    config = utils.load_config(bucket, table)
    key_l0 = (
        config.get("l0_layer")
        + f"/{schema}/{table}/"
        + process_date
        + f"/{table}.{config.get('l0_format')}"
    )
    path_l0 = f"s3://{bucket}/{key_l0}"
    key_l1 = (
        config.get("l1_layer")
        + f"/{schema}/{table}/"
        + process_date
        + f"/{table}.{config.get('l1_format')}"
    )
    path_l1 = f"s3://{bucket}/{key_l1}"
    key_audit = (
        config.get("audit_layer")
        + f"/{schema}/{table}/"
        + process_date
        + f"/error_{table}.{config.get('audit_format')}"
    )
    path_audit = f"s3://{bucket}/{key_audit}"

    context = {"df": None, "layer": "l0_to_l1", "config": config, "spark": spark}
    context["df"] = utils.load_df(spark, path_l0, config["l0_format"])

    logging.info(f"Validating table {table}")
    valid_records, error_records, df_cached = validations.validate_l0_to_l1(
        context["df"], config
    )

    logging.info(f"Transforming table {table}")
    context["df"] = valid_records
    valid_records = transformations.transform(context)

    utils.write_file(valid_records, path_l1, config["l1_format"])
    if not error_records.isEmpty():
        utils.write_file(error_records, path_audit, config["audit_format"])
    df_cached.unpersist()
    logging.info(f"\nCompleted process from l0 to l1, table {table}")


def main():
    args = getResolvedOptions(sys.argv, ["JOB_NAME", "bucket", "schema", "table", "process_date"])

    bucket = args["bucket"]
    schema_name = args["schema"]
    table_name = args["table"]
    process_date = args["process_date"]

    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    job = Job(glueContext)
    job.init(args["JOB_NAME"], args)

    start_time = datetime.now().isoformat()
    status = "RUNNING"
    error_message = None

    items = {
        "schema_name": schema_name,
        "table_name": table_name,
        "process_date": process_date,
        "start_time": start_time,
        "end_time": None,
        "status": status,
        "error_message": error_message,
    }

    logging.info(items)

    try:
        stage_name = "rcv_to_l0"
        rcv_to_l0(schema_name, table_name, bucket, process_date, spark)

        stage_name = "l0_to_l1"
        l0_to_l1(schema_name, table_name, bucket, process_date, spark)

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
