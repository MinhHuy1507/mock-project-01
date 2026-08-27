import pandas as pd
import os
import yaml
import boto3

s3 = boto3.client("s3")


def get_object(bucket, key):
    return s3.get_object(Bucket=bucket, Key=key)


def read_parquet(path):
    try:
        return pd.read_parquet(path, engine="pyarrow")
    except Exception as e:
        raise e


def load_config(bucket: str, table: str):
    key = f"config/{table}.yaml"
    obj = get_object(bucket, key)
    return yaml.safe_load(obj["Body"].read())
