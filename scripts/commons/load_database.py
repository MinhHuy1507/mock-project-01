from commons.utils import load_config, read_parquet
from sqlalchemy import create_engine, text
from commons.configs import pg_conn


def get_engine():
    return create_engine(pg_conn, pool_pre_ping=True)


def create_table_customers():
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute("""
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
        """)


def create_table_orders():
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute("""
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
        """)


def create_table_province():
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute("""
            CREATE SCHEMA IF NOT EXISTS retail;

            CREATE TABLE IF NOT EXISTS retail.province (
                province_id VARCHAR(50) PRIMARY KEY,
                province_name VARCHAR(255),
                process_date TIMESTAMP,
                source_file VARCHAR(255)
            );
        """)


def create_table_products():
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute("""
            CREATE SCHEMA IF NOT EXISTS retail;

            CREATE TABLE IF NOT EXISTS retail.products (
                product_id VARCHAR(50) PRIMARY KEY,
                product_name VARCHAR(255),
                unit_price NUMERIC(15, 2),
                process_date TIMESTAMP,
                source_file VARCHAR(255)
            );
        """)


def append_only(file_path, config):
    schema_name = config["schema_name"]
    table_name = config["table_name"]

    df = read_parquet(file_path)
    engine = get_engine()
    with engine.begin() as conn:
        df.to_sql(
            name=table_name,
            schema=schema_name,
            con=conn,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=10000,
        )


def truncate_and_insert(file_path, config):
    schema_name = config["schema_name"]
    table_name = config["table_name"]

    df = read_parquet(file_path)
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(f"TRUNCATE TABLE {schema_name}.{table_name}")
        df.to_sql(
            name=table_name,
            schema=schema_name,
            con=conn,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=10000,
        )


def upsert(file_path, config):
    schema_name = config["schema_name"]
    table_name = config["table_name"]

    df = read_parquet(file_path)

    columns = df.columns.to_list()
    columns_text = ", ".join(columns)
    primary_key = config["load_database"]["primary_key"]
    update_cols = ", ".join(
        f"{col} = EXCLUDED.{col}" for col in columns if col != primary_key
    )
    insert_into_main_table = f"""
        INSERT INTO {schema_name}.{table_name} ({columns_text})
        SELECT {columns_text}
        FROM {schema_name}.{table_name}_stg
        ON CONFLICT ({primary_key})
        DO UPDATE
        SET {update_cols};
    """

    create_temp_table = f"""
        DROP TABLE IF EXISTS {schema_name}.{table_name}_stg;
        CREATE TABLE {schema_name}.{table_name}_stg (LIKE {schema_name}.{table_name});
    """

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(create_temp_table))
        df.to_sql(
            name=f"{table_name}_stg",
            schema=schema_name,
            con=conn,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=10000,
        )
        conn.execute(text(insert_into_main_table))


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
