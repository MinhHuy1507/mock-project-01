from datetime import datetime

import boto3
import yaml
from commons import logger
import snowflake.connector

logging = logger.get_logger(__name__)
s3 = boto3.client("s3")


def load_config_local(config_path: str):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# snowflake
def get_object(bucket: str, key: str):
    return s3.get_object(Bucket=bucket, Key=key)


def load_config(bucket: str, table: str):
    key = f"config/{table}.yaml"
    obj = get_object(bucket, key)
    return yaml.safe_load(obj["Body"].read())


def get_header(bucket: str, key: str):
    s3 = boto3.client("s3")

    response = s3.list_objects_v2(Bucket=bucket, Prefix=key)

    target_key = None

    if "Contents" in response:
        for obj in response["Contents"]:
            obj_key = obj["Key"]
            if obj_key.endswith(".csv") and not obj_key.endswith(".crc"):
                target_key = obj_key
                break

    if not target_key:
        raise FileNotFoundError(f"File not found in s3://{bucket}/{key}")

    obj = get_object(bucket, target_key)
    header_line = next(obj["Body"].iter_lines()).decode("utf-8")
    obj["Body"].close()

    return header_line.split(",")


def refresh_external_table(schema_name, ext_name, process_date):
    sql_text = (
        f"ALTER EXTERNAL TABLE {schema_name}.{ext_name} REFRESH '{process_date}';"
    )
    return sql_text


def create_process_view(schema_name, table_name, process_date, view_name):
    try:
        partition_date = datetime.strptime(process_date, "%Y/%m/%d")
    except ValueError as exc:
        raise ValueError("process_date must use YYYY/MM/DD format") from exc

    return f"""
    CREATE OR REPLACE VIEW {schema_name}.{view_name} AS
    SELECT *
    FROM {schema_name}.{table_name}
    WHERE LOWER(TRIM(id::STRING)) != 'id'
      AND year = '{partition_date:%Y}'
      AND month = '{partition_date:%m}'
      AND day = '{partition_date:%d}'
    """


def write_file(stage, schema_name, table_name, process_date, view_name, file_format):
    format_map = {
        "csv": "csv_ff",
        "parquet": "parquet_ff",
    }
    file_name = f"{table_name}.{file_format}"

    sql = f"""
    COPY INTO @{stage}/{schema_name}/{table_name}/{process_date}/{file_name}
    FROM (
        SELECT * FROM {schema_name}.{view_name}
    )
    FILE_FORMAT = {schema_name}.{format_map.get(file_format)}
    SINGLE = TRUE
    OVERWRITE = TRUE
    """

    return sql


def get_conn(user, password, account, warehouse, database, schema):
    return snowflake.connector.connect(
        user=user,
        password=password,
        account=account,
        warehouse=warehouse,
        database=database,
        schema=schema,
    )
