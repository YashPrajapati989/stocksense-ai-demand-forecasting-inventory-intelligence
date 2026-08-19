-- ============================================================
-- StockSense AI
-- Phase 3 - PostgreSQL Data Architecture
-- ============================================================

CREATE SCHEMA IF NOT EXISTS analytics;


-- ============================================================
-- 1. DAILY SALES PERFORMANCE
-- ============================================================

DROP VIEW IF EXISTS analytics.vw_daily_sales CASCADE;

CREATE VIEW analytics.vw_daily_sales AS
SELECT
    d.full_date AS sales_date,
    d.year,
    d.quarter,
    d.month_number,
    d.month_name,
    d.month_short,
    d.week_of_year,
    d.day_name,
    d.is_weekend,

    COUNT(*) AS sales_records,

    COUNT(DISTINCT f.store_key) AS active_stores,
    COUNT(DISTINCT f.product_key) AS active_products,

    SUM(COALESCE(f.qty_sold, 0)) AS units_sold,

    SUM(COALESCE(f.sales_amount, 0)) AS revenue,

    SUM(COALESCE(f.cogs, 0)) AS cogs,

    SUM(
        COALESCE(f.sales_amount, 0)
        - COALESCE(f.cogs, 0)
    ) AS gross_profit,

    CASE
        WHEN SUM(COALESCE(f.sales_amount, 0)) = 0
            THEN 0
        ELSE
            SUM(
                COALESCE(f.sales_amount, 0)
                - COALESCE(f.cogs, 0)
            )
            /
            SUM(COALESCE(f.sales_amount, 0))
    END AS gross_margin,

    SUM(COALESCE(f.number_of_transactions, 0))
        AS transactions,

    COUNT(*) FILTER (
        WHERE f.is_return = TRUE
    ) AS return_records,

    SUM(
        CASE
            WHEN f.is_return = TRUE
                THEN COALESCE(f.qty_sold, 0)
            ELSE 0
        END
    ) AS returned_units

FROM core.fact_sales f
JOIN core.dim_date d
    ON d.date_key = f.date_key

GROUP BY
    d.full_date,
    d.year,
    d.quarter,
    d.month_number,
    d.month_name,
    d.month_short,
    d.week_of_year,
    d.day_name,
    d.is_weekend;


-- ============================================================
-- 2. MONTHLY SALES PERFORMANCE
-- ============================================================

DROP VIEW IF EXISTS analytics.vw_monthly_sales CASCADE;

CREATE VIEW analytics.vw_monthly_sales AS
SELECT
    d.year,
    d.month_number,
    d.month_name,

    DATE_TRUNC(
        'month',
        d.full_date
    )::DATE AS month_start,

    COUNT(*) AS sales_records,

    COUNT(DISTINCT f.store_key) AS active_stores,

    COUNT(DISTINCT f.product_key) AS active_products,

    SUM(COALESCE(f.qty_sold, 0)) AS units_sold,

    SUM(COALESCE(f.sales_amount, 0)) AS revenue,

    SUM(COALESCE(f.cogs, 0)) AS cogs,

    SUM(
        COALESCE(f.sales_amount, 0)
        - COALESCE(f.cogs, 0)
    ) AS gross_profit,

    CASE
        WHEN SUM(COALESCE(f.sales_amount, 0)) = 0
            THEN 0
        ELSE
            SUM(
                COALESCE(f.sales_amount, 0)
                - COALESCE(f.cogs, 0)
            )
            /
            SUM(COALESCE(f.sales_amount, 0))
    END AS gross_margin,

    SUM(
        COALESCE(f.number_of_transactions, 0)
    ) AS transactions,

    COUNT(*) FILTER (
        WHERE f.is_return = TRUE
    ) AS return_records

FROM core.fact_sales f
JOIN core.dim_date d
    ON d.date_key = f.date_key

GROUP BY
    d.year,
    d.month_number,
    d.month_name,
    DATE_TRUNC(
        'month',
        d.full_date
    )::DATE;


-- ============================================================
-- 3. PRODUCT PERFORMANCE
-- ============================================================

DROP VIEW IF EXISTS analytics.vw_product_performance CASCADE;

CREATE VIEW analytics.vw_product_performance AS
SELECT
    p.product_key,
    p.product_no,
    p.product_description,

    p.product_division,
    p.product_category,
    p.product_subcategory,
    p.product_segment,

    s.supplier_key,
    s.supplier_name,

    COUNT(f.sales_key) AS sales_records,

    COUNT(DISTINCT f.store_key) AS stores_selling,

    MIN(f.transaction_date) AS first_sale_date,
    MAX(f.transaction_date) AS last_sale_date,

    SUM(COALESCE(f.qty_sold, 0)) AS units_sold,

    SUM(COALESCE(f.sales_amount, 0)) AS revenue,

    SUM(COALESCE(f.cogs, 0)) AS cogs,

    SUM(
        COALESCE(f.sales_amount, 0)
        - COALESCE(f.cogs, 0)
    ) AS gross_profit,

    CASE
        WHEN SUM(COALESCE(f.sales_amount, 0)) = 0
            THEN 0
        ELSE
            SUM(
                COALESCE(f.sales_amount, 0)
                - COALESCE(f.cogs, 0)
            )
            /
            SUM(COALESCE(f.sales_amount, 0))
    END AS gross_margin,

    SUM(
        COALESCE(f.number_of_transactions, 0)
    ) AS transactions,

    COUNT(*) FILTER (
        WHERE f.is_return = TRUE
    ) AS return_records,

    SUM(
        CASE
            WHEN f.is_return = TRUE
                THEN COALESCE(f.qty_sold, 0)
            ELSE 0
        END
    ) AS returned_units

FROM core.dim_product p

LEFT JOIN core.fact_sales f
    ON f.product_key = p.product_key

LEFT JOIN core.dim_supplier s
    ON s.supplier_key = p.supplier_key

GROUP BY
    p.product_key,
    p.product_no,
    p.product_description,
    p.product_division,
    p.product_category,
    p.product_subcategory,
    p.product_segment,
    s.supplier_key,
    s.supplier_name;


-- ============================================================
-- 4. STORE PERFORMANCE
-- ============================================================

DROP VIEW IF EXISTS analytics.vw_store_performance CASCADE;

CREATE VIEW analytics.vw_store_performance AS
SELECT
    st.store_key,
    st.store_id,
    st.store_type,

    COUNT(f.sales_key) AS sales_records,

    COUNT(DISTINCT f.product_key) AS products_sold,

    MIN(f.transaction_date) AS first_sale_date,
    MAX(f.transaction_date) AS last_sale_date,

    SUM(COALESCE(f.qty_sold, 0)) AS units_sold,

    SUM(COALESCE(f.sales_amount, 0)) AS revenue,

    SUM(COALESCE(f.cogs, 0)) AS cogs,

    SUM(
        COALESCE(f.sales_amount, 0)
        - COALESCE(f.cogs, 0)
    ) AS gross_profit,

    CASE
        WHEN SUM(COALESCE(f.sales_amount, 0)) = 0
            THEN 0
        ELSE
            SUM(
                COALESCE(f.sales_amount, 0)
                - COALESCE(f.cogs, 0)
            )
            /
            SUM(COALESCE(f.sales_amount, 0))
    END AS gross_margin,

    SUM(
        COALESCE(f.number_of_transactions, 0)
    ) AS transactions,

    COUNT(*) FILTER (
        WHERE f.is_return = TRUE
    ) AS return_records

FROM core.dim_store st

LEFT JOIN core.fact_sales f
    ON f.store_key = st.store_key

GROUP BY
    st.store_key,
    st.store_id,
    st.store_type;


-- ============================================================
-- 5. SUPPLIER PERFORMANCE
-- ============================================================

DROP VIEW IF EXISTS analytics.vw_supplier_performance CASCADE;

CREATE VIEW analytics.vw_supplier_performance AS
SELECT
    s.supplier_key,
    s.supplier_id,
    s.supplier_name,

    COUNT(DISTINCT p.product_key) AS products_supplied,

    COUNT(DISTINCT f.store_key) AS stores_served,

    SUM(COALESCE(f.qty_sold, 0)) AS units_sold,

    SUM(COALESCE(f.sales_amount, 0)) AS revenue,

    SUM(COALESCE(f.cogs, 0)) AS cogs,

    SUM(
        COALESCE(f.sales_amount, 0)
        - COALESCE(f.cogs, 0)
    ) AS gross_profit,

    CASE
        WHEN SUM(COALESCE(f.sales_amount, 0)) = 0
            THEN 0
        ELSE
            SUM(
                COALESCE(f.sales_amount, 0)
                - COALESCE(f.cogs, 0)
            )
            /
            SUM(COALESCE(f.sales_amount, 0))
    END AS gross_margin

FROM core.dim_supplier s

LEFT JOIN core.dim_product p
    ON p.supplier_key = s.supplier_key

LEFT JOIN core.fact_sales f
    ON f.supplier_key = s.supplier_key

GROUP BY
    s.supplier_key,
    s.supplier_id,
    s.supplier_name;


-- ============================================================
-- 6. CURRENT INVENTORY POSITION
-- ============================================================

DROP VIEW IF EXISTS analytics.vw_inventory_position CASCADE;

CREATE VIEW analytics.vw_inventory_position AS

WITH ranked_inventory AS (
    SELECT
        f.*,

        ROW_NUMBER() OVER (
            PARTITION BY
                f.store_key,
                f.product_key

            ORDER BY
                f.start_date DESC,
                f.inventory_key DESC
        ) AS rn

    FROM core.fact_inventory f
)

SELECT
    i.inventory_key,

    st.store_key,
    st.store_id,
    st.store_type,

    p.product_key,
    p.product_no,
    p.product_description,

    p.product_division,
    p.product_category,
    p.product_subcategory,
    p.product_segment,

    s.supplier_key,
    s.supplier_name,

    i.start_date,
    i.end_date,
    i.is_open_ended,

    i.stock_status,
    i.sales_channel,

    i.qty_on_hand,

    i.stocks_selling_amount,
    i.cost_of_stocks,

    i.stock_unit_selling_price,
    i.stock_unit_cost_price

FROM ranked_inventory i

JOIN core.dim_store st
    ON st.store_key = i.store_key

JOIN core.dim_product p
    ON p.product_key = i.product_key

LEFT JOIN core.dim_supplier s
    ON s.supplier_key = i.supplier_key

WHERE i.rn = 1;


-- ============================================================
-- 7. INVENTORY RISK
-- ============================================================

-- Days of cover:
--   Current Stock / Average Daily Units Sold
-- ============================================================

DROP VIEW IF EXISTS analytics.vw_inventory_risk CASCADE;

CREATE VIEW analytics.vw_inventory_risk AS

WITH inventory AS (
    SELECT *
    FROM analytics.vw_inventory_position
),

sales_30d AS (
    SELECT
        f.store_key,
        f.product_key,

        SUM(COALESCE(f.qty_sold, 0)) AS units_sold_30d,

        SUM(COALESCE(f.sales_amount, 0)) AS revenue_30d

    FROM core.fact_sales f

    WHERE f.transaction_date >= (
        SELECT MAX(transaction_date)
        FROM core.fact_sales
    ) - INTERVAL '29 days'

    GROUP BY
        f.store_key,
        f.product_key
)

SELECT
    i.*,

    COALESCE(s.units_sold_30d, 0) AS units_sold_30d,

    COALESCE(s.revenue_30d, 0) AS revenue_30d,

    COALESCE(s.units_sold_30d, 0) / 30.0
        AS average_daily_units_sold,

    CASE
        WHEN COALESCE(s.units_sold_30d, 0) <= 0
            THEN NULL

        ELSE
            i.qty_on_hand
            /
            (s.units_sold_30d / 30.0)
    END AS estimated_days_of_cover,

    CASE

        WHEN COALESCE(i.qty_on_hand, 0) <= 0
            THEN 'OUT_OF_STOCK'

        WHEN COALESCE(s.units_sold_30d, 0) <= 0
            THEN 'NO_RECENT_DEMAND'

        WHEN
            i.qty_on_hand
            /
            (s.units_sold_30d / 30.0)
            <= 7
            THEN 'CRITICAL'

        WHEN
            i.qty_on_hand
            /
            (s.units_sold_30d / 30.0)
            <= 14
            THEN 'HIGH'

        WHEN
            i.qty_on_hand
            /
            (s.units_sold_30d / 30.0)
            <= 30
            THEN 'MEDIUM'

        ELSE 'HEALTHY'

    END AS inventory_risk

FROM inventory i

LEFT JOIN sales_30d s
    ON s.store_key = i.store_key
   AND s.product_key = i.product_key;


-- ============================================================
-- 8. SLOW-MOVING PRODUCTS
-- ============================================================
-- Identifies products with inventory but weak recent demand.

DROP VIEW IF EXISTS analytics.vw_slow_moving_products CASCADE;

CREATE VIEW analytics.vw_slow_moving_products AS

SELECT
    r.store_id,
    r.store_type,

    r.product_no,
    r.product_description,

    r.product_category,
    r.product_subcategory,
    r.product_segment,

    r.supplier_name,

    r.qty_on_hand,

    r.cost_of_stocks,
    r.stocks_selling_amount,

    r.units_sold_30d,
    r.average_daily_units_sold,

    r.estimated_days_of_cover,

    CASE
        WHEN r.units_sold_30d = 0
            THEN 'NO_SALES_30D'

        WHEN r.units_sold_30d <= 5
            THEN 'VERY_SLOW'

        WHEN r.units_sold_30d <= 15
            THEN 'SLOW'

        ELSE 'NORMAL'
    END AS movement_class

FROM analytics.vw_inventory_risk r

WHERE
    r.qty_on_hand > 0
    AND r.units_sold_30d <= 15;


-- ============================================================
-- 9. ABC PRODUCT CLASSIFICATION
-- ============================================================
-- ABC classification based on cumulative revenue contribution.
--
-- A = first 80%
-- B = next 15%
-- C = remaining 5%
--
-- This is calculated across the total sales history.

DROP VIEW IF EXISTS analytics.vw_abc_product_classification CASCADE;

CREATE VIEW analytics.vw_abc_product_classification AS

WITH product_revenue AS (
    SELECT
        p.product_key,
        p.product_no,
        p.product_description,

        p.product_category,
        p.product_subcategory,
        p.product_segment,

        SUM(COALESCE(f.sales_amount, 0))
            AS revenue

    FROM core.dim_product p

    LEFT JOIN core.fact_sales f
        ON f.product_key = p.product_key

    GROUP BY
        p.product_key,
        p.product_no,
        p.product_description,
        p.product_category,
        p.product_subcategory,
        p.product_segment
),

ranked AS (
    SELECT
        *,

        SUM(revenue) OVER ()
            AS total_revenue,

        SUM(revenue) OVER (
            ORDER BY revenue DESC, product_no
            ROWS BETWEEN UNBOUNDED PRECEDING
                 AND CURRENT ROW
        ) AS cumulative_revenue

    FROM product_revenue
)

SELECT
    product_key,
    product_no,
    product_description,

    product_category,
    product_subcategory,
    product_segment,

    revenue,

    CASE
        WHEN total_revenue = 0
            THEN 0
        ELSE cumulative_revenue / total_revenue
    END AS cumulative_revenue_pct,

    CASE
        WHEN total_revenue = 0
            THEN 'C'

        WHEN cumulative_revenue / total_revenue <= 0.80
            THEN 'A'

        WHEN cumulative_revenue / total_revenue <= 0.95
            THEN 'B'

        ELSE 'C'
    END AS abc_class

FROM ranked;


-- ============================================================
-- 10. DEMAND FEATURES
-- ============================================================

DROP VIEW IF EXISTS analytics.vw_demand_features CASCADE;

CREATE VIEW analytics.vw_demand_features AS

WITH daily AS (
    SELECT
        d.full_date AS sales_date,

        f.store_key,
        f.product_key,

        SUM(COALESCE(f.qty_sold, 0))
            AS units_sold,

        SUM(COALESCE(f.sales_amount, 0))
            AS revenue,

        SUM(COALESCE(f.cogs, 0))
            AS cogs,

        SUM(
            CASE
                WHEN f.is_return = TRUE
                    THEN COALESCE(f.qty_sold, 0)
                ELSE 0
            END
        ) AS returned_units,

        SUM(
            COALESCE(f.number_of_transactions, 0)
        ) AS transactions

    FROM core.fact_sales f

    JOIN core.dim_date d
        ON d.date_key = f.date_key

    GROUP BY
        d.full_date,
        f.store_key,
        f.product_key
),

features AS (
    SELECT
        *,

        AVG(units_sold) OVER (
            PARTITION BY store_key, product_key
            ORDER BY sales_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS avg_daily_units_7d,

        AVG(units_sold) OVER (
            PARTITION BY store_key, product_key
            ORDER BY sales_date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS avg_daily_units_30d,

        SUM(units_sold) OVER (
            PARTITION BY store_key, product_key
            ORDER BY sales_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS units_sold_7d,

        SUM(units_sold) OVER (
            PARTITION BY store_key, product_key
            ORDER BY sales_date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS units_sold_30d,

        SUM(revenue) OVER (
            PARTITION BY store_key, product_key
            ORDER BY sales_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS revenue_7d,

        SUM(revenue) OVER (
            PARTITION BY store_key, product_key
            ORDER BY sales_date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS revenue_30d

    FROM daily
)

SELECT
    f.sales_date,

    f.store_key,
    st.store_id,
    st.store_type,

    f.product_key,
    p.product_no,
    p.product_description,

    p.product_division,
    p.product_category,
    p.product_subcategory,
    p.product_segment,

    f.units_sold,
    f.revenue,
    f.cogs,
    f.returned_units,
    f.transactions,

    f.avg_daily_units_7d,
    f.avg_daily_units_30d,

    f.units_sold_7d,
    f.units_sold_30d,

    f.revenue_7d,
    f.revenue_30d

FROM features f

JOIN core.dim_store st
    ON st.store_key = f.store_key

JOIN core.dim_product p
    ON p.product_key = f.product_key;


-- ============================================================
-- 11. ANALYTICS VIEW INVENTORY
-- ============================================================

SELECT
    table_schema,
    table_name
FROM information_schema.views
WHERE table_schema = 'analytics'
ORDER BY table_name;


-- ============================================================
-- 12. BASIC VIEW ROW COUNTS
-- ============================================================

SELECT
    'vw_daily_sales' AS view_name,
    COUNT(*) AS row_count
FROM analytics.vw_daily_sales

UNION ALL

SELECT
    'vw_monthly_sales',
    COUNT(*)
FROM analytics.vw_monthly_sales

UNION ALL

SELECT
    'vw_product_performance',
    COUNT(*)
FROM analytics.vw_product_performance

UNION ALL

SELECT
    'vw_store_performance',
    COUNT(*)
FROM analytics.vw_store_performance

UNION ALL

SELECT
    'vw_supplier_performance',
    COUNT(*)
FROM analytics.vw_supplier_performance

UNION ALL

SELECT
    'vw_inventory_position',
    COUNT(*)
FROM analytics.vw_inventory_position

UNION ALL

SELECT
    'vw_inventory_risk',
    COUNT(*)
FROM analytics.vw_inventory_risk

UNION ALL

SELECT
    'vw_slow_moving_products',
    COUNT(*)
FROM analytics.vw_slow_moving_products

UNION ALL

SELECT
    'vw_abc_product_classification',
    COUNT(*)
FROM analytics.vw_abc_product_classification

UNION ALL

SELECT
    'vw_demand_features',
    COUNT(*)
FROM analytics.vw_demand_features

ORDER BY view_name;