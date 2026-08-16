import csv
import random
from faker import Faker
from datetime import datetime, timedelta

from commons.utils import make_dirs


def generate_mock_data(path, prefix, num_records=100):
    fake = Faker("vi_VN")

    customers_path = path + "customers/" + prefix + "/"
    products_path = path + "products/" + prefix + "/"
    province_path = path + "province/" + prefix + "/"
    orders_path = path + "orders/" + prefix + "/"

    make_dirs(customers_path)
    make_dirs(products_path)
    make_dirs(province_path)
    make_dirs(orders_path)

    # Province
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

    provinces = []
    for i in range(1, len(PROVINCES) + 1):
        provinces.append({"id": f"PROV_{i}", "name": PROVINCES[i - 1]})

    with open(f"{province_path}/province.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name"])
        writer.writeheader()
        writer.writerows(provinces)

    # Products
    products = []
    for i in range(1, 51):
        products.append(
            {
                "id": f"PROD_{i}",
                "name": fake.catch_phrase(),
                "unit_price": round(random.uniform(10.0, 5000.0), 2),
            }
        )

    with open(f"{products_path}/products.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "unit_price"])
        writer.writeheader()
        writer.writerows(products)

    # Customers
    # Schema: id, name, birthday, address, kpi
    # Lỗi mô phỏng: kpi > 100, birthday sai định dạng, name null
    customers = []
    for i in range(1, num_records + 1):
        is_error = random.random() < 0.1

        c_id = f"CUST_{i}"
        name = fake.name() if not is_error else ""

        # Lỗi định dạng ngày
        if is_error and random.choice([True, False]):
            birthday = fake.date_of_birth(minimum_age=18, maximum_age=80).strftime(
                "%d-%m-%Y"
            )
        else:
            birthday = fake.date_of_birth(minimum_age=18, maximum_age=80).strftime(
                "%Y-%m-%d"
            )

        address = fake.address().replace("\n", ", ")

        address = (
            address.split(",")[0]
            + ", "
            + PROVINCES[random.randint(0, len(PROVINCES) - 1)]
        )

        # Lỗi range kpi (chuẩn là 0-100)
        kpi = round(random.uniform(0, 100), 2)
        if is_error:
            kpi = round(random.uniform(101, 200), 2)

        customers.append(
            {
                "id": c_id,
                "name": name,
                "birthday": birthday,
                "address": address,
                "kpi": kpi,
            }
        )

    with open(
        f"{customers_path}/customers.csv", "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=["id", "name", "birthday", "address", "kpi"]
        )
        writer.writeheader()
        writer.writerows(customers)

    # Orders
    # Schema: id, customer_id, product_id, quantity, price, order_date[cite: 2, 4]
    # Lỗi mô phỏng: null customer_id, số lượng âm
    orders = []
    for i in range(1, num_records * 2 + 1):
        is_error = random.random() < 0.1

        product = random.choice(products)
        customer_id = f"CUST_{random.randint(1, num_records)}"

        # Lỗi thiếu khóa ngoại / Not Null
        if is_error and random.choice([True, False]):
            customer_id = ""

        # Lỗi range quantity (chuẩn là 0-9999)
        quantity = random.randint(1, 10)
        if is_error:
            quantity = random.randint(-5, 0)

        orders.append(
            {
                "id": f"ORD_{i}",
                "customer_id": customer_id,
                "product_id": product["id"],
                "quantity": quantity,
                "price": product["unit_price"],
                "order_date": fake.date_time_between(
                    start_date="-5d", end_date="now"
                ).strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    with open(f"{orders_path}/orders.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "customer_id",
                "product_id",
                "quantity",
                "price",
                "order_date",
            ],
        )
        writer.writeheader()
        writer.writerows(orders)

    print(
        f"Đã tạo thành công dữ liệu với khoảng {num_records} records chính (có chèn % lỗi)!"
    )


if __name__ == "__main__":
    RECORD_COUNT = 100
    DATE = datetime.now().strftime("%Y/%m/%d")
    PATH = "../data/rcv/"
    generate_mock_data(path=PATH, num_records=RECORD_COUNT, prefix=DATE)
