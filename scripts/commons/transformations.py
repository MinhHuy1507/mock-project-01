from datetime import datetime

import pandas as pd
import numpy as np


def transform(context):
    df = context["df"]
    layer = context["layer"]
    config = context["config"]

    if df.empty:
        return df

    transformations = config[layer]["transformation"]
    for transform_name, transform_rules in transformations.items():
        function = TRANSFORM_FUNCTIONS[transform_name]
        function(context, transform_rules)

    return df


# rcv_to_l0
def add_columns(context, transform_rules):
    df = context["df"]
    path = context["file_path"]

    COLUMNS = {"process_date": datetime.now(), "source_file": path}
    for column in transform_rules:
        df[column["name"]] = COLUMNS[column["name"]]


# l0_to_l1
## customers
def split_customers_address(context, transform_rules):
    df = context["df"]

    for rule in transform_rules:
        source = rule["from"]
        first_col, second_col = rule["to"]

        cleaned_source = df[source].str.strip(" ,").replace("", None)

        splits = cleaned_source.str.rsplit(",", n=1)

        df[first_col] = cleaned_source.replace({np.nan: None})
        df[second_col] = splits.str[1].str.strip().replace({np.nan: None})


def split_customers_name(context, transform_rules):
    df = context["df"]

    for rule in transform_rules:
        source = rule["from"]
        first_col, last_col = rule["to"]

        splits = df[source].str.split(n=1).replace("", None)

        df[first_col] = splits.str[0].replace({np.nan: None})
        df[last_col] = splits.str[1].replace({np.nan: None})


def rename_columns(context, transform_rules):
    df = context["df"]

    mapping = {}
    for rule in transform_rules:
        mapping[rule["from"]] = rule["to"]

    df.rename(columns=mapping, inplace=True)


TRANSFORM_FUNCTIONS = {
    "add_column": add_columns,
    "split_name": split_customers_name,
    "split_address": split_customers_address,
    "rename": rename_columns,
}
