from datetime import datetime
from pyspark.sql import functions as F


def transform(context):
    df = context["df"]
    layer = context["layer"]
    config = context["config"]

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
        col_name = column["name"]
        if col_name in COLUMNS:
            new_columns[col_name] = COLUMNS[col_name]
        else:
            raise ValueError(f"Unknown column name: {col_name}")

    if new_columns:
        df = df.withColumns(new_columns)

    return df


# l0_to_l1
## customers
def split_customers_address(context, transform_rules):
    df = context["df"]
    new_columns = {}

    for rule in transform_rules:
        source = rule["from"]
        address_col, province_col = rule["to"]

        cleaned = F.trim(F.regexp_replace(F.col(source), r"(^,+)|(,+$)", ""))
        parts = F.split(cleaned, ",")

        new_columns[province_col] = F.trim(F.element_at(parts, -1))
        new_columns[address_col] = F.trim(F.regexp_replace(cleaned, r",\s*[^,]+$", ""))

    return df.withColumns(new_columns)


def split_customers_name(context, transform_rules):
    df = context["df"]
    new_columns = {}

    for rule in transform_rules:
        source = rule["from"]
        first_col, last_col = rule["to"]

        parts = F.split(F.trim(F.col(source)), r"\s+")
        new_columns[last_col] = F.element_at(parts, -1)
        new_columns[first_col] = F.array_join(F.slice(parts, 1, F.size(parts) - 1), " ")

    return df.withColumns(new_columns)


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
