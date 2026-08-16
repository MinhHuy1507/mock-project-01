import pandas as pd
import os
import yaml
import boto3

# import boto3


def make_dirs(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def read_csv(path):
    return pd.read_csv(path)


def read_parquet(path):
    try:
        return pd.read_parquet(path)
    except Exception as e:
        raise str(e)


def write_csv(df, path):
    make_dirs(path)
    df.to_csv(path, index=False, header=True)


def write_parquet(df, path):
    make_dirs(path)
    df.to_parquet(path, index=False, engine="pyarrow")


def load_config(config_path: str):
    # if str(config_path).startswith("s3://"):
    #     path_parts = str(config_path).replace("s3://", "").split("/", 1)
    #     bucket_name, key = path_parts[0], path_parts[1]

    #     s3 = boto3.client("s3")
    #     obj = s3.get_object(Bucket=bucket_name, Key=key)
    #     return yaml.safe_load(obj["Body"].read())

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
