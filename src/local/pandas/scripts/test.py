import argparse
from datetime import datetime

from commons import validations, transformations, utils, logger
from commons.configs import CONFIGS, global_config

logging = logger.get_logger(__name__)


def rcv_to_l0(table, date_path):
    logging.info(f"Start processing table {table} from rcv/ to l0/")
    config = CONFIGS[table]
    path_rcv = (
        global_config["path"]["rcv"] + config["prefix"] + date_path + f"/{table}.csv"
    )
    path_l0 = (
        global_config["path"]["l0"] + config["prefix"] + date_path + f"/{table}.csv"
    )

    context = {
        "df": None,
        "file_path": path_rcv,
        "layer": "rcv_to_l0",
        "config": config,
    }

    logging.info(f"Validating table {table} from {context['file_path']}")
    validations.validate_rcv_to_l0(context)
    logging.info(f"Transforming table {table} from {context['file_path']}")
    context["df"] = transformations.transform(context)

    logging.info(f"After processing")
    logging.info(context["df"])

    utils.write_csv(context["df"], path_l0)
    logging.info(f"\nCompleted process from rcv to l0, table {table}")


def l0_to_l1(table, date_path):
    logging.info(f"Start processing table {table} from l0/ to l1/")
    config = CONFIGS[table]
    path_l0 = (
        global_config["path"]["l0"] + config["prefix"] + date_path + f"/{table}.csv"
    )
    path_l1 = (
        global_config["path"]["l1"] + config["prefix"] + date_path + f"/{table}.parquet"
    )
    path_audit = (
        global_config["path"]["error_records"]
        + config["prefix"]
        + date_path
        + f"/error_{table}.csv"
    )

    context = {
        "df": None,
        "layer": "l0_to_l1",
        "config": config,
    }

    context["df"] = utils.read_csv(path_l0)

    logging.info(f"Validating table {table}")
    valid_records, error_records = validations.validate_l0_to_l1(context["df"], config)

    logging.info(f"Transforming table {table}")
    context["df"] = valid_records
    valid_records = transformations.transform(context)

    logging.info(f"After processing")
    logging.info("=== Error records")
    logging.info(error_records)
    logging.info("=== Valid records")
    logging.info(valid_records)

    utils.write_parquet(valid_records, path_l1)
    if not error_records.empty:
        utils.write_csv(error_records, path_audit)
    logging.info(f"\nCompleted process from l0 to l1, table {table}")


# Để chạy local
def test(event, context):
    table = event.get("table")
    date_path = event.get("date_path")

    if not table or not date_path:
        raise ValueError("Missing 'table' or 'date_path' in event payload")

    print(f"Triggering pipeline for table: {table}, date partition: {date_path}")

    rcv_to_l0(table, date_path)
    l0_to_l1(table, date_path)

    return {
        "statusCode": 200,
        "body": f"Successfully processed {table} for {date_path}",
    }


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
    mock_event = {"table": args.table, "date_path": args.date_path}
    mock_context = {}

    test(mock_event, mock_context)
