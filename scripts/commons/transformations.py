from datetime import datetime

import pandas as pd


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

        split_series = df[source].apply(
            lambda x: x.split(",", 1) if isinstance(x, str) and x.strip() else None
        )

        first_values = [
            x[0].strip() if isinstance(x, list) and len(x) > 0 else None
            for x in split_series
        ]

        second_values = [
            x[1].strip() if isinstance(x, list) and len(x) > 1 else None
            for x in split_series
        ]

        df[first_col] = pd.Series(first_values, index=df.index, dtype=object)
        df[second_col] = pd.Series(second_values, index=df.index, dtype=object)


def split_customers_name(context, transform_rules):
    df = context["df"]

    for rule in transform_rules:
        source = rule["from"]
        first_col, last_col = rule["to"]

        split_series = df[source].apply(
            lambda x: x.split() if isinstance(x, str) and x.strip() else None
        )
        first_values = [
            x[0] if isinstance(x, list) and len(x) > 0 else None for x in split_series
        ]
        last_values = [
            " ".join(x[1:]) if isinstance(x, list) and len(x) > 1 else None
            for x in split_series
        ]

        df[first_col] = pd.Series(first_values, index=df.index, dtype=object)
        df[last_col] = pd.Series(last_values, index=df.index, dtype=object)


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
