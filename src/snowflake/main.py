import argparse

from commons import validations, transformations, utils, logger
from commons.configs import (
    sf_user,
    sf_password,
    sf_account,
    sf_warehouse,
    sf_database,
    sf_schema,
)

logging = logger.get_logger(__name__)


def l0_to_l1(schema, table, bucket, process_date, sf_conn):
    logging.info(f"Start processing table {table} from l0/ to l1/")
    config = utils.load_config(bucket, table)

    key_l0 = (
        config.get("l0_layer")
        + f"/{schema}/{table}/"
        + process_date
        + f"/{table}.{config.get('l0_format')}"
    )

    stage_l1 = config["stage_l1"]
    stage_audit = config["stage_audit"]

    view_table = f"vw_{table}"
    view_validation = f"vw_validation_{table}"
    view_validation_valid = f"vw_validation_valid_{table}"
    view_validation_invalid = f"vw_validation_invalid_{table}"
    view_transformation = f"vw_transformation_{table}"
    columns = utils.get_header(bucket, key_l0)

    logging.info(f"Refreshing external table for {table}")
    refresh_ext_sql = utils.refresh_external_table(schema, table, process_date)
    logging.info(refresh_ext_sql)
    sf_conn.cursor().execute(refresh_ext_sql)

    logging.info(f"Scoping input view to partition {process_date}")
    process_view_sql = utils.create_process_view(
        schema, table, process_date, view_table
    )
    logging.info(process_view_sql)
    sf_conn.cursor().execute(process_view_sql)

    logging.info(f"Validating table {table}")
    sql_validate = validations.validate_l0_to_l1(
        config, schema, view_table, view_validation
    )
    logging.info(sql_validate)
    sf_conn.cursor().execute(sql_validate)

    logging.info(f"Filtering valid records for {table}")
    sql_filter_valid = validations.get_view_validation(
        schema, view_validation, view_validation_valid, isvalid=True
    )
    logging.info(sql_filter_valid)
    sf_conn.cursor().execute(sql_filter_valid)

    logging.info(f"Filtering invalid records for {table}")
    sql_filter_invalid = validations.get_view_validation(
        schema, view_validation, view_validation_invalid, isvalid=False
    )
    logging.info(sql_filter_invalid)
    sf_conn.cursor().execute(sql_filter_invalid)

    logging.info(f"Transforming table {table}")
    sql_transform = transformations.transform_l0_to_l1(
        config, schema, view_validation_valid, view_transformation, columns
    )
    logging.info(sql_transform)
    sf_conn.cursor().execute(sql_transform)

    logging.info(f"Writing valid records to l1/{schema}/{table}/{process_date}/")
    write_l1_sql = utils.write_file(
        stage_l1,
        schema,
        table,
        process_date,
        view_transformation,
        config["l1_format"],
    )
    logging.info(write_l1_sql)
    sf_conn.cursor().execute(write_l1_sql)

    logging.info(f"Writing invalid records to audit/{schema}/{table}/{process_date}/")
    write_audit_sql = utils.write_file(
        stage_audit,
        schema,
        table,
        process_date,
        view_validation_invalid,
        config["audit_format"],
    )
    logging.info(write_audit_sql)
    sf_conn.cursor().execute(write_audit_sql)

    logging.info(f"\nCompleted process from l0 to l1, table {table}")


def lambda_handler(event, context):
    bucket = event.get("bucket")
    schema_name = event.get("schema")
    table_name = event.get("table")
    process_date = event.get("process_date")

    try:
        conn = utils.get_conn(
            user=sf_user,
            password=sf_password,
            account=sf_account,
            warehouse=sf_warehouse,
            database=sf_database,
            schema=sf_schema,
        )
        l0_to_l1(schema_name, table_name, bucket, process_date, conn)
    except Exception as e:
        logging.error(str(e))
        raise e
    finally:
        if conn:
            conn.close()
            logging.info("Snowflake connection closed.")


def parse_args():
    parser = argparse.ArgumentParser(description="Run Snowflake l0 to l1 processing")
    parser.add_argument(
        "--bucket",
        default="huynm43-mock-project-s3-414061810527-us-east-1-an",
        help="S3 bucket name",
    )
    parser.add_argument(
        "--schema",
        default="retail",
        help="Snowflake schema name",
    )
    parser.add_argument(
        "--table",
        default="customers",
        help="Table name",
    )
    parser.add_argument(
        "--process-date",
        default="2026/08/28",
        help="Processing partition date in YYYY/MM/DD format",
    )
    return parser.parse_args()


# test
if __name__ == "__main__":
    args = parse_args()
    event = {
        "bucket": args.bucket,
        "schema": args.schema,
        "table": args.table,
        "process_date": args.process_date,
    }
    context = {}
    lambda_handler(event, context)
