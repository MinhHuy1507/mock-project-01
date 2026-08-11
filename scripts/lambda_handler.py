import argparse
from datetime import datetime

from configs import (
    customers_config,
    products_config,
    orders_config,
    province_config,
    global_config,
)
from commons import validations, transformations, utils

CONFIGS = {
    "customers": customers_config,
    "products": products_config,
    "orders": orders_config,
    "province": province_config,
}


def rcv_to_l0(table, date_path):
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

    validations.validate_rcv_to_l0(context)
    context["df"] = transformations.transform(context)

    utils.write_csv(context["df"], path_l0)


def l0_to_l1(table, date_path):
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

    valid_records, error_records = validations.validate_l0_to_l1(context["df"], config)
    valid_records = transformations.transform(context)

    print("=== Error records")
    print(error_records)
    print("=== Valid records")
    print(valid_records)

    utils.write_parquet(valid_records, path_l1)
    if not error_records.empty:
        utils.write_csv(error_records, path_audit)


def lambda_handler(event, context):
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

    lambda_handler(mock_event, mock_context)
