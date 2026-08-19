## 1. Import Libraries

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sqlalchemy import create_engine, text

from IPython.display import display

pd.set_option("display.max_columns", None)
pd.set_option("display.float_format", lambda x: f"{x:,.2f}")


## 2. PostgreSQL Connection
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "stocksense_ai"
DB_USER = "aiubvaibbibvv"
DB_PASSWORD = "Enter your DB password"

connection_string = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(connection_string)

with engine.connect() as connection:
    result = connection.execute(text("SELECT 1"))
    print("PostgreSQL connection successful.")


## 3. Analytics Layer Overview
views_query = """
SELECT
    table_name AS view_name
FROM information_schema.views
WHERE table_schema = 'analytics'
ORDER BY table_name;
"""

views = pd.read_sql(views_query, engine)

display(views)


# 4. Executive Business Overview
overview_query = """
SELECT
    ROUND(SUM(revenue)::NUMERIC, 2) AS total_revenue,
    ROUND(SUM(cogs)::NUMERIC, 2) AS total_cogs,
    ROUND(SUM(gross_profit)::NUMERIC, 2) AS gross_profit,
    ROUND(
        (
            SUM(gross_profit)
            / NULLIF(SUM(revenue), 0)
        )::NUMERIC,
        4
    ) AS gross_margin,
    SUM(units_sold) AS total_units_sold,
    SUM(transactions) AS total_transactions,
    MIN(sales_date) AS first_sales_date,
    MAX(sales_date) AS last_sales_date
FROM analytics.vw_daily_sales;
"""

overview = pd.read_sql(overview_query, engine)

display(overview)



# 5. Sales Trend Analysis
monthly_sales_query = """
SELECT
    month_start,
    year,
    month_number,
    month_name,
    revenue,
    cogs,
    gross_profit,
    gross_margin,
    units_sold,
    transactions
FROM analytics.vw_monthly_sales
ORDER BY month_start;
"""

monthly_sales = pd.read_sql(monthly_sales_query, engine)

monthly_sales.head()

plt.figure(figsize=(14, 6))

plt.plot(
    monthly_sales["month_start"],
    monthly_sales["revenue"],
    marker="o"
)

plt.title("Monthly Revenue Trend")
plt.xlabel("Month")
plt.ylabel("Revenue")

plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

plt.figure(figsize=(14, 6))

plt.plot(
    monthly_sales["month_start"],
    monthly_sales["units_sold"],
    marker="o"
)

plt.title("Monthly Unit Demand Trend")
plt.xlabel("Month")
plt.ylabel("Units Sold")

plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


# 6. Product Performance
product_query = """
SELECT
    product_no,
    product_description,
    product_category,
    product_subcategory,
    product_segment,
    units_sold,
    revenue,
    cogs,
    gross_profit,
    gross_margin
FROM analytics.vw_product_performance
ORDER BY revenue DESC;
"""

products = pd.read_sql(product_query, engine)

products.head(10)


top_products = products.head(10)

plt.figure(figsize=(12, 7))

plt.barh(
    top_products["product_description"].astype(str),
    top_products["revenue"]
)

plt.gca().invert_yaxis()

plt.title("Top 10 Products by Revenue")
plt.xlabel("Revenue")
plt.ylabel("Product")

plt.tight_layout()
plt.show()


category_query = """
SELECT
    product_category,
    SUM(units_sold) AS units_sold,
    SUM(revenue) AS revenue,
    SUM(gross_profit) AS gross_profit
FROM analytics.vw_product_performance
GROUP BY product_category
ORDER BY revenue DESC;
"""

category_performance = pd.read_sql(category_query, engine)

display(category_performance.head(15))


top_categories = category_performance.head(10)

plt.figure(figsize=(12, 6))

plt.bar(
    top_categories["product_category"].astype(str),
    top_categories["revenue"]
)

plt.title("Top Product Categories by Revenue")
plt.xlabel("Product Category")
plt.ylabel("Revenue")

plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.show()



# 7. Store Performance
store_query = """
SELECT
    store_id,
    store_type,
    units_sold,
    revenue,
    gross_profit,
    gross_margin,
    transactions
FROM analytics.vw_store_performance
ORDER BY revenue DESC;
"""

stores = pd.read_sql(store_query, engine)

display(stores.head(10))


plt.figure(figsize=(12, 7))

plt.barh(
    stores.head(10)["store_id"].astype(str),
    stores.head(10)["revenue"]
)

plt.gca().invert_yaxis()

plt.title("Top 10 Stores by Revenue")
plt.xlabel("Revenue")
plt.ylabel("Store")

plt.tight_layout()
plt.show()


# 8. Inventory Position
# ============================================================
# 8. INVENTORY POSITION
# ============================================================

print("\n" + "=" * 70)
print("8. INVENTORY POSITION")
print("=" * 70)

inventory_query = """
SELECT
    store_id,
    store_type,
    product_no,
    product_description,
    product_category,
    supplier_name,
    qty_on_hand,
    stocks_selling_amount,
    cost_of_stocks
FROM analytics.vw_inventory_position;
"""

inventory = pd.read_sql(inventory_query, engine)

print("\nInventory data loaded successfully.")
print(f"Inventory positions: {len(inventory):,}")

print("\nInventory preview:")
print(inventory.head())


inventory_summary = pd.DataFrame({
    "Metric": [
        "Inventory Positions",
        "Units on Hand",
        "Inventory Cost",
        "Inventory Selling Value"
    ],
    "Value": [
        len(inventory),
        inventory["qty_on_hand"].sum(),
        inventory["cost_of_stocks"].sum(),
        inventory["stocks_selling_amount"].sum()
    ]
})

print("\nInventory Summary:")
print(inventory_summary)



# ============================================================
# 9. INVENTORY RISK ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("9. INVENTORY RISK ANALYSIS")
print("=" * 70)

risk_query = """
SELECT
    store_id,
    product_no,
    product_description,
    product_category,
    qty_on_hand,
    units_sold_30d,
    average_daily_units_sold,
    estimated_days_of_cover,
    inventory_risk
FROM analytics.vw_inventory_risk;
"""

inventory_risk = pd.read_sql(risk_query, engine)

print("\nInventory risk data loaded successfully.")
print(f"Inventory risk positions: {len(inventory_risk):,}")

print("\nInventory risk preview:")
print(inventory_risk.head())


risk_summary = (
    inventory_risk
    .groupby("inventory_risk")
    .agg(
        product_store_positions=("product_no", "count"),
        units_on_hand=("qty_on_hand", "sum"),
        units_sold_30d=("units_sold_30d", "sum")
    )
    .sort_values(
        "product_store_positions",
        ascending=False
    )
)

print("\nInventory Risk Summary:")
print(risk_summary)


# Risk distribution chart

plt.figure(figsize=(10, 6))

risk_counts = (
    inventory_risk["inventory_risk"]
    .value_counts()
)

plt.bar(
    risk_counts.index,
    risk_counts.values
)

plt.title("Inventory Risk Distribution")
plt.xlabel("Risk Classification")
plt.ylabel("Product-Store Positions")

plt.xticks(rotation=30)
plt.tight_layout()
plt.show()


# Critical inventory positions

critical_inventory = (
    inventory_risk[
        inventory_risk["inventory_risk"].isin(
            ["OUT_OF_STOCK", "CRITICAL", "HIGH"]
        )
    ]
    .sort_values(
        "estimated_days_of_cover",
        na_position="first"
    )
)

print("\nTop Critical / High-Risk Inventory Positions:")
print(
    critical_inventory[
        [
            "store_id",
            "product_no",
            "product_description",
            "qty_on_hand",
            "units_sold_30d",
            "average_daily_units_sold",
            "estimated_days_of_cover",
            "inventory_risk"
        ]
    ].head(20)
)



# 10. Slow-Moving Inventory
slow_query = """
SELECT
    store_id,
    product_no,
    product_description,
    product_category,
    supplier_name,
    qty_on_hand,
    cost_of_stocks,
    stocks_selling_amount,
    units_sold_30d,
    average_daily_units_sold,
    estimated_days_of_cover,
    movement_class
FROM analytics.vw_slow_moving_products
ORDER BY cost_of_stocks DESC;
"""

slow_inventory = pd.read_sql(slow_query, engine)

display(slow_inventory.head(20))

slow_summary = (
    slow_inventory
    .groupby("movement_class")
    .agg(
        positions=("product_no", "count"),
        units_on_hand=("qty_on_hand", "sum"),
        inventory_cost=("cost_of_stocks", "sum")
    )
    .sort_values("inventory_cost", ascending=False)
)

display(slow_summary)



#11. ABC Product Classification
abc_query = """
SELECT
    product_no,
    product_description,
    product_category,
    revenue,
    cumulative_revenue_pct,
    abc_class
FROM analytics.vw_abc_product_classification
ORDER BY revenue DESC;
"""

abc = pd.read_sql(abc_query, engine)

display(abc.head(20))


abc_summary = (
    abc
    .groupby("abc_class")
    .agg(
        products=("product_no", "count"),
        revenue=("revenue", "sum")
    )
)

abc_summary["revenue_share"] = (
    abc_summary["revenue"]
    / abc_summary["revenue"].sum()
)

display(abc_summary)


# 12. Return Behaviour
return_query = """
SELECT
    SUM(gross_units_sold) AS gross_units,
    SUM(returned_units) AS returned_units,
    SUM(net_units_sold) AS net_units,
    SUM(gross_revenue) AS gross_revenue,
    SUM(returned_revenue) AS returned_revenue,
    SUM(net_revenue) AS net_revenue
FROM analytics.vw_demand_features;
"""

return_summary = pd.read_sql(return_query, engine)

display(return_summary)


gross_units = return_summary.loc[0, "gross_units"]
returned_units = return_summary.loc[0, "returned_units"]

return_rate = returned_units / gross_units

print(f"Return rate: {return_rate:.2%}")




# 13. Demand Variability
demand_query = """
SELECT
    product_key,
    product_no,
    product_description,
    store_key,
    store_id,
    sales_date,
    gross_units_sold
FROM analytics.vw_demand_features
ORDER BY product_key, store_key, sales_date;
"""

demand = pd.read_sql(demand_query, engine)

display(demand.head())


demand_variability = (
    demand
    .groupby(
        [
            "product_key",
            "product_no",
            "product_description",
            "store_key",
            "store_id"
        ]
    )
    .agg(
        average_daily_demand=("gross_units_sold", "mean"),
        demand_std=("gross_units_sold", "std"),
        total_demand=("gross_units_sold", "sum"),
        demand_days=("sales_date", "nunique")
    )
    .reset_index()
)

demand_variability["coefficient_of_variation"] = (
    demand_variability["demand_std"]
    /
    demand_variability["average_daily_demand"]
    .replace(0, np.nan)
)

display(
    demand_variability
    .sort_values(
        "coefficient_of_variation",
        ascending=False
    )
    .head(20)
)


# 14. Demand vs Inventory
inventory_demand = inventory_risk.copy()

inventory_demand[
    [
        "product_no",
        "product_description",
        "store_id",
        "qty_on_hand",
        "units_sold_30d",
        "average_daily_units_sold",
        "estimated_days_of_cover",
        "inventory_risk"
    ]
].head(20)



### 15. Initial Business Findings

#Populate this section after reviewing the outputs above.

#The findings should be evidence-based and should include:

### Sales
#- Overall revenue trend
#- Demand trend
#- Seasonal patterns

### Products
#- Highest-revenue products
#- Highest-volume products
#- Most profitable categories

### Inventory
#- Critical stock positions
#- High-risk products
#- Slow-moving inventory

### Demand
#3- High-demand products
#- High-volatility products
#- Stable products

### Returns
#- Overall return rate
#- Products/categories with elevated returns

### Business Opportunity

###Identify where StockSense AI could provide the greatest value:
##- Demand forecasting
##- Reorder recommendations
##- Stockout prevention
##- Excess inventory reduction
##- Inventory prioritisation ###
