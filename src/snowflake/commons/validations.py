def validate_not_null(column):
    if isinstance(column, str):
        column = [column]

    expr = []
    for col in column:
        expr_col = (
            f"CASE WHEN NULLIF(TRIM({col}::STRING), '') IS NULL "
            f"THEN 'not_null({col})' END"
        )
        expr.append(expr_col)
    return expr


def validate_unique(column):
    if isinstance(column, str):
        column = [column]

    partition_cols = ", ".join(column)
    check_col = column[0]

    partition_expr = ", ".join(f"NULLIF(TRIM({col}::STRING), '')" for col in column)
    all_columns_present = " AND ".join(
        f"NULLIF(TRIM({col}::STRING), '') IS NOT NULL" for col in column
    )
    expr = [f"""CASE WHEN {all_columns_present}
        AND COUNT(*) OVER(PARTITION BY {partition_expr}) > 1
        THEN 'unique({','.join(column)})' END"""]
    return expr


def validate_range(column, min, max):
    if isinstance(column, str):
        column = [column]

    expr = []
    for col in column:
        expr_col = (
            f"CASE WHEN NULLIF(TRIM({col}::STRING), '') IS NOT NULL "
            f"AND TRY_TO_DOUBLE({col}) NOT BETWEEN {min} AND {max} "
            f"THEN 'range({col})' END"
        )
        expr.append(expr_col)
    return expr


def validate_datatype(config):
    expr = []
    TYPE_MAPPING = {
        "integer": "TRY_TO_NUMBER({column})",
        "decimal": "TRY_TO_DECIMAL({column})",
        "date": "TRY_TO_DATE({column}{format})",
        "timestamp": "TRY_TO_TIMESTAMP({column})",
        "boolean": "TRY_TO_BOOLEAN({column})",
    }
    for column in config["columns"]:
        col_name = column["name"]
        col_type = column["type"]

        sql_template = TYPE_MAPPING.get(col_type)
        if not sql_template:
            continue

        fmt = ""
        if "format" in column:
            fmt = f", '{column['format']}'"

        cast_expr = sql_template.format(column=col_name, format=fmt)
        expr_col = (
            f"CASE WHEN NULLIF(TRIM({col_name}::STRING), '') IS NOT NULL "
            f"AND {cast_expr} IS NULL THEN 'datatype({col_name})' END"
        )
        expr.append(expr_col)

    return expr


VALIDATE_FUNCTIONS = {
    "not_null": validate_not_null,
    "unique": validate_unique,
    "range": validate_range,
}


def validate_l0_to_l1(config, schema, view_input, view_output):
    exprs = validate_datatype(config)
    for validation in config["l0_to_l1"]["validation"]:
        rule = validation["rule"]
        params = {k: v for k, v in validation.items() if k != "rule"}
        function_map = VALIDATE_FUNCTIONS[rule]
        expr_return = function_map(**params)
        exprs.extend(expr_return)

    exprs_str = ",\n".join(exprs)

    validate_sql = f"""
        CREATE OR REPLACE VIEW {schema}.{view_output} AS
        SELECT
            *,
            ARRAY_CONSTRUCT_COMPACT({exprs_str}) AS validation_errors
        FROM {schema}.{view_input}
    """

    return validate_sql


def get_view_validation(schema, view_input, view_output, isvalid):
    filter_sql = f"""
        CREATE OR REPLACE VIEW {schema}.{view_output} AS
        SELECT * FROM {schema}.{view_input}
        WHERE ARRAY_SIZE(validation_errors) {'= 0' if isvalid else '> 0'}
    """
    return filter_sql
