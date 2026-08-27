import os
from pathlib import Path
from commons.utils import load_config

DEFAULT_LOCAL_PATH = Path(__file__).resolve().parent.parent.parent / "config"
CONFIG_BASE_PATH = os.getenv("CONFIG_BASE_PATH", str(DEFAULT_LOCAL_PATH))

global_config = load_config(f"{CONFIG_BASE_PATH}/global.yaml")
customers_config = load_config(f"{CONFIG_BASE_PATH}/schemas/customers.yaml")
products_config = load_config(f"{CONFIG_BASE_PATH}/schemas/products.yaml")
province_config = load_config(f"{CONFIG_BASE_PATH}/schemas/province.yaml")
orders_config = load_config(f"{CONFIG_BASE_PATH}/schemas/orders.yaml")

CONFIGS = {
    "customers": customers_config,
    "products": products_config,
    "orders": orders_config,
    "province": province_config,
}

# postgres
pg_config = global_config["postgres"]
pg_username = pg_config["username"]
pg_password = pg_config["password"]
pg_host = pg_config["host"]
pg_port = pg_config["port"]
pg_database = pg_config["database"]
pg_conn = f"postgresql+psycopg2://{pg_username}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"

# Test
if __name__ == "__main__":
    config_file = "../config/temp.yaml"
    config = load_config(config_file=config_file)
    print(config)
