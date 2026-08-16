from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
from airflow.models.param import Param

from scripts.lambda_handler import lambda_handler

default_args = {
    "owner": "airflow",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "depends_on_past": False,
    "catch_up": False,
}

with DAG(
    dag_id="mock_project_v2",
    description="Run single table pipeline using params",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    tags=["pipeline", "mock-project"],
    params={
        "table_name": Param(
            default="customers",
            type="string",
            enum=["customers", "products", "orders", "province"],
            description="Chọn bảng dữ liệu cần xử lý",
        ),
        "custom_date": Param(
            default=datetime.now().strftime("%Y/%m/%d"),
            type="string",
            description="Nhập ngày chạy (YYYY/MM/DD). Để trống sẽ lấy ngày chạy tự động của Airflow.",
        ),
    },
) as dag:

    dynamic_table = "{{ params.table_name }}"
    dynamic_date = "{{ params.custom_date }}"

    rcv_to_l0 = PythonOperator(
        task_id="rcv_to_l0",
        python_callable=lambda_handler,
        op_kwargs={
            "event": {
                "job_id": "{{ dag.dag_id }}",
                "execution_id": "{{ run_id }}",
                "table": dynamic_table,
                "date_path": dynamic_date,
                "stage_name": "rcv_to_l0",
            },
            "context": {},
        },
    )

    l0_to_l1 = PythonOperator(
        task_id="l0_to_l1",
        python_callable=lambda_handler,
        op_kwargs={
            "event": {
                "job_id": "{{ dag.dag_id }}",
                "execution_id": "{{ run_id }}",
                "table": dynamic_table,
                "date_path": dynamic_date,
                "stage_name": "l0_to_l1",
            },
            "context": {},
        },
    )

    l1_to_database = PythonOperator(
        task_id="l1_to_database",
        python_callable=lambda_handler,
        op_kwargs={
            "event": {
                "job_id": "{{ dag.dag_id }}",
                "execution_id": "{{ run_id }}",
                "table": dynamic_table,
                "date_path": dynamic_date,
                "stage_name": "load_database",
            },
            "context": {},
        },
    )

    rcv_to_l0 >> l0_to_l1 >> l1_to_database
