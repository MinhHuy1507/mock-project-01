import os
import pandas as pd
from commons.utils import load_df
from pyspark.sql import functions as F
from pyspark.sql.window import Window


class ValidationError(Exception):
    pass


# RCV to L0
# Validate file exists, file format, file readable, file not empty
def validate_file(context):
    file_path = context["file_path"]
    spark = context["spark"]

    df = load_df(spark, file_path, context["config"]["rcv_format"])
    if df.isEmpty():
        raise ValidationError(f"File empty: {file_path}")

    context["df"] = df


def validate_schema(context):
    df = context["df"]
    config = context["config"]

    actual = df.columns
    expected = [col["name"] for col in config["columns"]]

    if actual != expected:
        raise ValidationError(f"Schema mismatch. Expected {expected}, got {actual}")


def validate_rcv_to_l0(context):
    config = context["config"]
    for function, required in config["rcv_to_l0"]["validation"].items():
        if required:
            function_map = VALIDATE_FUNCTIONS[function]
            function_map(context)


# L0 to L1
def validate_not_null(df, column):
    mask = df[column].isNull()
    return F.when(mask, f"not_null({column})")


def validate_unique(df, columns):
    if not isinstance(columns, list):
        columns = [columns]

    temp_col = f"__err_unique_{'_'.join(columns)}"

    null_condition = F.lit(False)
    for col in columns:
        null_condition = null_condition | F.col(col).isNull()

    df_null = df.filter(null_condition)
    df_non_null = df.filter(~null_condition)

    window_spec = Window.partitionBy(*columns)
    duplicate_condition = F.count("*").over(window_spec) > 1

    df_non_null = df_non_null.withColumn(
        temp_col, F.when(duplicate_condition, f"unique({','.join(columns)})")
    )

    df_null = df_null.withColumn(temp_col, F.lit(None).cast("string"))

    result_df = df_non_null.unionByName(df_null)

    return result_df, temp_col


def validate_format(df, column, format):
    safe_col = F.expr(f"try_to_timestamp({column}, '{format}')")
    mask = safe_col.isNotNull() | df[column].isNull()
    return F.when(~mask, f"format({column})")


def validate_range(df, column, min, max):
    safe_col = F.expr(f"try_cast({column} as double)")
    mask = ((safe_col >= min) & (safe_col <= max)) | df[column].isNull()
    return F.when(~mask, f"range({column})")


def validate_datatype(df, column, col_type):
    mapping_type = {
        "string": df[column].cast("string").isNotNull(),
        "int": F.expr(f"try_cast({column} as bigint)").isNotNull(),
        "decimal": F.expr(f"try_cast({column} as double)").isNotNull(),
        "date": F.expr(f"try_cast({column} as date)").isNotNull(),
        "datetime": F.expr(f"try_cast({column} as timestamp)").isNotNull(),
    }
    if col_type in mapping_type:
        mask = mapping_type[col_type]
    else:
        raise ValueError(f"Unsupported type: {col_type}")
    return F.when(~mask, f"datatype({column})")


def validate_l0_to_l1(df, config):
    error_exprs = []
    temp_unique_cols = []

    # Rule datatype
    for col in config["columns"]:
        col_name = col["name"]
        col_type = col["type"]
        if col_name and col_type and col_name in df.columns:
            error_exprs.append(validate_datatype(df, col_name, col_type))

    # Orther rules (unique, not_null, format, range)
    for validation in config["l0_to_l1"]["validation"]:
        rule = validation["rule"]
        function = VALIDATE_FUNCTIONS[rule]
        params = {k: v for k, v in validation.items() if k != "rule"}
        columns = params.get("column", [])

        if rule == "unique":
            df, temp_col_name = function(df, columns)
            error_exprs.append(F.col(temp_col_name))
            temp_unique_cols.append(temp_col_name)
        else:
            if isinstance(columns, list):
                for col in columns:
                    single_col_params = params.copy()
                    single_col_params["column"] = col
                    error_exprs.append(function(df, **single_col_params))
            else:
                error_exprs.append(function(df, **params))

    df = df.withColumn(
        "__errors", F.filter(F.array(*error_exprs), lambda x: x.isNotNull())
    )

    df = df.persist()
    valid_df = df.filter(F.size("__errors") == 0)
    error_records = df.filter(F.size("__errors") > 0)
    error_records = (
        error_records.withColumn("error_type", F.lit("validation"))
        .withColumn("error_message", F.array_join("__errors", "; "))
        .withColumn(
            "error_rule",
            F.expr(
                "array_join(transform(__errors, x -> substring_index(x, '(', 1)), '; ')"
            ),
        )
        .withColumn(
            "error_column",
            F.expr(
                "array_join(transform(__errors, x -> replace(substring_index(x, '(', -1), ')', '')), '; ')"
            ),
        )
    )

    # Drop temporary columns used for validation
    cols_to_drop = temp_unique_cols + ["__errors"]
    valid_df = valid_df.drop(*cols_to_drop)
    error_records = error_records.drop(*cols_to_drop)

    return valid_df, error_records, df


VALIDATE_FUNCTIONS = {
    "validate_file": validate_file,
    "validate_schema": validate_schema,
    "not_null": validate_not_null,
    "unique": validate_unique,
    "format": validate_format,
    "range": validate_range,
}
