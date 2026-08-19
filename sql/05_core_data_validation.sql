-- ============================================================
-- Phase 3 - PostgreSQL Data Architecture
-- ============================================================


-- ============================================================
-- 1. CORE TABLE ROW COUNTS
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
-- 2. SOURCE → CORE ROW COUNT RECONCILIATION
-- ============================================================

SELECT
    (SELECT COUNT(*) FROM staging.sales_raw) AS staging_sales_rows,
    (SELECT COUNT(*) FROM core.fact_sales) AS core_sales_rows,
    (SELECT COUNT(*) FROM staging.sales_raw)
      - (SELECT COUNT(*) FROM core.fact_sales) AS sales_difference;

SELECT
    (SELECT COUNT(*) FROM staging.inventory_raw) AS staging_inventory_rows,
    (SELECT COUNT(*) FROM core.fact_inventory) AS core_inventory_rows,
    (SELECT COUNT(*) FROM staging.inventory_raw)
      - (SELECT COUNT(*) FROM core.fact_inventory) AS inventory_difference;


-- ============================================================
-- 3. PRIMARY KEY UNIQUENESS
-- ============================================================

SELECT
    'dim_date.date_key' AS key_name,
    COUNT(*) - COUNT(DISTINCT date_key) AS duplicate_keys
FROM core.dim_date

UNION ALL

SELECT
    'dim_store.store_key',
    COUNT(*) - COUNT(DISTINCT store_key)
FROM core.dim_store

UNION ALL

SELECT
    'dim_supplier.supplier_key',
    COUNT(*) - COUNT(DISTINCT supplier_key)
FROM core.dim_supplier

UNION ALL

SELECT
    'dim_product.product_key',
    COUNT(*) - COUNT(DISTINCT product_key)
FROM core.dim_product

UNION ALL

SELECT
    'fact_sales.sales_key',
    COUNT(*) - COUNT(DISTINCT sales_key)
FROM core.fact_sales

UNION ALL

SELECT
    'fact_inventory.inventory_key',
    COUNT(*) - COUNT(DISTINCT inventory_key)
FROM core.fact_inventory;


-- ============================================================
-- 4. NATURAL / BUSINESS KEY UNIQUENESS
-- ============================================================

SELECT
    COUNT(*) AS duplicate_product_numbers
FROM (
    SELECT product_no
    FROM core.dim_product
    GROUP BY product_no
    HAVING COUNT(*) > 1
) d;

SELECT
    COUNT(*) AS duplicate_store_ids
FROM (
    SELECT store_id
    FROM core.dim_store
    GROUP BY store_id
    HAVING COUNT(*) > 1
) d;

SELECT
    COUNT(*) AS duplicate_supplier_ids
FROM (
    SELECT supplier_id
    FROM core.dim_supplier
    GROUP BY supplier_id
    HAVING COUNT(*) > 1
) d;


-- ============================================================
-- 5. FOREIGN KEY / ORPHAN VALIDATION — SALES
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

SELECT COUNT(*) AS orphan_sales_suppliers
FROM core.fact_sales f
LEFT JOIN core.dim_supplier d
    ON d.supplier_key = f.supplier_key
WHERE f.supplier_key IS NOT NULL
  AND d.supplier_key IS NULL;


-- ============================================================
-- 6. FOREIGN KEY / ORPHAN VALIDATION — INVENTORY
-- ============================================================

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

SELECT COUNT(*) AS orphan_inventory_suppliers
FROM core.fact_inventory f
LEFT JOIN core.dim_supplier d
    ON d.supplier_key = f.supplier_key
WHERE f.supplier_key IS NOT NULL
  AND d.supplier_key IS NULL;

SELECT COUNT(*) AS orphan_inventory_start_dates
FROM core.fact_inventory f
LEFT JOIN core.dim_date d
    ON d.date_key = f.start_date_key
WHERE d.date_key IS NULL;

SELECT COUNT(*) AS orphan_inventory_end_dates
FROM core.fact_inventory f
LEFT JOIN core.dim_date d
    ON d.date_key = f.end_date_key
WHERE f.end_date_key IS NOT NULL
  AND d.date_key IS NULL;


-- ============================================================
-- 7. NULL FOREIGN KEY PROFILE
-- ============================================================

SELECT
    COUNT(*) AS total_sales,
    COUNT(*) FILTER (WHERE date_key IS NULL) AS null_date_key,
    COUNT(*) FILTER (WHERE store_key IS NULL) AS null_store_key,
    COUNT(*) FILTER (WHERE product_key IS NULL) AS null_product_key,
    COUNT(*) FILTER (WHERE supplier_key IS NULL) AS null_supplier_key
FROM core.fact_sales;

SELECT
    COUNT(*) AS total_inventory,
    COUNT(*) FILTER (WHERE start_date_key IS NULL) AS null_start_date_key,
    COUNT(*) FILTER (WHERE store_key IS NULL) AS null_store_key,
    COUNT(*) FILTER (WHERE product_key IS NULL) AS null_product_key,
    COUNT(*) FILTER (WHERE supplier_key IS NULL) AS null_supplier_key,
    COUNT(*) FILTER (WHERE end_date_key IS NULL) AS null_end_date_key
FROM core.fact_inventory;


-- ============================================================
-- 8. DATE DIMENSION CONTINUITY
-- ============================================================

SELECT
    MIN(full_date) AS minimum_date,
    MAX(full_date) AS maximum_date,
    COUNT(*) AS date_rows,
    (MAX(full_date) - MIN(full_date) + 1) AS expected_date_rows,
    COUNT(*) - (MAX(full_date) - MIN(full_date) + 1) AS missing_date_rows
FROM core.dim_date;


-- ============================================================
-- 9. DATE KEY CONSISTENCY
-- ============================================================

SELECT COUNT(*) AS inconsistent_date_keys
FROM core.dim_date
WHERE date_key <> TO_CHAR(full_date, 'YYYYMMDD')::INTEGER;


-- ============================================================
-- 10. FACT SALES DATE CONSISTENCY
-- ============================================================

SELECT COUNT(*) AS inconsistent_sales_dates
FROM core.fact_sales f
JOIN core.dim_date d
    ON d.date_key = f.date_key
WHERE f.transaction_date <> d.full_date;


-- ============================================================
-- 11. FACT INVENTORY DATE CONSISTENCY
-- ============================================================

SELECT COUNT(*) AS inconsistent_inventory_start_dates
FROM core.fact_inventory f
JOIN core.dim_date d
    ON d.date_key = f.start_date_key
WHERE f.start_date <> d.full_date;

SELECT COUNT(*) AS inconsistent_inventory_end_dates
FROM core.fact_inventory f
JOIN core.dim_date d
    ON d.date_key = f.end_date_key
WHERE f.end_date IS NOT NULL
  AND f.end_date <> d.full_date;


-- ============================================================
-- 12. INVENTORY INTERVAL INTEGRITY
-- ============================================================

SELECT
    COUNT(*) AS invalid_inventory_intervals
FROM core.fact_inventory
WHERE end_date IS NOT NULL
  AND end_date < start_date;

SELECT
    COUNT(*) AS open_ended_flag_mismatch
FROM core.fact_inventory
WHERE
    (is_open_ended = TRUE AND end_date IS NOT NULL)
    OR
    (is_open_ended = FALSE AND end_date IS NULL);


-- ============================================================
-- 13. OPEN-ENDED INVENTORY RECONCILIATION
-- ============================================================

SELECT
    (SELECT COUNT(*)
     FROM staging.inventory_raw
     WHERE end_date = DATE '9999-12-31') AS staging_open_ended,

    (SELECT COUNT(*)
     FROM core.fact_inventory
     WHERE is_open_ended = TRUE) AS core_open_ended,

    (
        (SELECT COUNT(*)
         FROM staging.inventory_raw
         WHERE end_date = DATE '9999-12-31')
        -
        (SELECT COUNT(*)
         FROM core.fact_inventory
         WHERE is_open_ended = TRUE)
    ) AS difference;


-- ============================================================
-- 14. SALES FACT GRAIN CHECK
-- ============================================================
-- The intended grain is one source row = one fact row.
-- Exact duplicate fact rows should therefore be investigated.

SELECT
    COUNT(*) AS duplicate_sales_grain_groups
FROM (
    SELECT
        transaction_date,
        store_key,
        product_key,
        supplier_key,
        sales_type,
        is_return,
        reason_of_return,
        sales_channel,
        qty_sold,
        sales_amount,
        cogs,
        number_of_transactions,
        COUNT(*) AS row_count
    FROM core.fact_sales
    GROUP BY
        transaction_date,
        store_key,
        product_key,
        supplier_key,
        sales_type,
        is_return,
        reason_of_return,
        sales_channel,
        qty_sold,
        sales_amount,
        cogs,
        number_of_transactions
    HAVING COUNT(*) > 1
) d;


-- ============================================================
-- 15. INVENTORY FACT GRAIN CHECK
-- ============================================================
-- The intended grain is one source inventory interval = one fact row.

SELECT
    COUNT(*) AS duplicate_inventory_grain_groups
FROM (
    SELECT
        store_key,
        product_key,
        supplier_key,
        start_date,
        end_date,
        stock_status,
        sales_channel,
        qty_on_hand,
        stocks_selling_amount,
        cost_of_stocks,
        stock_unit_selling_price,
        stock_unit_cost_price,
        COUNT(*) AS row_count
    FROM core.fact_inventory
    GROUP BY
        store_key,
        product_key,
        supplier_key,
        start_date,
        end_date,
        stock_status,
        sales_channel,
        qty_on_hand,
        stocks_selling_amount,
        cost_of_stocks,
        stock_unit_selling_price,
        stock_unit_cost_price
    HAVING COUNT(*) > 1
) d;


-- ============================================================
-- 16. SALES FINANCIAL QUALITY
-- ============================================================

SELECT
    COUNT(*) FILTER (WHERE qty_sold < 0) AS negative_qty,
    COUNT(*) FILTER (WHERE sales_amount < 0) AS negative_sales_amount,
    COUNT(*) FILTER (WHERE cogs < 0) AS negative_cogs,
    COUNT(*) FILTER (WHERE sales_amount IS NULL) AS null_sales_amount,
    COUNT(*) FILTER (WHERE cogs IS NULL) AS null_cogs
FROM core.fact_sales;


-- ============================================================
-- 17. INVENTORY FINANCIAL QUALITY
-- ============================================================

SELECT
    COUNT(*) FILTER (WHERE qty_on_hand < 0) AS negative_qty_on_hand,
    COUNT(*) FILTER (WHERE stocks_selling_amount < 0) AS negative_selling_value,
    COUNT(*) FILTER (WHERE cost_of_stocks < 0) AS negative_cost_value,
    COUNT(*) FILTER (WHERE stock_unit_selling_price < 0) AS negative_selling_price,
    COUNT(*) FILTER (WHERE stock_unit_cost_price < 0) AS negative_cost_price
FROM core.fact_inventory;


-- ============================================================
-- 18. INVENTORY VALUATION RECONCILIATION
-- ============================================================

SELECT
    COUNT(*) AS total_inventory_rows,

    COUNT(*) FILTER (
        WHERE ABS(
            stocks_selling_amount
            - (qty_on_hand * stock_unit_selling_price)
        ) > 0.01
    ) AS selling_value_mismatches,

    COUNT(*) FILTER (
        WHERE ABS(
            cost_of_stocks
            - (qty_on_hand * stock_unit_cost_price)
        ) > 0.01
    ) AS cost_value_mismatches

FROM core.fact_inventory;


-- ============================================================
-- 19. DIMENSION REFERENTIAL COVERAGE
-- ============================================================

SELECT
    'Sales → Stores' AS relationship,
    COUNT(DISTINCT f.store_key) AS fact_keys,
    COUNT(DISTINCT d.store_key) AS matching_dimension_keys
FROM core.fact_sales f
JOIN core.dim_store d
    ON d.store_key = f.store_key

UNION ALL

SELECT
    'Sales → Products',
    COUNT(DISTINCT f.product_key),
    COUNT(DISTINCT d.product_key)
FROM core.fact_sales f
JOIN core.dim_product d
    ON d.product_key = f.product_key

UNION ALL

SELECT
    'Inventory → Stores',
    COUNT(DISTINCT f.store_key),
    COUNT(DISTINCT d.store_key)
FROM core.fact_inventory f
JOIN core.dim_store d
    ON d.store_key = f.store_key

UNION ALL

SELECT
    'Inventory → Products',
    COUNT(DISTINCT f.product_key),
    COUNT(DISTINCT d.product_key)
FROM core.fact_inventory f
JOIN core.dim_product d
    ON d.product_key = f.product_key;


-- ============================================================
-- 20. PRODUCT ATTRIBUTE COMPLETENESS
-- ============================================================

SELECT
    COUNT(*) AS total_products,
    COUNT(*) FILTER (WHERE product_description IS NULL) AS missing_description,
    COUNT(*) FILTER (WHERE product_division IS NULL) AS missing_division,
    COUNT(*) FILTER (WHERE product_category IS NULL) AS missing_category,
    COUNT(*) FILTER (WHERE product_subcategory IS NULL) AS missing_subcategory,
    COUNT(*) FILTER (WHERE product_segment IS NULL) AS missing_segment,
    COUNT(*) FILTER (WHERE supplier_key IS NULL) AS missing_supplier
FROM core.dim_product;


-- ============================================================
-- 21. STORE ATTRIBUTE COMPLETENESS
-- ============================================================

SELECT
    COUNT(*) AS total_stores,
    COUNT(*) FILTER (WHERE store_type IS NULL) AS missing_store_type,
    COUNT(*) FILTER (WHERE first_seen_date IS NULL) AS missing_first_seen_date,
    COUNT(*) FILTER (WHERE last_seen_date IS NULL) AS missing_last_seen_date
FROM core.dim_store;


-- ============================================================
-- 22. SUPPLIER ATTRIBUTE COMPLETENESS
-- ============================================================

SELECT
    COUNT(*) AS total_suppliers,
    COUNT(*) FILTER (WHERE supplier_name IS NULL) AS missing_supplier_name
FROM core.dim_supplier;


-- ============================================================
-- 23. BUSINESS METRIC RECONCILIATION
-- ============================================================

SELECT
    'Sales Amount' AS metric,
    (SELECT COALESCE(SUM(sales_amount), 0)
     FROM staging.sales_raw) AS staging_value,
    (SELECT COALESCE(SUM(sales_amount), 0)
     FROM core.fact_sales) AS core_value,
    (SELECT COALESCE(SUM(sales_amount), 0)
     FROM staging.sales_raw)
    -
    (SELECT COALESCE(SUM(sales_amount), 0)
     FROM core.fact_sales) AS difference

UNION ALL

SELECT
    'COGS',
    (SELECT COALESCE(SUM(cogs), 0)
     FROM staging.sales_raw),
    (SELECT COALESCE(SUM(cogs), 0)
     FROM core.fact_sales),
    (SELECT COALESCE(SUM(cogs), 0)
     FROM staging.sales_raw)
    -
    (SELECT COALESCE(SUM(cogs), 0)
     FROM core.fact_sales)

UNION ALL

SELECT
    'Quantity Sold',
    (SELECT COALESCE(SUM(qty_sold), 0)
     FROM staging.sales_raw),
    (SELECT COALESCE(SUM(qty_sold), 0)
     FROM core.fact_sales),
    (SELECT COALESCE(SUM(qty_sold), 0)
     FROM staging.sales_raw)
    -
    (SELECT COALESCE(SUM(qty_sold), 0)
     FROM core.fact_sales);


-- ============================================================
-- 24. INVENTORY METRIC RECONCILIATION
-- ============================================================

SELECT
    'Quantity on Hand' AS metric,
    (SELECT COALESCE(SUM(qty_on_hand), 0)
     FROM staging.inventory_raw) AS staging_value,
    (SELECT COALESCE(SUM(qty_on_hand), 0)
     FROM core.fact_inventory) AS core_value,
    (SELECT COALESCE(SUM(qty_on_hand), 0)
     FROM staging.inventory_raw)
    -
    (SELECT COALESCE(SUM(qty_on_hand), 0)
     FROM core.fact_inventory) AS difference

UNION ALL

SELECT
    'Stock Selling Amount',
    (SELECT COALESCE(SUM(stocks_selling_amount), 0)
     FROM staging.inventory_raw),
    (SELECT COALESCE(SUM(stocks_selling_amount), 0)
     FROM core.fact_inventory),
    (SELECT COALESCE(SUM(stocks_selling_amount), 0)
     FROM staging.inventory_raw)
    -
    (SELECT COALESCE(SUM(stocks_selling_amount), 0)
     FROM core.fact_inventory)

UNION ALL

SELECT
    'Cost of Stocks',
    (SELECT COALESCE(SUM(cost_of_stocks), 0)
     FROM staging.inventory_raw),
    (SELECT COALESCE(SUM(cost_of_stocks), 0)
     FROM core.fact_inventory),
    (SELECT COALESCE(SUM(cost_of_stocks), 0)
     FROM staging.inventory_raw)
    -
    (SELECT COALESCE(SUM(cost_of_stocks), 0)
     FROM core.fact_inventory);


-- ============================================================
-- 25. FINAL CORE VALIDATION SUMMARY
-- ============================================================

SELECT
    'Sales row reconciliation' AS validation_check,
    CASE
        WHEN (SELECT COUNT(*) FROM staging.sales_raw)
           = (SELECT COUNT(*) FROM core.fact_sales)
        THEN 'PASS'
        ELSE 'FAIL'
    END AS status

UNION ALL

SELECT
    'Inventory row reconciliation',
    CASE
        WHEN (SELECT COUNT(*) FROM staging.inventory_raw)
           = (SELECT COUNT(*) FROM core.fact_inventory)
        THEN 'PASS'
        ELSE 'FAIL'
    END

UNION ALL

SELECT
    'Date dimension continuity',
    CASE
        WHEN (
            SELECT COUNT(*) - (MAX(full_date) - MIN(full_date) + 1)
            FROM core.dim_date
        ) = 0
        THEN 'PASS'
        ELSE 'FAIL'
    END

UNION ALL

SELECT
    'Sales orphan dates',
    CASE
        WHEN NOT EXISTS (
            SELECT 1
            FROM core.fact_sales f
            LEFT JOIN core.dim_date d
                ON d.date_key = f.date_key
            WHERE d.date_key IS NULL
        )
        THEN 'PASS'
        ELSE 'FAIL'
    END

UNION ALL

SELECT
    'Sales orphan products',
    CASE
        WHEN NOT EXISTS (
            SELECT 1
            FROM core.fact_sales f
            LEFT JOIN core.dim_product d
                ON d.product_key = f.product_key
            WHERE d.product_key IS NULL
        )
        THEN 'PASS'
        ELSE 'FAIL'
    END

UNION ALL

SELECT
    'Sales orphan stores',
    CASE
        WHEN NOT EXISTS (
            SELECT 1
            FROM core.fact_sales f
            LEFT JOIN core.dim_store d
                ON d.store_key = f.store_key
            WHERE d.store_key IS NULL
        )
        THEN 'PASS'
        ELSE 'FAIL'
    END

UNION ALL

SELECT
    'Inventory orphan products',
    CASE
        WHEN NOT EXISTS (
            SELECT 1
            FROM core.fact_inventory f
            LEFT JOIN core.dim_product d
                ON d.product_key = f.product_key
            WHERE d.product_key IS NULL
        )
        THEN 'PASS'
        ELSE 'FAIL'
    END

UNION ALL

SELECT
    'Inventory orphan stores',
    CASE
        WHEN NOT EXISTS (
            SELECT 1
            FROM core.fact_inventory f
            LEFT JOIN core.dim_store d
                ON d.store_key = f.store_key
            WHERE d.store_key IS NULL
        )
        THEN 'PASS'
        ELSE 'FAIL'
    END

UNION ALL

SELECT
    'Inventory date intervals',
    CASE
        WHEN NOT EXISTS (
            SELECT 1
            FROM core.fact_inventory
            WHERE end_date IS NOT NULL
              AND end_date < start_date
        )
        THEN 'PASS'
        ELSE 'FAIL'
    END

UNION ALL

SELECT
    'Open-ended inventory mapping',
    CASE
        WHEN (
            SELECT COUNT(*)
            FROM staging.inventory_raw
            WHERE end_date = DATE '9999-12-31'
        ) = (
            SELECT COUNT(*)
            FROM core.fact_inventory
            WHERE is_open_ended = TRUE
        )
        THEN 'PASS'
        ELSE 'FAIL'
    END

UNION ALL

SELECT
    'Sales amount reconciliation',
    CASE
        WHEN ABS(
            (SELECT COALESCE(SUM(sales_amount), 0)
             FROM staging.sales_raw)
            -
            (SELECT COALESCE(SUM(sales_amount), 0)
             FROM core.fact_sales)
        ) < 0.01
        THEN 'PASS'
        ELSE 'FAIL'
    END

UNION ALL

SELECT
    'Inventory cost reconciliation',
    CASE
        WHEN ABS(
            (SELECT COALESCE(SUM(cost_of_stocks), 0)
             FROM staging.inventory_raw)
            -
            (SELECT COALESCE(SUM(cost_of_stocks), 0)
             FROM core.fact_inventory)
        ) < 0.01
        THEN 'PASS'
        ELSE 'FAIL'
    END

ORDER BY validation_check;