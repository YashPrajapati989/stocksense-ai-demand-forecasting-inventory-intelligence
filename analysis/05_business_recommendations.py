# ============================================================
# StockSense AI
# Phase 8 - Business Recommendations & Decision Intelligence
# File: 05_business_recommendations.py
# ============================================================

import os
import warnings

import pandas as pd
import numpy as np

from sqlalchemy import create_engine


warnings.filterwarnings("ignore")


# ============================================================
# 1. CONFIGURATION
# ============================================================

print("=" * 70)
print("STOCKSENSE AI - BUSINESS RECOMMENDATIONS")
print("=" * 70)


# PostgreSQL Connection
# ------------------------------------------------------------
# IMPORTANT:
# Use the same connection configuration that worked in your
# previous scripts.
# Do not upload your real password to GitHub.
# ------------------------------------------------------------

DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "stocksense_ai",
    "user": "postgres",
    "password": "yash7046"
}


DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_CONFIG['user']}:"
    f"{DB_CONFIG['password']}@"
    f"{DB_CONFIG['host']}:"
    f"{DB_CONFIG['port']}/"
    f"{DB_CONFIG['database']}"
)


RESULTS_DIR = "../results"

INPUT_FILE = os.path.join(
    RESULTS_DIR,
    "inventory_optimization_recommendations.csv"
)


# ============================================================
# 2. CONNECT TO POSTGRESQL
# ============================================================

print("\n" + "=" * 70)
print("CONNECTING TO POSTGRESQL")
print("=" * 70)


try:

    engine = create_engine(
        DATABASE_URL
    )

    with engine.connect() as connection:
        pass

    print("\n✓ PostgreSQL connection successful.")


except Exception as error:

    raise ConnectionError(
        f"PostgreSQL connection failed:\n{error}"
    )


# ============================================================
# 3. LOAD INVENTORY OPTIMIZATION OUTPUT
# ============================================================

print("\n" + "=" * 70)
print("LOADING INVENTORY INTELLIGENCE DATA")
print("=" * 70)


df = pd.read_csv(
    INPUT_FILE
)


print("\n✓ Inventory intelligence dataset loaded.")

print(
    f"Rows    : {len(df):,}"
)

print(
    f"Columns : {df.shape[1]:,}"
)


# ============================================================
# 4. LOAD PRODUCT DIMENSION
# ============================================================

print("\n" + "=" * 70)
print("LOADING PRODUCT INFORMATION")
print("=" * 70)


product_query = """

SELECT
    product_key,
    product_no,
    product_description,
    product_division,
    product_category,
    product_subcategory,
    product_segment
FROM core.dim_product

"""


product_df = pd.read_sql(
    product_query,
    engine
)


print(
    f"\n✓ Product records loaded: "
    f"{len(product_df):,}"
)


# ============================================================
# 5. LOAD STORE DIMENSION
# ============================================================

print("\n" + "=" * 70)
print("LOADING STORE INFORMATION")
print("=" * 70)


store_query = """

SELECT
    store_key,
    store_id AS store,
    store_type
FROM core.dim_store

"""


store_df = pd.read_sql(
    store_query,
    engine
)


print(
    f"\n✓ Store records loaded: "
    f"{len(store_df):,}"
)


# ============================================================
# 6. LOAD ABC CLASSIFICATION
# ============================================================

print("\n" + "=" * 70)
print("LOADING ABC PRODUCT CLASSIFICATION")
print("=" * 70)


abc_query = """

SELECT
    product_key,
    abc_class
FROM analytics.vw_abc_product_classification

"""


abc_df = pd.read_sql(
    abc_query,
    engine
)


print(
    f"\n✓ ABC classification records loaded: "
    f"{len(abc_df):,}"
)


# ============================================================
# 7. MERGE BUSINESS CONTEXT
# ============================================================

print("\n" + "=" * 70)
print("COMBINING BUSINESS INTELLIGENCE DATA")
print("=" * 70)


df = df.merge(

    product_df,

    on="product_key",

    how="left"

)


df = df.merge(

    store_df,

    on="store_key",

    how="left"

)


df = df.merge(

    abc_df,

    on="product_key",

    how="left"

)


print(
    f"\n✓ Business context added."
)


print(
    f"Final analytical rows: "
    f"{len(df):,}"
)


# ============================================================
# 8. FORECAST COVERAGE
# ============================================================

print("\n" + "=" * 70)
print("ASSESSING FORECAST COVERAGE")
print("=" * 70)


df["forecast_available"] = np.where(

    df["forecast_demand_7d"] > 0,

    "YES",

    "NO"

)


print(
    "\nForecast Coverage:"
)


print(
    df["forecast_available"]
    .value_counts()
)


# ============================================================
# 9. CREATE BUSINESS PRIORITY SCORE
# ============================================================

print("\n" + "=" * 70)
print("CALCULATING BUSINESS PRIORITY")
print("=" * 70)


def calculate_priority(row):

    score = 0


    # Inventory risk

    if row["inventory_risk"] == "CRITICAL":

        score += 50

    elif row["inventory_risk"] == "HIGH RISK":

        score += 35

    elif row["inventory_risk"] == "MONITOR":

        score += 15


    # ABC importance

    if row["abc_class"] == "A":

        score += 30

    elif row["abc_class"] == "B":

        score += 15

    elif row["abc_class"] == "C":

        score += 5


    # Forecast availability

    if row["forecast_available"] == "YES":

        score += 10


    return score


df["priority_score"] = df.apply(
    calculate_priority,
    axis=1
)


# ============================================================
# 10. CREATE PRIORITY LEVEL
# ============================================================

print("\n" + "=" * 70)
print("ASSIGNING PRIORITY LEVELS")
print("=" * 70)


def assign_priority(score):

    if score >= 70:

        return "P1 - URGENT"

    elif score >= 50:

        return "P2 - HIGH"

    elif score >= 25:

        return "P3 - MEDIUM"

    else:

        return "P4 - LOW"


df["business_priority"] = df[
    "priority_score"
].apply(
    assign_priority
)


print(
    "\nBusiness Priority Distribution:"
)


print(
    df[
        "business_priority"
    ]
    .value_counts()
)


# ============================================================
# 11. TOP STOCKOUT PRIORITIES
# ============================================================

print("\n" + "=" * 70)
print("IDENTIFYING TOP STOCKOUT PRIORITIES")
print("=" * 70)


stockout_priority = (

    df[

        df[
            "inventory_risk"
        ].isin(
            [
                "CRITICAL",
                "HIGH RISK"
            ]
        )

    ]

    .sort_values(

        by=[
            "priority_score",
            "inventory_value_at_risk"
        ],

        ascending=False

    )

)


top_stockout_priority = stockout_priority.head(
    100
)


print(
    f"\nHigh-priority stockout records: "
    f"{len(stockout_priority):,}"
)


# ============================================================
# 12. EXCESS STOCK OPPORTUNITIES
# ============================================================

print("\n" + "=" * 70)
print("IDENTIFYING EXCESS STOCK OPPORTUNITIES")
print("=" * 70)


excess_stock = (

    df[

        df[
            "inventory_risk"
        ] == "EXCESS STOCK"

    ]

    .sort_values(

        by="inventory_value",

        ascending=False

    )

)


top_excess_stock = excess_stock.head(
    100
)


print(
    f"\nExcess stock records: "
    f"{len(excess_stock):,}"
)


# ============================================================
# 13. STORE RISK ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("ANALYSING STORE RISK")
print("=" * 70)


store_risk = (

    df.groupby(

        [
            "store_key",
            "store"
        ],

        dropna=False

    )

    .agg(

        inventory_records=(
            "product_key",
            "count"
        ),

        critical_items=(
            "inventory_risk",

            lambda x: (
                x == "CRITICAL"
            ).sum()
        ),

        high_risk_items=(
            "inventory_risk",

            lambda x: (
                x == "HIGH RISK"
            ).sum()
        ),

        excess_stock_items=(
            "inventory_risk",

            lambda x: (
                x == "EXCESS STOCK"
            ).sum()
        ),

        inventory_value_at_risk=(
            "inventory_value_at_risk",
            "sum"
        )

    )

    .reset_index()

)


store_risk["risk_items"] = (

    store_risk[
        "critical_items"
    ]

    +

    store_risk[
        "high_risk_items"
    ]

)


store_risk = store_risk.sort_values(

    "inventory_value_at_risk",

    ascending=False

)


print(
    f"\nStores analysed: "
    f"{len(store_risk):,}"
)


# ============================================================
# 14. PRODUCT RISK ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("ANALYSING PRODUCT RISK")
print("=" * 70)


product_risk = (

    df.groupby(

        [
            "product_key",
            "product_no",
            "product_description",
            "product_category",
            "abc_class"
        ],

        dropna=False

    )

    .agg(

        store_count=(
            "store_key",
            "nunique"
        ),

        critical_items=(
            "inventory_risk",

            lambda x: (
                x == "CRITICAL"
            ).sum()
        ),

        high_risk_items=(
            "inventory_risk",

            lambda x: (
                x == "HIGH RISK"
            ).sum()
        ),

        excess_stock_items=(
            "inventory_risk",

            lambda x: (
                x == "EXCESS STOCK"
            ).sum()
        ),

        inventory_value_at_risk=(
            "inventory_value_at_risk",
            "sum"
        )

    )

    .reset_index()

)


product_risk["risk_items"] = (

    product_risk[
        "critical_items"
    ]

    +

    product_risk[
        "high_risk_items"
    ]

)


product_risk = product_risk.sort_values(

    "inventory_value_at_risk",

    ascending=False

)


print(
    f"\nProducts analysed: "
    f"{len(product_risk):,}"
)


# ============================================================
# 15. CATEGORY RISK ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("ANALYSING CATEGORY RISK")
print("=" * 70)


category_risk = (

    df.groupby(

        "product_category",

        dropna=False

    )

    .agg(

        inventory_records=(
            "product_key",
            "count"
        ),

        critical_items=(
            "inventory_risk",

            lambda x: (
                x == "CRITICAL"
            ).sum()
        ),

        high_risk_items=(
            "inventory_risk",

            lambda x: (
                x == "HIGH RISK"
            ).sum()
        ),

        excess_stock_items=(
            "inventory_risk",

            lambda x: (
                x == "EXCESS STOCK"
            ).sum()
        ),

        inventory_value_at_risk=(
            "inventory_value_at_risk",
            "sum"
        )

    )

    .reset_index()

)


category_risk = category_risk.sort_values(

    "inventory_value_at_risk",

    ascending=False

)


print(
    f"\nCategories analysed: "
    f"{len(category_risk):,}"
)


# ============================================================
# 16. CREATE EXECUTIVE RECOMMENDATIONS
# ============================================================

print("\n" + "=" * 70)
print("GENERATING EXECUTIVE RECOMMENDATIONS")
print("=" * 70)


critical_count = (

    df[
        "inventory_risk"
    ] == "CRITICAL"

).sum()


high_risk_count = (

    df[
        "inventory_risk"
    ] == "HIGH RISK"

).sum()


excess_count = (

    df[
        "inventory_risk"
    ] == "EXCESS STOCK"

).sum()


total_value_at_risk = (

    df[
        "inventory_value_at_risk"
    ].sum()

)


recommendations = []


# Critical inventory recommendation

if critical_count > 0:

    recommendations.append({

        "priority": "P1 - URGENT",

        "recommendation":
        "Immediately replenish critical inventory items.",

        "business_reason":
        f"{critical_count:,} inventory records are currently at critical stock levels."

    })


# High risk recommendation

if high_risk_count > 0:

    recommendations.append({

        "priority": "P2 - HIGH",

        "recommendation":
        "Prioritise purchase orders for high-risk inventory.",

        "business_reason":
        f"{high_risk_count:,} inventory records are below the recommended reorder threshold."

    })


# Excess inventory recommendation

if excess_count > 0:

    recommendations.append({

        "priority": "P2 - HIGH",

        "recommendation":
        "Review excess inventory for redistribution, promotions or purchasing reductions.",

        "business_reason":
        f"{excess_count:,} inventory records have more than 90 days of estimated inventory coverage."

    })


# Inventory value at risk

if total_value_at_risk > 0:

    recommendations.append({

        "priority": "P1 - URGENT",

        "recommendation":
        "Prioritise high-value inventory at risk.",

        "business_reason":
        f"Total inventory value exposed to stockout risk is {total_value_at_risk:,.2f}."

    })


recommendations_df = pd.DataFrame(
    recommendations
)


print(
    f"\nExecutive recommendations generated: "
    f"{len(recommendations_df)}"
)


# ============================================================
# 17. CREATE SUMMARY KPIs
# ============================================================

print("\n" + "=" * 70)
print("CREATING EXECUTIVE KPIs")
print("=" * 70)


summary_kpis = pd.DataFrame({

    "metric": [

        "Total Inventory Records",

        "Critical Items",

        "High Risk Items",

        "Monitor Items",

        "Healthy Items",

        "Excess Stock Items",

        "Inventory Value At Risk",

        "Average 7-Day Forecast",

        "Forecast Coverage (%)"

    ],

    "value": [

        len(df),

        (
            df["inventory_risk"]
            == "CRITICAL"
        ).sum(),

        (
            df["inventory_risk"]
            == "HIGH RISK"
        ).sum(),

        (
            df["inventory_risk"]
            == "MONITOR"
        ).sum(),

        (
            df["inventory_risk"]
            == "HEALTHY"
        ).sum(),

        (
            df["inventory_risk"]
            == "EXCESS STOCK"
        ).sum(),

        total_value_at_risk,

        df[
            "forecast_demand_7d"
        ].mean(),

        (
            df[
                "forecast_available"
            ]
            == "YES"
        ).mean() * 100

    ]

})


print(
    "\n✓ Executive KPIs created."
)


# ============================================================
# 18. SAVE BUSINESS OUTPUTS
# ============================================================

print("\n" + "=" * 70)
print("SAVING BUSINESS RECOMMENDATIONS")
print("=" * 70)


top_stockout_priority.to_csv(

    os.path.join(
        RESULTS_DIR,
        "top_stockout_priorities.csv"
    ),

    index=False

)


top_excess_stock.to_csv(

    os.path.join(
        RESULTS_DIR,
        "top_excess_stock_opportunities.csv"
    ),

    index=False

)


store_risk.to_csv(

    os.path.join(
        RESULTS_DIR,
        "store_risk_analysis.csv"
    ),

    index=False

)


product_risk.to_csv(

    os.path.join(
        RESULTS_DIR,
        "product_risk_analysis.csv"
    ),

    index=False

)


category_risk.to_csv(

    os.path.join(
        RESULTS_DIR,
        "category_risk_analysis.csv"
    ),

    index=False

)


recommendations_df.to_csv(

    os.path.join(
        RESULTS_DIR,
        "executive_recommendations.csv"
    ),

    index=False

)


summary_kpis.to_csv(

    os.path.join(
        RESULTS_DIR,
        "executive_kpis.csv"
    ),

    index=False

)


print("\n✓ Business intelligence outputs saved successfully.")


# ============================================================
# 19. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("STOCKSENSE AI BUSINESS RECOMMENDATIONS COMPLETE")
print("=" * 70)


print(
    f"\nTotal inventory records analysed: "
    f"{len(df):,}"
)


print(
    f"Critical inventory items: "
    f"{critical_count:,}"
)


print(
    f"High-risk inventory items: "
    f"{high_risk_count:,}"
)


print(
    f"Excess stock items: "
    f"{excess_count:,}"
)


print(
    f"\nTotal inventory value at risk: "
    f"{total_value_at_risk:,.2f}"
)


print("\nGenerated files:")

print(
    "• top_stockout_priorities.csv"
)

print(
    "• top_excess_stock_opportunities.csv"
)

print(
    "• store_risk_analysis.csv"
)

print(
    "• product_risk_analysis.csv"
)

print(
    "• category_risk_analysis.csv"
)

print(
    "• executive_recommendations.csv"
)

print(
    "• executive_kpis.csv"
)


print(
    "\nNext phase:"
    "\nPower BI Dashboard & StockSense AI Decision Intelligence"
)
