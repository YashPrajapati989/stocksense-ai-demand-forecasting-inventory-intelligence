-- ============================================================
-- StockSense AI
-- Phase 3 - PostgreSQL Data Architecture
-- Step 7: Analytics Layer Validation
-- ============================================================

-- ============================================================
-- 1. ANALYTICS VIEW EXISTENCE CHECK
-- ============================================================

SELECT
    table_name AS view_name
FROM information_schema.views
WHERE table_schema = 'analytics'
ORDER BY table_name;


-- ============================================================
-- 2. ANALYTICS VIEW ROW COUNTS
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


-- ============================================================
-- 3. DAILY SALES RECONCILIATION
-- ============================================================

SELECT
    'Revenue' AS metric,

    (
        SELECT COALESCE(SUM(sales_amount), 0)
        FROM core.fact_sales
    ) AS core_value,

    (
        SELECT COALESCE(SUM(revenue), 0)
        FROM analytics.vw_daily_sales
    ) AS analytics_value,

    (
        SELECT COALESCE(SUM(sales_amount), 0)
        FROM core.fact_sales
    )
    -
    (
        SELECT COALESCE(SUM(revenue), 0)
        FROM analytics.vw_daily_sales
    ) AS difference

UNION ALL

SELECT
    'Units Sold',

    (
        SELECT COALESCE(SUM(qty_sold), 0)
        FROM core.fact_sales
    ),

    (
        SELECT COALESCE(SUM(units_sold), 0)
        FROM analytics.vw_daily_sales
    ),

    (
        SELECT COALESCE(SUM(qty_sold), 0)
        FROM core.fact_sales
    )
    -
    (
        SELECT COALESCE(SUM(units_sold), 0)
        FROM analytics.vw_daily_sales
    )

UNION ALL

SELECT
    'COGS',

    (
        SELECT COALESCE(SUM(cogs), 0)
        FROM core.fact_sales
    ),

    (
        SELECT COALESCE(SUM(cogs), 0)
        FROM analytics.vw_daily_sales
    ),

    (
        SELECT COALESCE(SUM(cogs), 0)
        FROM core.fact_sales
    )
    -
    (
        SELECT COALESCE(SUM(cogs), 0)
        FROM analytics.vw_daily_sales
    );


-- ============================================================
-- 4. MONTHLY SALES RECONCILIATION
-- ============================================================

SELECT
    'Monthly Revenue' AS metric,

    (
        SELECT COALESCE(SUM(sales_amount), 0)
        FROM core.fact_sales
    ) AS core_value,

    (
        SELECT COALESCE(SUM(revenue), 0)
        FROM analytics.vw_monthly_sales
    ) AS analytics_value,

    (
        SELECT COALESCE(SUM(sales_amount), 0)
        FROM core.fact_sales
    )
    -
    (
        SELECT COALESCE(SUM(revenue), 0)
        FROM analytics.vw_monthly_sales
    ) AS difference

UNION ALL

SELECT
    'Monthly Units Sold',

    (
        SELECT COALESCE(SUM(qty_sold), 0)
        FROM core.fact_sales
    ),

    (
        SELECT COALESCE(SUM(units_sold), 0)
        FROM analytics.vw_monthly_sales
    ),

    (
        SELECT COALESCE(SUM(qty_sold), 0)
        FROM core.fact_sales
    )
    -
    (
        SELECT COALESCE(SUM(units_sold), 0)
        FROM analytics.vw_monthly_sales
    );


-- ============================================================
-- 5. PRODUCT PERFORMANCE RECONCILIATION
-- ============================================================

SELECT
    'Product Revenue' AS metric,

    (
        SELECT COALESCE(SUM(sales_amount), 0)
        FROM core.fact_sales
    ) AS core_value,

    (
        SELECT COALESCE(SUM(revenue), 0)
        FROM analytics.vw_product_performance
    ) AS analytics_value,

    (
        SELECT COALESCE(SUM(sales_amount), 0)
        FROM core.fact_sales
    )
    -
    (
        SELECT COALESCE(SUM(revenue), 0)
        FROM analytics.vw_product_performance
    ) AS difference

UNION ALL

SELECT
    'Product Units',

    (
        SELECT COALESCE(SUM(qty_sold), 0)
        FROM core.fact_sales
    ),

    (
        SELECT COALESCE(SUM(units_sold), 0)
        FROM analytics.vw_product_performance
    ),

    (
        SELECT COALESCE(SUM(qty_sold), 0)
        FROM core.fact_sales
    )
    -
    (
        SELECT COALESCE(SUM(units_sold), 0)
        FROM analytics.vw_product_performance
    );


-- ============================================================
-- 6. STORE PERFORMANCE RECONCILIATION
-- ============================================================

SELECT
    'Store Revenue' AS metric,

    (
        SELECT COALESCE(SUM(sales_amount), 0)
        FROM core.fact_sales
    ) AS core_value,

    (
        SELECT COALESCE(SUM(revenue), 0)
        FROM analytics.vw_store_performance
    ) AS analytics_value,

    (
        SELECT COALESCE(SUM(sales_amount), 0)
        FROM core.fact_sales
    )
    -
    (
        SELECT COALESCE(SUM(revenue), 0)
        FROM analytics.vw_store_performance
    ) AS difference

UNION ALL

SELECT
    'Store Units',

    (
        SELECT COALESCE(SUM(qty_sold), 0)
        FROM core.fact_sales
    ),

    (
        SELECT COALESCE(SUM(units_sold), 0)
        FROM analytics.vw_store_performance
    ),

    (
        SELECT COALESCE(SUM(qty_sold), 0)
        FROM core.fact_sales
    )
    -
    (
        SELECT COALESCE(SUM(units_sold), 0)
        FROM analytics.vw_store_performance
    );


-- ============================================================
-- 7. SUPPLIER PERFORMANCE RECONCILIATION
-- ============================================================

SELECT
    'Supplier Revenue' AS metric,

    (
        SELECT COALESCE(SUM(sales_amount), 0)
        FROM core.fact_sales
    ) AS core_value,

    (
        SELECT COALESCE(SUM(revenue), 0)
        FROM analytics.vw_supplier_performance
    ) AS analytics_value,

    (
        SELECT COALESCE(SUM(sales_amount), 0)
        FROM core.fact_sales
    )
    -
    (
        SELECT COALESCE(SUM(revenue), 0)
        FROM analytics.vw_supplier_performance
    ) AS difference;


-- ============================================================
-- 8. PRODUCT PERFORMANCE DUPLICATE CHECK
-- ============================================================

SELECT
    product_no,
    COUNT(*) AS row_count
FROM analytics.vw_product_performance
GROUP BY product_no
HAVING COUNT(*) > 1
ORDER BY row_count DESC;


-- ============================================================
-- 9. STORE PERFORMANCE DUPLICATE CHECK
-- ============================================================

SELECT
    store_id,
    COUNT(*) AS row_count
FROM analytics.vw_store_performance
GROUP BY store_id
HAVING COUNT(*) > 1
ORDER BY row_count DESC;


-- ============================================================
-- 10. SUPPLIER PERFORMANCE DUPLICATE CHECK
-- ============================================================

SELECT
    supplier_id,
    COUNT(*) AS row_count
FROM analytics.vw_supplier_performance
GROUP BY supplier_id
HAVING COUNT(*) > 1
ORDER BY row_count DESC;


-- ============================================================
-- 11. INVENTORY POSITION UNIQUENESS
-- ============================================================
-- There should be at most one current inventory record for each
-- Store × Product combination.

SELECT
    store_id,
    product_no,
    COUNT(*) AS row_count
FROM analytics.vw_inventory_position
GROUP BY
    store_id,
    product_no
HAVING COUNT(*) > 1
ORDER BY row_count DESC;


-- ============================================================
-- 12. INVENTORY POSITION QUALITY
-- ============================================================

SELECT
    COUNT(*) AS total_inventory_positions,

    COUNT(*) FILTER (
        WHERE qty_on_hand < 0
    ) AS negative_stock,

    COUNT(*) FILTER (
        WHERE cost_of_stocks < 0
    ) AS negative_cost,

    COUNT(*) FILTER (
        WHERE stocks_selling_amount < 0
    ) AS negative_selling_value,

    COUNT(*) FILTER (
        WHERE stock_unit_cost_price < 0
    ) AS negative_unit_cost,

    COUNT(*) FILTER (
        WHERE stock_unit_selling_price < 0
    ) AS negative_unit_selling_price

FROM analytics.vw_inventory_position;


-- ============================================================
-- 13. INVENTORY RISK CLASSIFICATION CHECK
-- ============================================================

SELECT
    inventory_risk,
    COUNT(*) AS product_store_count
FROM analytics.vw_inventory_risk
GROUP BY inventory_risk
ORDER BY product_store_count DESC;


-- ============================================================
-- 14. INVENTORY RISK LOGIC CHECK
-- ============================================================

SELECT
    COUNT(*) AS risk_logic_violations
FROM analytics.vw_inventory_risk
WHERE
       (
           inventory_risk = 'OUT_OF_STOCK'
           AND qty_on_hand > 0
       )

    OR (
           inventory_risk = 'CRITICAL'
           AND (
               qty_on_hand <= 0
               OR estimated_days_of_cover IS NULL
               OR estimated_days_of_cover > 7
           )
       )

    OR (
           inventory_risk = 'HIGH'
           AND (
               estimated_days_of_cover IS NULL
               OR estimated_days_of_cover <= 7
               OR estimated_days_of_cover > 14
           )
       )

    OR (
           inventory_risk = 'MEDIUM'
           AND (
               estimated_days_of_cover IS NULL
               OR estimated_days_of_cover <= 14
               OR estimated_days_of_cover > 30
           )
       )

    OR (
           inventory_risk = 'HEALTHY'
           AND (
               estimated_days_of_cover IS NULL
               OR estimated_days_of_cover <= 30
           )
       );


-- ============================================================
-- 15. DAYS OF COVER QUALITY
-- ============================================================

SELECT
    COUNT(*) AS total_positions,

    COUNT(*) FILTER (
        WHERE estimated_days_of_cover IS NULL
    ) AS null_days_of_cover,

    COUNT(*) FILTER (
        WHERE estimated_days_of_cover < 0
    ) AS negative_days_of_cover,

    MIN(estimated_days_of_cover)
        AS minimum_days_of_cover,

    MAX(estimated_days_of_cover)
        AS maximum_days_of_cover,

    AVG(estimated_days_of_cover)
        AS average_days_of_cover

FROM analytics.vw_inventory_risk;


-- ============================================================
-- 16. SLOW-MOVING INVENTORY CHECK
-- ============================================================

SELECT
    movement_class,
    COUNT(*) AS product_store_count,
    SUM(qty_on_hand) AS units_on_hand,
    SUM(cost_of_stocks) AS inventory_cost,
    SUM(stocks_selling_amount) AS inventory_selling_value
FROM analytics.vw_slow_moving_products
GROUP BY movement_class
ORDER BY
    CASE movement_class
        WHEN 'NO_SALES_30D' THEN 1
        WHEN 'VERY_SLOW' THEN 2
        WHEN 'SLOW' THEN 3
        ELSE 4
    END;


-- ============================================================
-- 17. ABC CLASSIFICATION DISTRIBUTION
-- ============================================================

SELECT
    abc_class,
    COUNT(*) AS product_count,
    SUM(revenue) AS revenue,
    CASE
        WHEN SUM(SUM(revenue)) OVER () = 0
            THEN 0
        ELSE
            SUM(revenue)
            /
            SUM(SUM(revenue)) OVER ()
    END AS revenue_share
FROM analytics.vw_abc_product_classification
GROUP BY abc_class
ORDER BY abc_class;


-- ============================================================
-- 18. ABC CLASS VALIDATION
-- ============================================================

SELECT
    COUNT(*) AS invalid_abc_rows
FROM analytics.vw_abc_product_classification
WHERE abc_class NOT IN ('A', 'B', 'C');


-- ============================================================
-- 19. ABC CUMULATIVE PERCENTAGE VALIDATION
-- ============================================================

SELECT
    COUNT(*) AS invalid_cumulative_percentages
FROM analytics.vw_abc_product_classification
WHERE cumulative_revenue_pct < 0
   OR cumulative_revenue_pct > 1;


-- ============================================================
-- 20. DEMAND FEATURE QUALITY
-- ============================================================

SELECT
    COUNT(*) AS demand_feature_rows,

    COUNT(DISTINCT sales_date)
        AS sales_dates,

    COUNT(DISTINCT store_key)
        AS stores,

    COUNT(DISTINCT product_key)
        AS products,

    COUNT(*) FILTER (
        WHERE units_sold < 0
    ) AS negative_units,

    COUNT(*) FILTER (
        WHERE revenue < 0
    ) AS negative_revenue

FROM analytics.vw_demand_features;


-- ============================================================
-- 21. DEMAND FEATURE DUPLICATE GRAIN CHECK
-- ============================================================
-- Expected grain:
-- Store × Product × Date

SELECT
    sales_date,
    store_key,
    product_key,
    COUNT(*) AS row_count
FROM analytics.vw_demand_features
GROUP BY
    sales_date,
    store_key,
    product_key
HAVING COUNT(*) > 1
ORDER BY row_count DESC;


-- ============================================================
-- 22. DEMAND ROLLING FEATURE SANITY CHECK
-- ============================================================

SELECT
    COUNT(*) AS invalid_rolling_features
FROM analytics.vw_demand_features
WHERE
       avg_daily_units_7d < 0
    OR avg_daily_units_30d < 0
    OR units_sold_7d < 0
    OR units_sold_30d < 0
    OR revenue_7d < 0
    OR revenue_30d < 0;


-- ============================================================
-- 23. DEMAND FEATURE RELATIONSHIP CHECK
-- ============================================================

SELECT
    COUNT(*) AS rolling_7d_greater_than_30d_violations
FROM analytics.vw_demand_features
WHERE
    units_sold_7d > units_sold_30d
    AND sales_date >= (
        SELECT MIN(sales_date) + INTERVAL '29 days'
        FROM analytics.vw_demand_features
    );


-- ============================================================
-- 24. BUSINESS KPI SNAPSHOT
-- ============================================================

SELECT
    ROUND(
        SUM(revenue)::NUMERIC,
        2
    ) AS total_revenue,

    ROUND(
        SUM(cogs)::NUMERIC,
        2
    ) AS total_cogs,

    ROUND(
        SUM(gross_profit)::NUMERIC,
        2
    ) AS gross_profit,

    ROUND(
        (
            SUM(gross_profit)
            /
            NULLIF(SUM(revenue), 0)
        )::NUMERIC,
        4
    ) AS gross_margin,

    SUM(units_sold) AS units_sold,

    SUM(transactions) AS transactions,

    COUNT(DISTINCT active_stores) AS daily_store_observations

FROM analytics.vw_daily_sales;


-- ============================================================
-- 25. TOP 10 PRODUCTS BY REVENUE
-- ============================================================

SELECT
    product_no,
    product_description,
    product_category,
    units_sold,
    revenue,
    gross_profit,
    gross_margin
FROM analytics.vw_product_performance
ORDER BY revenue DESC
LIMIT 10;


-- ============================================================
-- 26. TOP 10 STORES BY REVENUE
-- ============================================================

SELECT
    store_id,
    store_type,
    units_sold,
    revenue,
    gross_profit,
    gross_margin
FROM analytics.vw_store_performance
ORDER BY revenue DESC
LIMIT 10;


-- ============================================================
-- 27. HIGHEST INVENTORY RISK POSITIONS
-- ============================================================

SELECT
    store_id,
    product_no,
    product_description,
    qty_on_hand,
    units_sold_30d,
    average_daily_units_sold,
    estimated_days_of_cover,
    inventory_risk
FROM analytics.vw_inventory_risk
ORDER BY
    CASE inventory_risk
        WHEN 'OUT_OF_STOCK' THEN 1
        WHEN 'CRITICAL' THEN 2
        WHEN 'HIGH' THEN 3
        WHEN 'MEDIUM' THEN 4
        WHEN 'HEALTHY' THEN 5
        WHEN 'NO_RECENT_DEMAND' THEN 6
        ELSE 7
    END,
    estimated_days_of_cover NULLS FIRST
LIMIT 20;


-- ============================================================
-- 28. FINAL ANALYTICS VALIDATION SUMMARY
-- ============================================================

SELECT
    'Daily sales revenue reconciliation' AS validation_check,
    CASE
        WHEN ABS(
            (SELECT SUM(sales_amount)
             FROM core.fact_sales)
            -
            (SELECT SUM(revenue)
             FROM analytics.vw_daily_sales)
        ) < 0.01
        THEN 'PASS'
        ELSE 'FAIL'
    END AS status

UNION ALL

SELECT
    'Monthly sales revenue reconciliation',
    CASE
        WHEN ABS(
            (SELECT SUM(sales_amount)
             FROM core.fact_sales)
            -
            (SELECT SUM(revenue)
             FROM analytics.vw_monthly_sales)
        ) < 0.01
        THEN 'PASS'
        ELSE 'FAIL'
    END

UNION ALL

SELECT
    'Product revenue reconciliation',
    CASE
        WHEN ABS(
            (SELECT SUM(sales_amount)
             FROM core.fact_sales)
            -
            (SELECT SUM(revenue)
             FROM analytics.vw_product_performance)
        ) < 0.01
        THEN 'PASS'
        ELSE 'FAIL'
    END

UNION ALL

SELECT
    'Store revenue reconciliation',
    CASE
        WHEN ABS(
            (SELECT SUM(sales_amount)
             FROM core.fact_sales)
            -
            (SELECT SUM(revenue)
             FROM analytics.vw_store_performance)
        ) < 0.01
        THEN 'PASS'
        ELSE 'FAIL'
    END

UNION ALL

SELECT
    'Inventory position uniqueness',
    CASE
        WHEN NOT EXISTS (
            SELECT 1
            FROM analytics.vw_inventory_position
            GROUP BY store_id, product_no
            HAVING COUNT(*) > 1
        )
        THEN 'PASS'
        ELSE 'FAIL'
    END

UNION ALL

SELECT
    'Inventory risk logic',
    CASE
        WHEN (
            SELECT COUNT(*)
            FROM analytics.vw_inventory_risk
            WHERE
                   (
                       inventory_risk = 'OUT_OF_STOCK'
                       AND qty_on_hand > 0
                   )
                OR (
                       inventory_risk = 'CRITICAL'
                       AND (
                           qty_on_hand <= 0
                           OR estimated_days_of_cover IS NULL
                           OR estimated_days_of_cover > 7
                       )
                   )
                OR (
                       inventory_risk = 'HIGH'
                       AND (
                           estimated_days_of_cover IS NULL
                           OR estimated_days_of_cover <= 7
                           OR estimated_days_of_cover > 14
                       )
                   )
                OR (
                       inventory_risk = 'MEDIUM'
                       AND (
                           estimated_days_of_cover IS NULL
                           OR estimated_days_of_cover <= 14
                           OR estimated_days_of_cover > 30
                       )
                   )
                OR (
                       inventory_risk = 'HEALTHY'
                       AND (
                           estimated_days_of_cover IS NULL
                           OR estimated_days_of_cover <= 30
                       )
                   )
        ) = 0
        THEN 'PASS'
        ELSE 'FAIL'
    END

UNION ALL

SELECT
    'ABC classification validity',
    CASE
        WHEN NOT EXISTS (
            SELECT 1
            FROM analytics.vw_abc_product_classification
            WHERE abc_class NOT IN ('A', 'B', 'C')
               OR cumulative_revenue_pct < 0
               OR cumulative_revenue_pct > 1
        )
        THEN 'PASS'
        ELSE 'FAIL'
    END

UNION ALL

SELECT
    'Demand feature grain',
    CASE
        WHEN NOT EXISTS (
            SELECT 1
            FROM analytics.vw_demand_features
            GROUP BY sales_date, store_key, product_key
            HAVING COUNT(*) > 1
        )
        THEN 'PASS'
        ELSE 'FAIL'
    END

UNION ALL

SELECT
    'Demand feature non-negative sanity',
    CASE
        WHEN NOT EXISTS (
            SELECT 1
            FROM analytics.vw_demand_features
            WHERE
                   units_sold < 0
                OR revenue < 0
                OR avg_daily_units_7d < 0
                OR avg_daily_units_30d < 0
                OR units_sold_7d < 0
                OR units_sold_30d < 0
                OR revenue_7d < 0
                OR revenue_30d < 0
        )
        THEN 'PASS'
        ELSE 'FAIL'
    END

ORDER BY validation_check;