import pandas as pd
import os
import yaml


def read_csv(path):
    return pd.read_csv(path)


def write_csv(df, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False, header=True)


def write_parquet(df, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_parquet(path, index=False, engine="pyarrow")


def load_config(config_file):
    with open(config_file, "r") as file:
        return yaml.safe_load(file)
