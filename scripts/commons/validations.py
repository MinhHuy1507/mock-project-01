import os
import pandas as pd


class ValidationError(Exception):
    pass


# RCV to L0
# Validate file exists, file format, file readable, file not empty
def validate_file(context):
    file_path = context["file_path"]
    config = context.get("config", {})
    suffix = config.get("suffix")

    if not os.path.exists(file_path):
        raise ValidationError(f"File not found: {file_path}")
    if suffix and not file_path.endswith(suffix):
        raise ValidationError(
            f"Invalid file format {file_path}. Expected file format {suffix}"
        )
    try:
        context["df"] = pd.read_csv(file_path)
        if context["df"].empty:
            raise ValidationError(f"File empty: {file_path}")
    except Exception as e:
        raise ValidationError(f"File is not readable: {str(e)}")


def validate_schema(context):
    df = context["df"]
    config = context["config"]

    df_columns = df.columns.tolist()
    schema_columns = [column["name"] for column in config["columns"]]
    missing_columns = set(schema_columns) - set(df_columns)
    extra_columns = set(df_columns) - set(schema_columns)

    if missing_columns or extra_columns:
        message = []
        if missing_columns:
            message.append(f"Missing columns: {list(missing_columns)}")
        if extra_columns:
            message.append(f"Unexpected columns: {list(extra_columns)}")
        raise ValidationError("Schema drift detected. " + "; ".join(message))


def validate_rcv_to_l0(context):
    config = context["config"]
    for function, required in config["rcv_to_l0"]["validation"].items():
        if required:
            function_map = VALIDATE_FUNCTIONS[function]
            function_map(context)


# L0 to L1
def validate_not_null(df, column):
    if isinstance(column, list):
        mask = df[column].notna().all(axis=1)
    else:
        mask = df[column].notna()
    return mask


def validate_unique(df, column):
    mask = ~df[column].duplicated()
    return mask


def validate_format(df, column, format):
    python_format = format.replace("yyyy", "%Y").replace("MM", "%m").replace("dd", "%d")
    parsed = pd.to_datetime(df[column], format=python_format, errors="coerce")
    mask = parsed.notna()
    return mask


def validate_range(df, column, min, max):
    mask = (df[column] >= min) & (df[column] <= max)
    return mask


def validate_datatype(df, column, col_type):
    s = df[column]
    if col_type == "string":
        return s.apply(lambda x: isinstance(x, str)) | s.isna()
    elif col_type in ["decimal", "int"]:
        return pd.to_numeric(s, errors="coerce").notna() | s.isna()
    elif col_type in ["date", "datetime"]:
        return pd.to_datetime(s, errors="coerce").notna() | s.isna()
    else:
        raise ValueError(f"Unsupported type: {col_type}")


# Add new row error, for audit (error_records)
def _add_row_error(error_rows, df, idx, rule, params):
    column = params.get("column", "")
    if isinstance(column, list):
        error_columns = column
    elif column:
        error_columns = [column]
    else:
        error_columns = []

    error_message = f"{rule}({','.join(error_columns)})"
    record = error_rows.get(idx)
    if record is None:
        record = {
            "_source_index": idx,
            **df.loc[idx].to_dict(),
            "error_type": "validation",
            "error_rule": set(),
            "error_column": set(),
            "error_message": set(),
        }
        error_rows[idx] = record

    record["error_rule"].add(rule)
    record["error_message"].add(error_message)
    for col in error_columns:
        record["error_column"].add(col)


def validate_l0_to_l1(df, config):
    error_rows = {}

    # Validate datatype
    for col in config["columns"]:
        col_name = col["name"]
        col_type = col["type"]

        if col_name and col_type and col_name in df.columns:
            mask = validate_datatype(df, col_name, col_type)
            failed_idx = df.index[~mask]
            params = {"column": col_name, "type": col_type}
            for idx in failed_idx:
                _add_row_error(error_rows, df, idx, "datatype", params)

    # Validate rules (not null, unique, range, format)
    for validation in config["l0_to_l1"]["validation"]:
        rule = validation["rule"]
        function = VALIDATE_FUNCTIONS[rule]
        params = {k: v for k, v in validation.items() if k != "rule"}
        columns = params.get("column", [])

        if isinstance(columns, list) and rule != "unique":
            for col in columns:
                single_col_params = params.copy()
                single_col_params["column"] = col
                mask = function(df, **single_col_params)

                if rule != "not_null":
                    mask = mask | df[col].isna()

                failed_idx = df.index[~mask]
                for idx in failed_idx:
                    _add_row_error(error_rows, df, idx, rule, single_col_params)
        else:
            mask = function(df, **params)
            failed_idx = df.index[~mask]
            for idx in failed_idx:
                _add_row_error(error_rows, df, idx, rule, params)

    error_records = pd.DataFrame(
        [
            {
                **record,
                "error_rule": "; ".join(record["error_rule"]),
                "error_column": "; ".join(record["error_column"]),
                "error_message": "; ".join(record["error_message"]),
            }
            for record in error_rows.values()
        ]
    )

    if not error_records.empty:
        valid_df = df.drop(index=error_records["_source_index"].unique()).copy()
    else:
        valid_df = df.copy()
    return valid_df, error_records


VALIDATE_FUNCTIONS = {
    "validate_file": validate_file,
    "validate_schema": validate_schema,
    "not_null": validate_not_null,
    "unique": validate_unique,
    "format": validate_format,
    "range": validate_range,
}
