from commons.utils import load_config

global_config = load_config("../config/global.yaml")
customers_config = load_config("../config/schemas/customers.yaml")
products_config = load_config("../config/schemas/products.yaml")
province_config = load_config("../config/schemas/province.yaml")
orders_config = load_config("../config/schemas/orders.yaml")

# Test
if __name__ == "__main__":
    config_file = "../config/temp.yaml"
    config = load_config(config_file=config_file)
    print(config)
