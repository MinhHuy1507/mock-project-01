from datetime import datetime
from pyspark.sql import functions as F
import numpy as np


def transform(context):
    df = context["df"]
    layer = context["layer"]
    config = context["config"]

    if df.isEmpty():
        return df

    transformations = config[layer]["transformation"]
    for transform_name, transform_rules in transformations.items():
        function = TRANSFORM_FUNCTIONS[transform_name]
        context["df"] = function(context, transform_rules)

    return context["df"]


# rcv_to_l0
def add_columns(context, transform_rules):
    df = context["df"]
    path = context["file_path"]

    COLUMNS = {"process_date": F.current_timestamp(), "source_file": F.lit(path)}
    new_columns = dict()
    for column in transform_rules:
        new_columns[column["name"]] = COLUMNS[column["name"]]

    df = df.withColumns(new_columns)

    return df


# l0_to_l1
## customers
def split_customers_address(context, transform_rules):
    df = context["df"]

    for rule in transform_rules:
        source = rule["from"]
        address_col, province_col = rule["to"]
        cleaned = F.trim(F.regexp_replace(F.col(source), r"(^,+)|(,+$)", ""))
        parts = F.split(cleaned, ",")
        df = df.withColumn(province_col, F.trim(F.element_at(parts, -1))).withColumn(
            address_col, F.trim(F.regexp_replace(cleaned, r",\s*[^,]+$", ""))
        )

    return df


def split_customers_name(context, transform_rules):
    df = context["df"]

    for rule in transform_rules:
        source = rule["from"]
        first_col, last_col = rule["to"]

        parts = F.split(F.trim(F.col(source)), r"\s+")

        df = df.withColumn(last_col, F.element_at(parts, -1)).withColumn(
            first_col, F.regexp_replace(F.col(source), r"\s+\S+$", "")
        )

    return df


def rename_columns(context, transform_rules):
    df = context["df"]

    mapping = {}
    for rule in transform_rules:
        mapping[rule["from"]] = rule["to"]

    df = df.withColumnsRenamed(mapping)
    return df


def filter_columns(context, transform_rules):
    df = context["df"]

    for rule in transform_rules:
        output_columns = rule["output"]

    df = df.select(output_columns)
    return df


TRANSFORM_FUNCTIONS = {
    "add_column": add_columns,
    "split_name": split_customers_name,
    "split_address": split_customers_address,
    "rename": rename_columns,
    "filter_columns": filter_columns,
}
