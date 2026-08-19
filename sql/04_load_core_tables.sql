-- ============================================================
-- Phase 3 - PostgreSQL Data Architecture
-- ============================================================

-- ============================================================
-- 0. REFRESH CORE DATA
-- ============================================================
-- Facts are cleared before dimensions because of FK dependencies.

TRUNCATE TABLE
    core.fact_inventory,
    core.fact_sales,
    core.dim_product,
    core.dim_store,
    core.dim_supplier,
    core.dim_date
RESTART IDENTITY CASCADE;

ROLLBACK;
-- ============================================================
-- 1. LOAD DIM_DATE
-- ============================================================
-- Date range is derived from the actual source data.
-- 9999-12-31 is an open-ended marker and is excluded.

WITH source_dates AS (
    SELECT transaction_date AS dt
    FROM staging.sales_raw
    WHERE transaction_date IS NOT NULL

    UNION

    SELECT start_date AS dt
    FROM staging.inventory_raw
    WHERE start_date IS NOT NULL

    UNION

    SELECT end_date AS dt
    FROM staging.inventory_raw
    WHERE end_date IS NOT NULL
      AND end_date <> DATE '9999-12-31'
),
date_bounds AS (
    SELECT
        MIN(dt) AS min_date,
        MAX(dt) AS max_date
    FROM source_dates
)
INSERT INTO core.dim_date (
    date_key,
    full_date,
    year,
    quarter,
    month_number,
    month_name,
    month_short,
    week_of_year,
    day_of_month,
    day_of_week,
    day_name,
    is_weekend
)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INTEGER AS date_key,
    d::DATE AS full_date,
    EXTRACT(YEAR FROM d)::SMALLINT AS year,
    EXTRACT(QUARTER FROM d)::SMALLINT AS quarter,
    EXTRACT(MONTH FROM d)::SMALLINT AS month_number,
    TO_CHAR(d, 'FMMonth') AS month_name,
    TO_CHAR(d, 'Mon') AS month_short,
    EXTRACT(WEEK FROM d)::SMALLINT AS week_of_year,
    EXTRACT(DAY FROM d)::SMALLINT AS day_of_month,
    EXTRACT(ISODOW FROM d)::SMALLINT AS day_of_week,
    TO_CHAR(d, 'FMDay') AS day_name,
    EXTRACT(ISODOW FROM d) IN (6, 7) AS is_weekend
FROM date_bounds,
     generate_series(
         min_date,
         max_date,
         INTERVAL '1 day'
     ) AS gs(d)
WHERE min_date IS NOT NULL
  AND max_date IS NOT NULL;


-- ============================================================
-- 2. LOAD DIM_SUPPLIER
-- ============================================================

INSERT INTO core.dim_supplier (
    supplier_id,
    supplier_name
)
SELECT DISTINCT
    TRIM(supplier) AS supplier_id,
    TRIM(supplier) AS supplier_name
FROM (
    SELECT supplier
    FROM staging.sales_raw

    UNION

    SELECT supplier
    FROM staging.inventory_raw
) s
WHERE NULLIF(TRIM(supplier), '') IS NOT NULL;


-- ============================================================
-- 3. LOAD DIM_STORE
-- ============================================================

WITH store_source AS (
    SELECT
        TRIM(store) AS store_id,
        NULLIF(TRIM(store_type), '') AS store_type,
        start_date AS observed_date
    FROM staging.inventory_raw
    WHERE NULLIF(TRIM(store), '') IS NOT NULL

    UNION ALL

    SELECT
        TRIM(store) AS store_id,
        NULL::VARCHAR(100) AS store_type,
        transaction_date AS observed_date
    FROM staging.sales_raw
    WHERE NULLIF(TRIM(store), '') IS NOT NULL
),
store_aggregated AS (
    SELECT
        store_id,
        MAX(store_type) AS store_type,
        MIN(observed_date) AS first_seen_date,
        MAX(observed_date) AS last_seen_date
    FROM store_source
    GROUP BY store_id
)
INSERT INTO core.dim_store (
    store_id,
    store_type,
    first_seen_date,
    last_seen_date
)
SELECT
    store_id,
    store_type,
    first_seen_date,
    last_seen_date
FROM store_aggregated;


-- ============================================================
-- 4. LOAD DIM_PRODUCT
-- ============================================================

WITH product_source AS (
    SELECT
        TRIM(product_no) AS product_no,
        NULLIF(TRIM(product_description), '') AS product_description,
        NULLIF(TRIM(product_division), '') AS product_division,
        NULLIF(TRIM(product_category), '') AS product_category,
        NULLIF(TRIM(product_subcategory), '') AS product_subcategory,
        NULLIF(TRIM(product_segment), '') AS product_segment,
        NULLIF(TRIM(supplier), '') AS supplier,
        transaction_date AS observed_date
    FROM staging.sales_raw
    WHERE NULLIF(TRIM(product_no), '') IS NOT NULL

    UNION ALL

    SELECT
        TRIM(product_no) AS product_no,
        NULLIF(TRIM(product_description), '') AS product_description,
        NULLIF(TRIM(product_division), '') AS product_division,
        NULLIF(TRIM(product_category), '') AS product_category,
        NULLIF(TRIM(product_subcategory), '') AS product_subcategory,
        NULLIF(TRIM(product_segment), '') AS product_segment,
        NULLIF(TRIM(supplier), '') AS supplier,
        start_date AS observed_date
    FROM staging.inventory_raw
    WHERE NULLIF(TRIM(product_no), '') IS NOT NULL
),
product_attributes AS (
    SELECT
        product_no,
        MAX(product_description) AS product_description,
        MAX(product_division) AS product_division,
        MAX(product_category) AS product_category,
        MAX(product_subcategory) AS product_subcategory,
        MAX(product_segment) AS product_segment,
        MIN(observed_date) AS first_seen_date,
        MAX(observed_date) AS last_seen_date
    FROM product_source
    GROUP BY product_no
),
supplier_frequency AS (
    SELECT
        product_no,
        supplier,
        COUNT(*) AS supplier_count,
        ROW_NUMBER() OVER (
            PARTITION BY product_no
            ORDER BY COUNT(*) DESC, supplier
        ) AS rn
    FROM product_source
    WHERE supplier IS NOT NULL
    GROUP BY product_no, supplier
)
INSERT INTO core.dim_product (
    product_no,
    product_description,
    product_division,
    product_category,
    product_subcategory,
    product_segment,
    supplier_key,
    first_seen_date,
    last_seen_date
)
SELECT
    p.product_no,
    p.product_description,
    p.product_division,
    p.product_category,
    p.product_subcategory,
    p.product_segment,
    ds.supplier_key,
    p.first_seen_date,
    p.last_seen_date
FROM product_attributes p
LEFT JOIN supplier_frequency sf
    ON p.product_no = sf.product_no
   AND sf.rn = 1
LEFT JOIN core.dim_supplier ds
    ON ds.supplier_id = sf.supplier;


-- ============================================================
-- 5. LOAD FACT_SALES
-- ============================================================

INSERT INTO core.fact_sales (
    date_key,
    store_key,
    product_key,
    supplier_key,
    transaction_date,
    sales_type,
    is_return,
    reason_of_return,
    sales_channel,
    qty_sold,
    sales_amount,
    cogs,
    number_of_transactions
)
SELECT
    dd.date_key,
    ds.store_key,
    dp.product_key,
    sup.supplier_key,
    s.transaction_date,
    s.sales_type,
    s.is_return,
    s.reason_of_return,
    s.sales_channel,
    s.qty_sold,
    s.sales_amount,
    s.cogs,
    s.number_of_transactions
FROM staging.sales_raw s
JOIN core.dim_date dd
    ON dd.full_date = s.transaction_date
JOIN core.dim_store ds
    ON ds.store_id = TRIM(s.store)
JOIN core.dim_product dp
    ON dp.product_no = TRIM(s.product_no)
LEFT JOIN core.dim_supplier sup
    ON sup.supplier_id = NULLIF(TRIM(s.supplier), '');


-- ============================================================
-- 6. LOAD FACT_INVENTORY
-- ============================================================

INSERT INTO core.fact_inventory (
    store_key,
    product_key,
    supplier_key,
    start_date_key,
    end_date_key,
    start_date,
    end_date,
    is_open_ended,
    stock_status,
    sales_channel,
    qty_on_hand,
    stocks_selling_amount,
    cost_of_stocks,
    stock_unit_selling_price,
    stock_unit_cost_price
)
SELECT
    ds.store_key,
    dp.product_key,
    sup.supplier_key,

    start_dd.date_key,

    CASE
        WHEN i.end_date = DATE '9999-12-31'
            THEN NULL
        ELSE end_dd.date_key
    END AS end_date_key,

    i.start_date,

    CASE
        WHEN i.end_date = DATE '9999-12-31'
            THEN NULL
        ELSE i.end_date
    END AS end_date,

    (i.end_date = DATE '9999-12-31') AS is_open_ended,

    i.stock_status,
    i.sales_channel,
    i.qty_on_hand,
    i.stocks_selling_amount,
    i.cost_of_stocks,
    i.stock_unit_selling_price,
    i.stock_unit_cost_price

FROM staging.inventory_raw i

JOIN core.dim_store ds
    ON ds.store_id = TRIM(i.store)

JOIN core.dim_product dp
    ON dp.product_no = TRIM(i.product_no)

LEFT JOIN core.dim_supplier sup
    ON sup.supplier_id = NULLIF(TRIM(i.supplier), '')

JOIN core.dim_date start_dd
    ON start_dd.full_date = i.start_date

LEFT JOIN core.dim_date end_dd
    ON end_dd.full_date = i.end_date
   AND i.end_date <> DATE '9999-12-31';


COMMIT;


-- ============================================================
-- 7. POST-LOAD ROW COUNT VALIDATION
-- ============================================================

SELECT 'dim_date' AS table_name, COUNT(*) AS row_count
FROM core.dim_date

UNION ALL

SELECT 'dim_store', COUNT(*)
FROM core.dim_store

UNION ALL

SELECT 'dim_supplier', COUNT(*)
FROM core.dim_supplier

UNION ALL

SELECT 'dim_product', COUNT(*)
FROM core.dim_product

UNION ALL

SELECT 'fact_sales', COUNT(*)
FROM core.fact_sales

UNION ALL

SELECT 'fact_inventory', COUNT(*)
FROM core.fact_inventory

ORDER BY table_name;


-- ============================================================
-- 8. SOURCE → CORE RECONCILIATION
-- ============================================================

SELECT
    (SELECT COUNT(*) FROM staging.sales_raw) AS staging_sales_rows,
    (SELECT COUNT(*) FROM core.fact_sales) AS core_sales_rows,
    (SELECT COUNT(*) FROM staging.sales_raw)
      -
    (SELECT COUNT(*) FROM core.fact_sales) AS sales_row_difference;

SELECT
    (SELECT COUNT(*) FROM staging.inventory_raw) AS staging_inventory_rows,
    (SELECT COUNT(*) FROM core.fact_inventory) AS core_inventory_rows,
    (SELECT COUNT(*) FROM staging.inventory_raw)
      -
    (SELECT COUNT(*) FROM core.fact_inventory) AS inventory_row_difference;


-- ============================================================
-- 9. OPEN-ENDED INVENTORY RECONCILIATION
-- ============================================================

SELECT
    (SELECT COUNT(*)
     FROM staging.inventory_raw
     WHERE end_date = DATE '9999-12-31') AS staging_open_ended,

    (SELECT COUNT(*)
     FROM core.fact_inventory
     WHERE is_open_ended = TRUE) AS core_open_ended;


-- ============================================================
-- 10. FOREIGN KEY / ORPHAN CHECKS
-- ============================================================

SELECT COUNT(*) AS orphan_sales_dates
FROM core.fact_sales f
LEFT JOIN core.dim_date d
    ON d.date_key = f.date_key
WHERE d.date_key IS NULL;

SELECT COUNT(*) AS orphan_sales_stores
FROM core.fact_sales f
LEFT JOIN core.dim_store d
    ON d.store_key = f.store_key
WHERE d.store_key IS NULL;

SELECT COUNT(*) AS orphan_sales_products
FROM core.fact_sales f
LEFT JOIN core.dim_product d
    ON d.product_key = f.product_key
WHERE d.product_key IS NULL;

SELECT COUNT(*) AS orphan_inventory_stores
FROM core.fact_inventory f
LEFT JOIN core.dim_store d
    ON d.store_key = f.store_key
WHERE d.store_key IS NULL;

SELECT COUNT(*) AS orphan_inventory_products
FROM core.fact_inventory f
LEFT JOIN core.dim_product d
    ON d.product_key = f.product_key
WHERE d.product_key IS NULL;


-- ============================================================
-- 11. CORE SAMPLE CHECKS
-- ============================================================

SELECT *
FROM core.dim_product
ORDER BY product_key
LIMIT 10;

SELECT *
FROM core.fact_sales
ORDER BY sales_key
LIMIT 10;

SELECT *
FROM core.fact_inventory
ORDER BY inventory_key
LIMIT 10;