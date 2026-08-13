import os
from pathlib import Path
from commons.utils import load_config

DEFAULT_LOCAL_PATH = Path(__file__).resolve().parent.parent / "config"
CONFIG_BASE_PATH = os.getenv("CONFIG_BASE_PATH", str(DEFAULT_LOCAL_PATH))

global_config = load_config(f"{CONFIG_BASE_PATH}/global.yaml")
customers_config = load_config(f"{CONFIG_BASE_PATH}/schemas/customers.yaml")
products_config = load_config(f"{CONFIG_BASE_PATH}/schemas/products.yaml")
province_config = load_config(f"{CONFIG_BASE_PATH}/schemas/province.yaml")
orders_config = load_config(f"{CONFIG_BASE_PATH}/schemas/orders.yaml")

# Test
if __name__ == "__main__":
    config_file = "../config/temp.yaml"
    config = load_config(config_file=config_file)
    print(config)
