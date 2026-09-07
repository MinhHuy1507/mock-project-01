def split_customers_name(transform_rules, column_expr):
    for rule in transform_rules:
        source_col = rule["from"]
        first_col, second_col = rule["to"]

        cleaned = f"TRIM({source_col})"
        column_expr[first_col] = (
            f"NULLIF(REGEXP_SUBSTR({cleaned}, '[^[:space:]]+$'), '')"
        )
        column_expr[second_col] = (
            f"NULLIF(TRIM(REGEXP_REPLACE({cleaned}, '[^[:space:]]+$', '')), '')"
        )
    return column_expr


def split_customers_address(transform_rules, column_expr):
    for rule in transform_rules:
        source_col = rule["from"]
        first_col, second_col = rule["to"]

        cleaned = f"TRIM(REGEXP_REPLACE({source_col}, '(^,+)|(,+$)', ''))"
        column_expr[first_col] = (
            f"NULLIF(TRIM(REGEXP_REPLACE({cleaned}, ',\\\\s*[^,]+$', '')), '')"
        )
        column_expr[second_col] = f"NULLIF(TRIM(SPLIT_PART({cleaned}, ',', -1)), '')"

    return column_expr


def rename_columns(transform_rules, column_expr):
    for rule in transform_rules:
        source_col = rule["from"]
        target_col = rule["to"]
        column_expr[target_col] = source_col
    return column_expr


def filter_columns(transform_rules, column_expr):
    for rule in transform_rules:
        output_columns = rule["output"]
    filtered_expr = {}
    for col in output_columns:
        if col in column_expr:
            filtered_expr[col] = column_expr[col]

    return filtered_expr


def transform_l0_to_l1(config, schema, view_input, view_output, columns):
    # Casting datatype
    col_metadata = {col["name"]: col for col in config.get("columns", [])}
    for col in (
        config.get("rcv_to_l0", {}).get("transformation", {}).get("add_column", [])
    ):
        col_metadata[col["name"]] = col

    CAST_MAPPING = {
        "string": "{column}",
        "integer": "CAST({column} AS INT)",
        "decimal": "CAST({column} AS DECIMAL(38, 4))",
        "date": "TRY_TO_DATE({column}{format})",
        "datetime": "TRY_TO_TIMESTAMP({column})",
        "timestamp": "TRY_TO_TIMESTAMP({column})",
        "boolean": "CAST({column} AS BOOLEAN)",
    }

    column_expr = {}
    for col in columns:
        meta = col_metadata.get(col, {"type": "string"})
        col_type = meta.get("type", "string").lower()

        sql_template = CAST_MAPPING.get(col_type, "{column}")
        fmt = f", '{meta['format']}'" if "format" in meta else ""

        column_expr[col] = sql_template.format(column=col, format=fmt)

    # Orther rules
    for transform_name, transform_rules in config["l0_to_l1"]["transformation"].items():
        function = TRANSFORM_FUNCTIONS.get(transform_name)
        if function:
            column_expr = function(transform_rules, column_expr)

    # Sql generation
    column_expr_list = [f"{expr} AS {col}" for col, expr in column_expr.items()]
    column_expr_str = ",\n            ".join(column_expr_list)

    transform_sql = f"""
        CREATE OR REPLACE VIEW {schema}.{view_output} AS
        SELECT
            {column_expr_str}
        FROM {schema}.{view_input}
    """

    return transform_sql


TRANSFORM_FUNCTIONS = {
    "split_name": split_customers_name,
    "split_address": split_customers_address,
    "rename": rename_columns,
    "filter_columns": filter_columns,
}
