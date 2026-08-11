from datetime import datetime

def transform(df, config, layer):
    if df.empty:
        return df
    
    transformations = config[layer]["transformation"]
    for transform_name, config in transformations.items():
        function = TRANSFORM_FUNCTIONS[transform_name]
        function(df, config)

    return df

# rcv_to_l0
COLUMNS = {
    "process_date": datetime.now(),
    "source_file": "temp"
}

def add_columns(df, config):
    for column in config:
        df[column["name"]] = COLUMNS[column["name"]]


# l0_to_l1
## customers
def split_customers_address(df, config):
    for rule in config:
        source = rule["from"]
        targets = rule["to"]

        result = df[source].str.split(
            ",",
            n=1,
            expand=True
        )

        df[targets] = result

def split_customers_name(df, config):
    for rule in config:
        source = rule["from"]
        first_col, last_col = rule["to"]

        split_series = df[source].apply(
            lambda x: x.split() if isinstance(x, str) and x.strip() else None
        )
        df[first_col] = split_series.apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else None)
        df[last_col] = split_series.apply(
            lambda x: " ".join(x[1:]) if isinstance(x, list) and len(x) > 1 else None
        )

def rename_columns(df, config):
    mapping = {}
    for rule in config:
        mapping[rule["from"]] = rule["to"]

    df.rename(columns=mapping, inplace=True)

TRANSFORM_FUNCTIONS = {
    "add_column": add_columns,
    "split_name": split_customers_name,
    "split_address": split_customers_address,
    "rename": rename_columns
}