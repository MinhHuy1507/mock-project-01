import psycopg2
from commons.logger import get_logger

logging = get_logger(__name__)


def get_jdbc_url(db_config):
    return f"jdbc:postgresql://{db_config['host']}:{db_config['port']}/{db_config['database']}"


def execute_query(db_config, query):
    conn = psycopg2.connect(
        host=db_config["host"],
        port=db_config["port"],
        database=db_config["database"],
        user=db_config["user"],
        password=db_config["password"],
    )
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(query)
    cursor.close()
    conn.close()


def get_jdbc_properties(db_config, batch_size):
    return {
        "user": db_config["user"],
        "password": db_config["password"],
        "driver": "org.postgresql.Driver",
        "batchsize": str(batch_size),
        "rewriteBatchedInserts": "true",
        "stringtype": "unspecified"
    }


# CREATE TABLE FUNCTIONS
def create_table_customers(db_config):
    execute_query(
        db_config,
        """
        CREATE SCHEMA IF NOT EXISTS retail;
        CREATE TABLE IF NOT EXISTS retail.customers (
            customer_id VARCHAR(50) PRIMARY KEY,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            birthday DATE,
            address TEXT,
            address_province VARCHAR(100),
            kpi NUMERIC(10, 2),
            process_date TIMESTAMP,
            source_file VARCHAR(255)
        );
    """,
    )


def create_table_orders(db_config):
    execute_query(
        db_config,
        """
        CREATE SCHEMA IF NOT EXISTS retail;

        CREATE TABLE IF NOT EXISTS retail.orders (
            order_id VARCHAR(50) PRIMARY KEY,
            customer_id VARCHAR(50),
            product_id VARCHAR(50),
            quantity INTEGER,
            price NUMERIC(15, 2),
            order_date TIMESTAMP,
            process_date TIMESTAMP,
            source_file VARCHAR(255)
        );
    """,
    )


def create_table_province(db_config):
    execute_query(
        db_config,
        """
        CREATE SCHEMA IF NOT EXISTS retail;

        CREATE TABLE IF NOT EXISTS retail.province (
            province_id VARCHAR(50) PRIMARY KEY,
            province_name VARCHAR(255),
            process_date TIMESTAMP,
            source_file VARCHAR(255)
        );
    """,
    )


def create_table_products(db_config):
    execute_query(
        db_config,
        """
        CREATE SCHEMA IF NOT EXISTS retail;

        CREATE TABLE IF NOT EXISTS retail.products (
            product_id VARCHAR(50) PRIMARY KEY,
            product_name VARCHAR(255),
            unit_price NUMERIC(15, 2),
            process_date TIMESTAMP,
            source_file VARCHAR(255)
        );
    """,
    )


# LOAD STRATEGIES
def append_only(df, config, db_config):
    schema_name = config["schema_name"]
    table_name = config["table_name"]

    db_load_config = config.get("load_database", {})
    batch_size = db_load_config.get("batch_size", 10000)
    num_partitions = db_load_config.get("num_partitions", 4)

    jdbc_url = get_jdbc_url(db_config)
    properties = get_jdbc_properties(db_config, batch_size)

    logging.info(
        f"Writing to {table_name} with {num_partitions} partitions and batchsize {batch_size}"
    )

    df_append = df.repartition(num_partitions)
    df_append.write.jdbc(
        url=jdbc_url,
        table=f"{schema_name}.{table_name}",
        mode="append",
        properties=properties,
    )


def truncate_and_insert(df, config, db_config):
    schema_name = config["schema_name"]
    table_name = config["table_name"]

    execute_query(db_config, f"TRUNCATE TABLE {schema_name}.{table_name};")
    append_only(df, config, db_config)


def upsert(df, config, db_config):
    schema_name = config["schema_name"]
    table_name = config["table_name"]
    stg_table = f"{table_name}_stg"

    db_load_config = config.get("load_database", {})
    batch_size = db_load_config.get("batch_size", 10000)
    num_partitions = db_load_config.get("num_partitions", 4)
    primary_key = db_load_config.get("primary_key")

    jdbc_url = get_jdbc_url(db_config)
    properties = get_jdbc_properties(db_config, batch_size)

    # create staging table
    execute_query(
        db_config,
        f"""
        DROP TABLE IF EXISTS {schema_name}.{stg_table};
        CREATE TABLE {schema_name}.{stg_table} (LIKE {schema_name}.{table_name});
    """,
    )

    # write to staging table
    logging.info(
        f"Writing STG table {stg_table} with {num_partitions} partitions and batchsize {batch_size}"
    )
    df_write = df.repartition(num_partitions)

    df_write.write.jdbc(
        url=jdbc_url,
        table=f"{schema_name}.{stg_table}",
        mode="append",
        properties=properties,
    )

    # Merge from staging to main table
    columns = df.columns
    columns_text = ", ".join(columns)
    update_cols = ", ".join(
        f"{col} = EXCLUDED.{col}" for col in columns if col != primary_key
    )

    insert_into_main_table = f"""
        INSERT INTO {schema_name}.{table_name} ({columns_text})
        SELECT {columns_text}
        FROM {schema_name}.{stg_table}
        ON CONFLICT ({primary_key})
        DO UPDATE SET {update_cols};
    """

    logging.info(f"Merging from STG to Main table: {table_name}")
    execute_query(db_config, insert_into_main_table)
    execute_query(db_config, f"DROP TABLE IF EXISTS {schema_name}.{stg_table};")


CREATE_TABLES = {
    "customers": create_table_customers,
    "orders": create_table_orders,
    "province": create_table_province,
    "products": create_table_products,
}

LOAD_STRATEGIES = {
    "upsert": upsert,
    "truncate_and_insert": truncate_and_insert,
    "append_only": append_only,
}
