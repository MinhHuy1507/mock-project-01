import argparse
from datetime import datetime

from commons import validations, transformations, utils, logger
from commons.configs import CONFIGS, global_config
from pyspark.sql import SparkSession

logging = logger.get_logger(__name__)


def rcv_to_l0(table, bucket, process_date, spark):
    logging.info(f"Start processing table {table} from rcv/ to l0/")
    config = CONFIGS[table]
    path_rcv = (
        global_config["path"]["rcv"] + config["prefix"] + process_date + f"/{table}.csv"
    )
    path_l0 = (
        global_config["path"]["l0"] + config["prefix"] + process_date + f"/{table}.csv"
    )

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

    logging.info(f"After processing")
    logging.info(context["df"])

    utils.write_file(context["df"], path_l0, config["l0_format"])
    logging.info(f"\nCompleted process from rcv to l0, table {table}")


def l0_to_l1(table, process_date, spark):
    logging.info(f"Start processing table {table} from l0/ to l1/")
    config = CONFIGS[table]
    path_l0 = (
        global_config["path"]["l0"] + config["prefix"] + process_date + f"/{table}.csv"
    )
    path_l1 = (
        global_config["path"]["l1"]
        + config["prefix"]
        + process_date
        + f"/{table}.parquet"
    )
    path_audit = (
        global_config["path"]["error_records"]
        + config["prefix"]
        + process_date
        + f"/error_{table}.csv"
    )

    context = {"df": None, "layer": "l0_to_l1", "config": config, "spark": spark}

    context["df"] = utils.load_df(spark, path_l0, config["l0_format"])

    logging.info(f"Validating table {table}")
    valid_records, error_records = validations.validate_l0_to_l1(context["df"], config)

    logging.info(f"Transforming table {table}")
    context["df"] = valid_records
    valid_records = transformations.transform(context)

    logging.info(f"After processing")
    logging.info("=== Error records")
    logging.info(error_records.show(5, truncate=False))
    logging.info("=== Valid records")
    logging.info(valid_records.show(5, truncate=False))

    utils.write_file(valid_records, path_l1, config["l1_format"])
    if not error_records.isEmpty():
        utils.write_file(error_records, path_audit, config["audit_format"])
    logging.info(f"\nCompleted process from l0 to l1, table {table}")


def glue(event):
    # job_id = event.get("job_id")
    # execution_id = event.get("execution_id")
    table_name = event.get("table")
    process_date = event.get("process_date")
    # stage_name = event.get("stage_name")

    start_time = datetime.now().isoformat()
    status = "RUNNING"
    error_message = None

    items = {
        # "job_id": job_id,
        # "execution_id": execution_id,
        "table_name": table_name,
        "process_date": process_date,
        # "stage_name": stage_name,
        "start_time": start_time,
        "end_time": None,
        "status": status,
        "error_message": error_message,
    }

    logging.info(items)
    # audit_table.put_item(Item={...})

    spark = SparkSession.builder.appName("SparkJob").getOrCreate()

    try:
        rcv_to_l0(table_name, process_date, spark)
        l0_to_l1(table_name, process_date, spark)

        status = "SUCCESS"
        end_time = datetime.now().isoformat()

    except Exception as e:
        status = "FAILED"
        end_time = datetime.now().isoformat()
        error_message = str(e)
        logging.error("Error")
        raise e

    finally:
        items["status"] = status
        items["end_time"] = end_time
        items["error_message"] = error_message
        logging.info(items)
        # audit_table.update_item(...)
        pass


def parse_args():
    parser = argparse.ArgumentParser(description="Run the data transformation pipeline")
    parser.add_argument(
        "--table",
        nargs="?",
        default="customers",
        help="Table to transform (customers, products, orders, province)",
    )
    parser.add_argument(
        "--date-path",
        default=datetime.now().strftime("%Y/%m/%d"),
        help="Date partition to process (default: current date)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    mock_event = {"table": args.table, "process_date": args.process_date}

    glue(mock_event)
