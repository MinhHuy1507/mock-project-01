import os
import yaml

import boto3

s3 = boto3.client("s3")


def make_dirs(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def load_df(spark, file_path, file_format):
    if file_format == "csv":
        return spark.read.option("header", True).csv(file_path)
    elif file_format == "parquet":
        return spark.read.parquet(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_format}")


def write_file(df, file_path, file_format):
    if file_format == "csv":
        df.write.mode("overwrite").option("header", True).csv(file_path)
    elif file_format == "parquet":
        df.write.mode("overwrite").parquet(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_format}")


def get_object(bucket: str, key: str):
    return s3.get_object(Bucket=bucket, Key=key)


def load_config(bucket: str, table: str):
    key = f"config/{table}.yaml"
    obj = get_object(bucket, key)
    return yaml.safe_load(obj["Body"].read())
