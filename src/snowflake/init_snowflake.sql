USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS huynm43_mp;

CREATE SCHEMA IF NOT EXISTS huynm43_mp.retail;

USE DATABASE huynm43_mp;

USE SCHEMA retail;

-- Create storage integration
CREATE OR REPLACE STORAGE INTEGRATION huynm43_mp_snowflake_s3
TYPE = EXTERNAL_STAGE
STORAGE_PROVIDER = 'S3'
ENABLED = TRUE
STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::414061810527:role/huynm43-mp-snowflake-role'
STORAGE_ALLOWED_LOCATIONS = (
    's3://huynm43-mock-project-s3-414061810527-us-east-1-an/l0/',
    's3://huynm43-mock-project-s3-414061810527-us-east-1-an/l1/',
    's3://huynm43-mock-project-s3-414061810527-us-east-1-an/audit/'
);

DESC INTEGRATION huynm43_mp_snowflake_s3;

-- Create file format
CREATE OR REPLACE FILE FORMAT csv_ff
TYPE = CSV
SKIP_HEADER = 1
FIELD_OPTIONALLY_ENCLOSED_BY='"';

CREATE OR REPLACE FILE FORMAT parquet_ff
TYPE = PARQUET;

-- Create external stage
---- Stage l0
CREATE
OR REPLACE STAGE stage_l0 STORAGE_INTEGRATION = huynm43_mp_snowflake_s3 URL = 's3://huynm43-mock-project-s3-414061810527-us-east-1-an/l0/' FILE_FORMAT = csv_ff;

---- Stage audit
CREATE
OR REPLACE STAGE stage_audit STORAGE_INTEGRATION = huynm43_mp_snowflake_s3 URL = 's3://huynm43-mock-project-s3-414061810527-us-east-1-an/audit/' FILE_FORMAT = parquet_ff;

---- Stage l1
CREATE
OR REPLACE STAGE stage_l1 STORAGE_INTEGRATION = huynm43_mp_snowflake_s3 URL = 's3://huynm43-mock-project-s3-414061810527-us-east-1-an/l1/' FILE_FORMAT = parquet_ff;

-- Create external table
---- Customers
CREATE
OR REPLACE EXTERNAL TABLE retail.customers (
    id STRING AS (VALUE:c1::STRING),
    name STRING AS (VALUE:c2::STRING),
    birthday STRING AS (VALUE:c3::STRING),
    address STRING AS (VALUE:c4::STRING),
    kpi STRING AS (VALUE:c5::STRING),
    process_date STRING AS (VALUE:c6::STRING),
    source_file STRING AS (VALUE:c7::STRING),
    year STRING AS (
        SPLIT_PART(METADATA$FILENAME, '/', 1)
    ),
    month STRING AS (
        SPLIT_PART(METADATA$FILENAME, '/', 2)
    ),
    day STRING AS (
        SPLIT_PART(METADATA$FILENAME, '/', 3)
    )
)
PARTITION BY (year, month, day) LOCATION = @ stage_l0 / retail / customers / PATTERN = '.*/[^._][^/]*\\.csv$' FILE_FORMAT = csv_ff AUTO_REFRESH = FALSE;

---- Orders
CREATE
OR REPLACE EXTERNAL TABLE retail.orders (
    id STRING AS (VALUE:c1::STRING),
    customer_id STRING AS (VALUE:c2::STRING),
    product_id STRING AS (VALUE:c3::STRING),
    quantity STRING AS (VALUE:c4::STRING),
    price STRING AS (VALUE:c5::STRING),
    order_date STRING AS (VALUE:c6::STRING),
    process_date STRING AS (VALUE:c7::STRING),
    source_file STRING AS (VALUE:c8::STRING),
    year STRING AS (
        SPLIT_PART(METADATA$FILENAME, '/', 1)
    ),
    month STRING AS (
        SPLIT_PART(METADATA$FILENAME, '/', 2)
    ),
    day STRING AS (
        SPLIT_PART(METADATA$FILENAME, '/', 3)
    )
)
PARTITION BY (year, month, day) LOCATION = @ stage_l0 / retail / orders / PATTERN = '.*/[^._][^/]*\\.csv$' FILE_FORMAT = csv_ff AUTO_REFRESH = FALSE;

---- Products
CREATE
OR REPLACE EXTERNAL TABLE retail.products (
    id STRING AS (VALUE:c1::STRING),
    name STRING AS (VALUE:c2::STRING),
    unit_price STRING AS (VALUE:c3::STRING),
    process_date STRING AS (VALUE:c4::STRING),
    source_file STRING AS (VALUE:c5::STRING),
    year STRING AS (
        SPLIT_PART(METADATA$FILENAME, '/', 1)
    ),
    month STRING AS (
        SPLIT_PART(METADATA$FILENAME, '/', 2)
    ),
    day STRING AS (
        SPLIT_PART(METADATA$FILENAME, '/', 3)
    )
)
PARTITION BY (year, month, day) LOCATION = @ stage_l0 / retail / products / PATTERN = '.*/[^._][^/]*\\.csv$' FILE_FORMAT = csv_ff AUTO_REFRESH = FALSE;

---- Province
CREATE
OR REPLACE EXTERNAL TABLE retail.province (
    id STRING AS (VALUE:c1::STRING),
    name STRING AS (VALUE:c2::STRING),
    process_date STRING AS (VALUE:c3::STRING),
    source_file STRING AS (VALUE:c4::STRING),
    year STRING AS (
        SPLIT_PART(METADATA$FILENAME, '/', 1)
    ),
    month STRING AS (
        SPLIT_PART(METADATA$FILENAME, '/', 2)
    ),
    day STRING AS (
        SPLIT_PART(METADATA$FILENAME, '/', 3)
    )
)
PARTITION BY (year, month, day) LOCATION = @ stage_l0 / retail / province / PATTERN = '.*/[^._][^/]*\\.csv$' FILE_FORMAT = csv_ff AUTO_REFRESH = FALSE;

-- Create view
---- Customers
CREATE OR REPLACE VIEW retail.vw_customers AS
SELECT
    id,
    name,
    birthday,
    address,
    kpi,
    process_date,
    source_file,
    year,
    month,
    day
FROM retail.customers
WHERE
    LOWER(TRIM(id)) != 'id';

---- Orders
CREATE OR REPLACE VIEW retail.vw_orders AS
SELECT
    id,
    customer_id,
    product_id,
    quantity,
    price,
    order_date,
    process_date,
    source_file,
    year,
    month,
    day
FROM retail.orders
WHERE
    LOWER(TRIM(id)) != 'id';

---- Products
CREATE OR REPLACE VIEW retail.vw_products AS
SELECT
    id,
    name,
    unit_price,
    process_date,
    source_file,
    year,
    month,
    day
FROM retail.products
WHERE
    LOWER(TRIM(id)) != 'id';

---- Province
CREATE OR REPLACE VIEW retail.vw_province AS
SELECT
    id,
    name,
    process_date,
    source_file,
    year,
    month,
    day
FROM retail.province
WHERE
    LOWER(TRIM(id)) != 'id';