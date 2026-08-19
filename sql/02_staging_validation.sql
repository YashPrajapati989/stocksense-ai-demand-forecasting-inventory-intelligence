-- StockSense AI
-- Phase 3 - PostgreSQL Data Architecture
-- Step 2: Staging Layer Validation
-- READ-ONLY: validates staging.sales_raw and staging.inventory_raw

-- 1. Row counts
SELECT 'sales_raw' AS table_name, COUNT(*) AS row_count
FROM staging.sales_raw
UNION ALL
SELECT 'inventory_raw', COUNT(*)
FROM staging.inventory_raw;

-- 2. Sales completeness
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE transaction_date IS NULL) AS missing_transaction_date,
    COUNT(*) FILTER (WHERE sales_type IS NULL) AS missing_sales_type,
    COUNT(*) FILTER (WHERE is_return IS NULL) AS missing_return_flag,
    COUNT(*) FILTER (WHERE supplier IS NULL) AS missing_supplier,
    COUNT(*) FILTER (WHERE product_no IS NULL) AS missing_product,
    COUNT(*) FILTER (WHERE store IS NULL) AS missing_store,
    COUNT(*) FILTER (WHERE sales_channel IS NULL) AS missing_sales_channel,
    COUNT(*) FILTER (WHERE qty_sold IS NULL) AS missing_qty_sold,
    COUNT(*) FILTER (WHERE sales_amount IS NULL) AS missing_sales_amount,
    COUNT(*) FILTER (WHERE cogs IS NULL) AS missing_cogs
FROM staging.sales_raw;

-- 3. Inventory completeness
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE start_date IS NULL) AS missing_start_date,
    COUNT(*) FILTER (WHERE end_date IS NULL) AS missing_end_date,
    COUNT(*) FILTER (WHERE stock_status IS NULL) AS missing_stock_status,
    COUNT(*) FILTER (WHERE supplier IS NULL) AS missing_supplier,
    COUNT(*) FILTER (WHERE product_no IS NULL) AS missing_product,
    COUNT(*) FILTER (WHERE store IS NULL) AS missing_store,
    COUNT(*) FILTER (WHERE store_type IS NULL) AS missing_store_type,
    COUNT(*) FILTER (WHERE sales_channel IS NULL) AS missing_sales_channel,
    COUNT(*) FILTER (WHERE qty_on_hand IS NULL) AS missing_qty_on_hand,
    COUNT(*) FILTER (WHERE stocks_selling_amount IS NULL) AS missing_selling_amount,
    COUNT(*) FILTER (WHERE cost_of_stocks IS NULL) AS missing_cost_of_stocks
FROM staging.inventory_raw;

-- 4. Date ranges
SELECT MIN(transaction_date) AS earliest_transaction_date,
       MAX(transaction_date) AS latest_transaction_date,
       COUNT(DISTINCT transaction_date) AS distinct_transaction_dates
FROM staging.sales_raw;

SELECT MIN(start_date) AS earliest_start_date,
       MAX(start_date) AS latest_start_date,
       MIN(end_date) AS earliest_end_date,
       MAX(end_date) AS latest_end_date
FROM staging.inventory_raw;



-- 5. Inventory date integrity
SELECT COUNT(*) AS open_ended_inventory_records
FROM staging.inventory_raw
WHERE end_date = DATE '9999-12-31';

SELECT COUNT(*) AS end_before_start
FROM staging.inventory_raw
WHERE end_date < start_date;

SELECT COUNT(*) AS same_day_inventory_intervals
FROM staging.inventory_raw
WHERE end_date = start_date;



-- 6. Exact duplicates
SELECT COUNT(*) AS exact_duplicate_rows
FROM (
    SELECT transaction_date, sales_type, is_return, reason_of_return,
           supplier, product_no, product_description, product_division,
           product_category, product_subcategory, product_segment,
           store, sales_channel, qty_sold, sales_amount, cogs,
           number_of_transactions
    FROM staging.sales_raw
    GROUP BY transaction_date, sales_type, is_return, reason_of_return,
             supplier, product_no, product_description, product_division,
             product_category, product_subcategory, product_segment,
             store, sales_channel, qty_sold, sales_amount, cogs,
             number_of_transactions
    HAVING COUNT(*) > 1
) d;

SELECT COUNT(*) AS exact_duplicate_rows
FROM (
    SELECT start_date, end_date, stock_status, supplier, product_no,
           product_description, product_division, product_category,
           product_subcategory, product_segment, store, store_type,
           sales_channel, qty_on_hand, stocks_selling_amount,
           cost_of_stocks, stock_unit_selling_price, stock_unit_cost_price
    FROM staging.inventory_raw
    GROUP BY start_date, end_date, stock_status, supplier, product_no,
             product_description, product_division, product_category,
             product_subcategory, product_segment, store, store_type,
             sales_channel, qty_on_hand, stocks_selling_amount,
             cost_of_stocks, stock_unit_selling_price, stock_unit_cost_price
    HAVING COUNT(*) > 1
) d;



-- 7. Sales quantity / returns
SELECT
    COUNT(*) FILTER (WHERE qty_sold < 0) AS negative_qty_sold,
    COUNT(*) FILTER (WHERE qty_sold = 0) AS zero_qty_sold,
    COUNT(*) FILTER (WHERE qty_sold > 0) AS positive_qty_sold
FROM staging.sales_raw;

SELECT
    is_return,
    COUNT(*) AS record_count,
    SUM(qty_sold) AS total_qty_sold,
    SUM(sales_amount) AS total_sales_amount
FROM staging.sales_raw
GROUP BY is_return
ORDER BY is_return;

SELECT
    COUNT(*) FILTER (
        WHERE is_return = TRUE
          AND NULLIF(TRIM(reason_of_return), '') IS NULL
    ) AS returns_without_reason,
    COUNT(*) FILTER (
        WHERE is_return = FALSE
          AND NULLIF(TRIM(reason_of_return), '') IS NOT NULL
    ) AS non_returns_with_reason
FROM staging.sales_raw;



-- 8. Inventory quantity / price checks
SELECT
    COUNT(*) FILTER (WHERE qty_on_hand < 0) AS negative_qty_on_hand,
    COUNT(*) FILTER (WHERE qty_on_hand = 0) AS zero_qty_on_hand,
    COUNT(*) FILTER (WHERE qty_on_hand > 0) AS positive_qty_on_hand
FROM staging.inventory_raw;

SELECT
    COUNT(*) FILTER (WHERE stock_unit_selling_price < 0) AS negative_selling_price,
    COUNT(*) FILTER (WHERE stock_unit_cost_price < 0) AS negative_cost_price,
    COUNT(*) FILTER (WHERE stock_unit_selling_price = 0) AS zero_selling_price,
    COUNT(*) FILTER (WHERE stock_unit_cost_price = 0) AS zero_cost_price
FROM staging.inventory_raw;



-- 9. Financial reconciliation
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE ABS(stocks_selling_amount -
                  (qty_on_hand * stock_unit_selling_price)) > 0.01
    ) AS selling_value_mismatch,
    COUNT(*) FILTER (
        WHERE ABS(cost_of_stocks -
                  (qty_on_hand * stock_unit_cost_price)) > 0.01
    ) AS cost_value_mismatch
FROM staging.inventory_raw;

SELECT
    COUNT(*) FILTER (WHERE sales_amount < 0) AS negative_sales_amount,
    COUNT(*) FILTER (WHERE cogs < 0) AS negative_cogs
FROM staging.sales_raw;



-- 10. Store × Product × Date repeated keys
SELECT
    transaction_date,
    store,
    product_no,
    COUNT(*) AS record_count
FROM staging.sales_raw
GROUP BY transaction_date, store, product_no
HAVING COUNT(*) > 1
ORDER BY record_count DESC
LIMIT 50;



-- 11. Store × Product coverage
WITH sales_keys AS (
    SELECT DISTINCT store, product_no FROM staging.sales_raw
),
inventory_keys AS (
    SELECT DISTINCT store, product_no FROM staging.inventory_raw
)
SELECT
    CASE
        WHEN s.store IS NOT NULL AND i.store IS NOT NULL
            THEN 'Both Sales and Inventory'
        WHEN s.store IS NOT NULL AND i.store IS NULL
            THEN 'Sales Only'
        WHEN s.store IS NULL AND i.store IS NOT NULL
            THEN 'Inventory Only'
    END AS coverage_status,
    COUNT(*) AS store_product_combinations
FROM sales_keys s
FULL OUTER JOIN inventory_keys i
    ON s.store = i.store AND s.product_no = i.product_no
GROUP BY 1
ORDER BY 1;



-- 12. Dimension coverage
SELECT 'Stores' AS dimension,
       (SELECT COUNT(DISTINCT store) FROM staging.sales_raw) AS sales_count,
       (SELECT COUNT(DISTINCT store) FROM staging.inventory_raw) AS inventory_count
UNION ALL
SELECT 'Products',
       (SELECT COUNT(DISTINCT product_no) FROM staging.sales_raw),
       (SELECT COUNT(DISTINCT product_no) FROM staging.inventory_raw)
UNION ALL
SELECT 'Suppliers',
       (SELECT COUNT(DISTINCT supplier) FROM staging.sales_raw),
       (SELECT COUNT(DISTINCT supplier) FROM staging.inventory_raw)
UNION ALL
SELECT 'Sales Channels',
       (SELECT COUNT(DISTINCT sales_channel) FROM staging.sales_raw),
       (SELECT COUNT(DISTINCT sales_channel) FROM staging.inventory_raw);



-- 13. Business distributions
SELECT sales_type, COUNT(*) AS records,
       SUM(qty_sold) AS qty_sold,
       SUM(sales_amount) AS sales_amount
FROM staging.sales_raw
GROUP BY sales_type
ORDER BY records DESC;

SELECT stock_status, COUNT(*) AS records,
       SUM(qty_on_hand) AS total_qty_on_hand,
       SUM(stocks_selling_amount) AS total_stock_selling_value,
       SUM(cost_of_stocks) AS total_stock_cost
FROM staging.inventory_raw
GROUP BY stock_status
ORDER BY records DESC;



-- 14. Final one-screen validation summary
SELECT 'Sales row count' AS validation_check,
       COUNT(*)::TEXT AS result
FROM staging.sales_raw
UNION ALL
SELECT 'Inventory row count', COUNT(*)::TEXT
FROM staging.inventory_raw
UNION ALL
SELECT 'Sales missing transaction dates', COUNT(*)::TEXT
FROM staging.sales_raw WHERE transaction_date IS NULL
UNION ALL
SELECT 'Inventory invalid date intervals', COUNT(*)::TEXT
FROM staging.inventory_raw WHERE end_date < start_date
UNION ALL
SELECT 'Sales negative quantities', COUNT(*)::TEXT
FROM staging.sales_raw WHERE qty_sold < 0
UNION ALL
SELECT 'Inventory negative quantities', COUNT(*)::TEXT
FROM staging.inventory_raw WHERE qty_on_hand < 0
UNION ALL
SELECT 'Open-ended inventory records', COUNT(*)::TEXT
FROM staging.inventory_raw WHERE end_date = DATE '9999-12-31';