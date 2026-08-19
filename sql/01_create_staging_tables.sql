-- ============================================================
-- StockSense AI
-- Phase 3 - PostgreSQL Data Architecture
-- Step 1: Staging Tables
-- ============================================================

CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS analytics;


-- ============================================================
-- STAGING: SALES
-- ============================================================

DROP TABLE IF EXISTS staging.sales_raw;

CREATE TABLE staging.sales_raw (
    transaction_date        DATE,
    sales_type              VARCHAR(100),
    is_return               BOOLEAN,
    reason_of_return        VARCHAR(255),

    supplier                VARCHAR(100),
    product_no              VARCHAR(100),
    product_description     TEXT,

    product_division        VARCHAR(150),
    product_category        VARCHAR(150),
    product_subcategory     VARCHAR(150),
    product_segment         VARCHAR(150),

    store                   VARCHAR(100),
    sales_channel           VARCHAR(100),

    qty_sold                NUMERIC(18,4),
    sales_amount            NUMERIC(18,2),
    cogs                    NUMERIC(18,2),
    number_of_transactions  INTEGER
);


-- ============================================================
-- STAGING: INVENTORY
-- ============================================================

DROP TABLE IF EXISTS staging.inventory_raw;

CREATE TABLE staging.inventory_raw (
    start_date                  DATE,
    end_date                    DATE,

    stock_status                VARCHAR(100),

    supplier                    VARCHAR(100),
    product_no                  VARCHAR(100),
    product_description         TEXT,

    product_division            VARCHAR(150),
    product_category            VARCHAR(150),
    product_subcategory         VARCHAR(150),
    product_segment             VARCHAR(150),

    store                       VARCHAR(100),
    store_type                  VARCHAR(100),
    sales_channel               VARCHAR(100),

    qty_on_hand                 NUMERIC(18,4),

    stocks_selling_amount       NUMERIC(18,2),
    cost_of_stocks              NUMERIC(18,2),

    stock_unit_selling_price    NUMERIC(18,2),
    stock_unit_cost_price       NUMERIC(18,2)
);


--Sales
SELECT COUNT(*) AS sales_rows
FROM staging.sales_raw;

SELECT *
FROM staging.sales_raw
LIMIT 10;


-- Inventory
SELECT COUNT(*) AS inventory_rows
FROM staging.inventory_raw;

SELECT *
FROM staging.inventory_raw
LIMIT 10;