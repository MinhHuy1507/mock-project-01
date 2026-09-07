import csv
import random
from faker import Faker
from datetime import datetime, timedelta
import time

from commons.utils import make_dirs


def generate_mock_data(path, prefix, num_records=100):
    start = time.perf_counter()
    fake = Faker("vi_VN")

    customers_path = path + "customers/" + prefix + "/"
    products_path = path + "products/" + prefix + "/"
    province_path = path + "province/" + prefix + "/"
    orders_path = path + "orders/" + prefix + "/"

    make_dirs(customers_path)
    make_dirs(products_path)
    make_dirs(province_path)
    make_dirs(orders_path)

    orders_count = num_records
    customer_count = max(1000, int(orders_count**0.55))
    product_count = int(customer_count * 1.5)

    # Provinces in Vietnam
    PROVINCES = [
        "Ha Noi",
        "Hai Phong",
        "Quang Ninh",
        "Lang Son",
        "Cao Bang",
        "Tuyen Quang",
        "Lao Cai",
        "Thai Nguyen",
        "Phu Tho",
        "Bac Ninh",
        "Hung Yen",
        "Ninh Binh",
        "Thanh Hoa",
        "Nghe An",
        "Ha Tinh",
        "Quang Tri",
        "Hue",
        "Da Nang",
        "Quang Ngai",
        "Gia Lai",
        "Dak Lak",
        "Khanh Hoa",
        "Lam Dong",
        "Dong Nai",
        "Tay Ninh",
        "Ho Chi Minh",
        "Dong Thap",
        "An Giang",
        "Vinh Long",
        "Can Tho",
        "Ca Mau",
        "Kien Giang",
        "Son La",
        "Dien Bien",
    ]

    print("Creating Province data")
    with open(f"{province_path}/province.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name"])
        for i, name in enumerate(PROVINCES, 1):
            writer.writerow([f"PROV_{i}", name])

    print(f"Province: {time.perf_counter() - start:.3f}s")

    # Products
    start = time.perf_counter()
    print("Creating Products data...")
    POOL_SIZE = 1000
    product_name_pool = [fake.catch_phrase() for _ in range(POOL_SIZE)]
    product_prices = {}
    product_ids = []

    with open(f"{products_path}/products.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "unit_price"])
        for i in range(1, product_count + 1):
            product_id = f"PROD_{i}"
            price = round(random.uniform(10.0, 5000.0), 2)

            product_ids.append(product_id)
            product_prices[product_id] = price

            writer.writerow(
                [product_id, f"{random.choice(product_name_pool)}_{i}", price]
            )

    print(f"Products: {time.perf_counter() - start:.3f}s")

    # Customers
    start = time.perf_counter()
    print(f"Creating data for {customer_count} Customers...")
    NAME_POOL_SIZE = 2000
    STREET_POOL_SIZE = 2000

    last_name_pool = [fake.last_name() for _ in range(300)]
    middle_name_pool = [fake.middle_name() for _ in range(1000)]
    first_name_pool = [fake.first_name() for _ in range(NAME_POOL_SIZE)]
    street_pool = [fake.street_name() for _ in range(STREET_POOL_SIZE)]
    customer_ids = []

    start_birth = datetime(1945, 1, 1)
    end_birth = datetime(2008, 12, 31)
    birth_range_days = (end_birth - start_birth).days

    with open(
        f"{customers_path}/customers.csv", "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "birthday", "address", "kpi"])

        for i in range(1, customer_count + 1):
            is_error = random.random() < 0.1
            cust_id = f"CUST_{i}"
            customer_ids.append(cust_id)

            # Name
            if is_error:
                name = ""
            else:
                name = f"{random.choice(last_name_pool)} {random.choice(middle_name_pool)} {random.choice(first_name_pool)}"

            # Birthday
            birthday_dt = start_birth + timedelta(
                days=random.randint(0, birth_range_days)
            )
            if is_error and random.choice([True, False]):
                birthday = birthday_dt.strftime("%d-%m-%Y")
            else:
                birthday = birthday_dt.strftime("%Y-%m-%d")

            # Address
            address = f"{random.choice(street_pool)}, {random.choice(PROVINCES)}"

            # KPI
            kpi = round(random.uniform(0, 100), 2)
            if is_error:
                kpi = round(random.uniform(101, 200), 2)

            writer.writerow([cust_id, name, birthday, address, kpi])

    print(f"Customers: {time.perf_counter() - start:.3f}s")

    # Orders
    start = time.perf_counter()
    print(f"Creating {orders_count:,} Orders...")
    base_ts = int(datetime.now().timestamp())

    date_pool = [
        datetime.fromtimestamp(base_ts - random.randint(0, 100)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        for _ in range(1_000)
    ]

    with open(f"{orders_path}/orders.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["id", "customer_id", "product_id", "quantity", "price", "order_date"]
        )

        for i in range(1, orders_count + 1):
            is_error = random.random() < 0.1

            customer_id = random.choice(customer_ids)
            if is_error and random.choice([True, False]):
                customer_id = ""

            product_id = random.choice(product_ids)

            quantity = random.randint(1, 10)
            if is_error:
                quantity = random.randint(-5, 0)

            random_seconds = random.randint(0, 86400 * 5)
            order_date = random.choice(date_pool)

            writer.writerow(
                [
                    f"ORD_{i}",
                    customer_id,
                    product_id,
                    quantity,
                    product_prices[product_id],
                    order_date,
                ]
            )

            if i % 100_000 == 0:
                print(f"  -> Created {i:,} Order rows.")
        print(f"Orders: {time.perf_counter() - start:.3f}s")

    print(f"\n=> COMPLETED! Created data for {num_records:,} records!")


# Test
if __name__ == "__main__":
    RECORD_COUNT = 100_000
    DATE = datetime.now().strftime("%Y/%m/%d")
    PATH = "../../../data/rcv/"

    generate_mock_data(path=PATH, num_records=RECORD_COUNT, prefix=DATE)
