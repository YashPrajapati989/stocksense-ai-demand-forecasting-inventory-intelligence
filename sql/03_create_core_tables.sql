-- ============================================================
-- Phase 3 - PostgreSQL Data Architecture
-- ============================================================

CREATE SCHEMA IF NOT EXISTS core;

-- ============================================================
-- 1. DIM_DATE
-- ============================================================

DROP TABLE IF EXISTS core.dim_date CASCADE;

CREATE TABLE core.dim_date (
    date_key        INTEGER PRIMARY KEY,
    full_date       DATE NOT NULL UNIQUE,
    year            SMALLINT NOT NULL,
    quarter         SMALLINT NOT NULL,
    month_number    SMALLINT NOT NULL,
    month_name      VARCHAR(20) NOT NULL,
    month_short     VARCHAR(3) NOT NULL,
    week_of_year    SMALLINT NOT NULL,
    day_of_month    SMALLINT NOT NULL,
    day_of_week     SMALLINT NOT NULL,
    day_name        VARCHAR(20) NOT NULL,
    is_weekend      BOOLEAN NOT NULL
);


-- ============================================================
-- 2. DIM_STORE
-- ============================================================

DROP TABLE IF EXISTS core.dim_store CASCADE;

CREATE TABLE core.dim_store (
    store_key       BIGSERIAL PRIMARY KEY,
    store_id        VARCHAR(100) NOT NULL UNIQUE,
    store_type      VARCHAR(100),
    first_seen_date DATE,
    last_seen_date  DATE
);


-- ============================================================
-- 3. DIM_SUPPLIER
-- ============================================================

DROP TABLE IF EXISTS core.dim_supplier CASCADE;

CREATE TABLE core.dim_supplier (
    supplier_key    BIGSERIAL PRIMARY KEY,
    supplier_id     VARCHAR(100) NOT NULL UNIQUE,
    supplier_name   VARCHAR(255)
);


-- ============================================================
-- 4. DIM_PRODUCT
-- ============================================================

DROP TABLE IF EXISTS core.dim_product CASCADE;

CREATE TABLE core.dim_product (
    product_key         BIGSERIAL PRIMARY KEY,
    product_no          VARCHAR(100) NOT NULL UNIQUE,
    product_description TEXT,

    product_division    VARCHAR(150),
    product_category    VARCHAR(150),
    product_subcategory VARCHAR(150),
    product_segment     VARCHAR(150),

    supplier_key        BIGINT REFERENCES core.dim_supplier(supplier_key),

    first_seen_date     DATE,
    last_seen_date      DATE
);


-- ============================================================
-- 5. FACT_SALES
-- ============================================================

DROP TABLE IF EXISTS core.fact_sales CASCADE;

CREATE TABLE core.fact_sales (
    sales_key               BIGSERIAL PRIMARY KEY,

    date_key                INTEGER NOT NULL
                            REFERENCES core.dim_date(date_key),

    store_key               BIGINT NOT NULL
                            REFERENCES core.dim_store(store_key),

    product_key             BIGINT NOT NULL
                            REFERENCES core.dim_product(product_key),

    supplier_key            BIGINT
                            REFERENCES core.dim_supplier(supplier_key),

    transaction_date        DATE NOT NULL,

    sales_type              VARCHAR(100),
    is_return               BOOLEAN,
    reason_of_return        VARCHAR(255),
    sales_channel           VARCHAR(100),

    qty_sold                NUMERIC(18,4),
    sales_amount            NUMERIC(18,2),
    cogs                    NUMERIC(18,2),
    number_of_transactions  INTEGER,

    loaded_at               TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 6. FACT_INVENTORY
-- ===========================================================

DROP TABLE IF EXISTS core.fact_inventory CASCADE;

CREATE TABLE core.fact_inventory (
    inventory_key              BIGSERIAL PRIMARY KEY,

    store_key                  BIGINT NOT NULL
                               REFERENCES core.dim_store(store_key),

    product_key                BIGINT NOT NULL
                               REFERENCES core.dim_product(product_key),

    supplier_key               BIGINT
                               REFERENCES core.dim_supplier(supplier_key),

    start_date_key             INTEGER NOT NULL
                               REFERENCES core.dim_date(date_key),

    end_date_key               INTEGER
                               REFERENCES core.dim_date(date_key),

    start_date                 DATE NOT NULL,
    end_date                   DATE,

    is_open_ended              BOOLEAN NOT NULL DEFAULT FALSE,

    stock_status               VARCHAR(100),
    sales_channel              VARCHAR(100),

    qty_on_hand                NUMERIC(18,4),

    stocks_selling_amount      NUMERIC(18,2),
    cost_of_stocks             NUMERIC(18,2),

    stock_unit_selling_price   NUMERIC(18,2),
    stock_unit_cost_price      NUMERIC(18,2),

    loaded_at                  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_inventory_date_order
        CHECK (
            end_date IS NULL
            OR end_date >= start_date
        ),

    CONSTRAINT chk_inventory_open_ended
        CHECK (
            (is_open_ended = TRUE AND end_date IS NULL)
            OR
            (is_open_ended = FALSE AND end_date IS NOT NULL)
        )
);


-- ============================================================
-- 7. INDEXES — FACT TABLES
-- ============================================================

CREATE INDEX idx_fact_sales_date
    ON core.fact_sales(date_key);

CREATE INDEX idx_fact_sales_store
    ON core.fact_sales(store_key);

CREATE INDEX idx_fact_sales_product
    ON core.fact_sales(product_key);

CREATE INDEX idx_fact_sales_supplier
    ON core.fact_sales(supplier_key);

CREATE INDEX idx_fact_sales_transaction_date
    ON core.fact_sales(transaction_date);


CREATE INDEX idx_fact_inventory_store
    ON core.fact_inventory(store_key);

CREATE INDEX idx_fact_inventory_product
    ON core.fact_inventory(product_key);

CREATE INDEX idx_fact_inventory_supplier
    ON core.fact_inventory(supplier_key);

CREATE INDEX idx_fact_inventory_start_date
    ON core.fact_inventory(start_date_key);

CREATE INDEX idx_fact_inventory_end_date
    ON core.fact_inventory(end_date_key);

CREATE INDEX idx_fact_inventory_store_product
    ON core.fact_inventory(store_key, product_key);


-- ============================================================
-- 8. INDEXES — DIMENSIONS
-- ============================================================

CREATE INDEX idx_dim_product_category
    ON core.dim_product(product_category);

CREATE INDEX idx_dim_product_subcategory
    ON core.dim_product(product_subcategory);

CREATE INDEX idx_dim_product_segment
    ON core.dim_product(product_segment);

CREATE INDEX idx_dim_product_supplier
    ON core.dim_product(supplier_key);

CREATE INDEX idx_dim_store_type
    ON core.dim_store(store_type);


-- ============================================================
-- 9. CORE TABLE INVENTORY
-- ============================================================

SELECT
    table_schema,
    table_name
FROM information_schema.tables
WHERE table_schema = 'core'
ORDER BY table_name;