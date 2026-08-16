"""DAG for testing connectivity to PostgreSQL and MinIO S3."""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

from datetime import datetime, timedelta

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}

POSTGRES_CONN_ID = "postgres_dw"
AWS_CONN_ID = "minio_s3"


def check_postgres_connection():
    try:
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        conn = pg_hook.get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        logger.info(f"Postgres Connection Successful, Query Result: {result}")
    except Exception as e:
        logger.error(f"Postgres Connection Failed: {e}")


def check_s3_connection():
    try:
        s3_hook = S3Hook(aws_conn_id=AWS_CONN_ID)
        conn = s3_hook.get_conn()
        logger.info(f"S3 Connection Successful: {conn}")
    except Exception as e:
        logger.error(f"S3 Connection Failed: {e}")


with DAG(
    dag_id="ops_check_connectivity",
    description="Check connectivity to Postgres, Minio S3",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    template_searchpath=["/opt/airflow"],
    tags=["ops", "setup", "check connections"],
) as dag:

    ping_postgres = PythonOperator(
        task_id="ping_postgres", python_callable=check_postgres_connection
    )
    ping_minio = PythonOperator(
        task_id="ping_minio", python_callable=check_s3_connection
    )
