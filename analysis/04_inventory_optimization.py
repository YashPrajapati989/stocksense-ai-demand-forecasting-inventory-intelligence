# ============================================================
# StockSense AI
# Phase 7 - Inventory Optimization & Risk Intelligence
# File: 04_inventory_optimization.py
# ============================================================

import os
import pickle
import warnings

import numpy as np
import pandas as pd

from sqlalchemy import create_engine


warnings.filterwarnings("ignore")


# ============================================================
# 1. CONFIGURATION
# ============================================================

print("=" * 70)
print("STOCKSENSE AI - INVENTORY OPTIMIZATION")
print("=" * 70)


# PostgreSQL connection
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "stocksense_ai",
    "user": "postgres",
    "password": "yash7046"
}


# ------------------------------------------------------------
# IMPORTANT
# ------------------------------------------------------------
# Replace YOUR_POSTGRES_PASSWORD with your actual password.
# Do not upload this password to GitHub.
# ------------------------------------------------------------


DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_CONFIG['user']}:"
    f"{DB_CONFIG['password']}@"
    f"{DB_CONFIG['host']}:"
    f"{DB_CONFIG['port']}/"
    f"{DB_CONFIG['database']}"
)


RESULTS_DIR = "../results"
MODELS_DIR = "../models"

MODEL_PATH = os.path.join(
    MODELS_DIR,
    "best_demand_forecasting_model_timeseries.pkl"
)

FEATURE_PATH = os.path.join(
    MODELS_DIR,
    "model_features_timeseries.pkl"
)

OUTPUT_PATH = os.path.join(
    RESULTS_DIR,
    "inventory_optimization_recommendations.csv"
)


# Inventory assumptions

LEAD_TIME_DAYS = 7

SERVICE_LEVEL_Z = 1.65

FORECAST_HORIZON = 7


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

    connection = engine.connect()

    connection.close()

    print("\n✓ PostgreSQL connection successful.")


except Exception as error:

    raise ConnectionError(
        f"PostgreSQL connection failed:\n{error}"
    )


# ============================================================
# 3. LOAD INVENTORY DATA
# ============================================================

print("\n" + "=" * 70)
print("LOADING CURRENT INVENTORY DATA")
print("=" * 70)


inventory_query = """

SELECT
    inventory_key,
    store_key,
    product_key,
    stock_status,
    qty_on_hand,
    stocks_selling_amount,
    cost_of_stocks
FROM analytics.vw_inventory_position

"""


inventory_df = pd.read_sql(
    inventory_query,
    engine
)


print("\n✓ Inventory data loaded.")

print(
    f"Rows: "
    f"{len(inventory_df):,}"
)


print(
    f"Unique Store × Product combinations: "
    f"{inventory_df[['store_key', 'product_key']].drop_duplicates().shape[0]:,}"
)


# ============================================================
# 4. LOAD LATEST ML FEATURES
# ============================================================

print("\n" + "=" * 70)
print("LOADING FORECASTING FEATURES")
print("=" * 70)


features_path = (
    "../data/processed/"
    "stocksense_ml_timeseries_features.csv"
)


features_df = pd.read_csv(
    features_path,
    parse_dates=["sales_date"]
)


print(
    f"\n✓ ML feature dataset loaded."
)


print(
    f"Rows: "
    f"{len(features_df):,}"
)


# Keep the latest available record
# for each Store × Product combination

latest_features_df = (

    features_df
    .sort_values("sales_date")
    .groupby(
        [
            "store_key",
            "product_key"
        ],
        as_index=False
    )
    .tail(1)

)


print(
    f"\n✓ Latest Store × Product feature records selected."
)


print(
    f"Rows: "
    f"{len(latest_features_df):,}"
)


# ============================================================
# 5. LOAD TRAINED MODEL
# ============================================================

print("\n" + "=" * 70)
print("LOADING TRAINED FORECASTING MODEL")
print("=" * 70)


with open(
    MODEL_PATH,
    "rb"
) as file:

    model = pickle.load(
        file
    )


with open(
    FEATURE_PATH,
    "rb"
) as file:

    model_features = pickle.load(
        file
    )


print(
    "\n✓ Forecasting model loaded."
)


print(
    "✓ Model feature list loaded."
)


print(
    f"\nNumber of model features: "
    f"{len(model_features)}"
)


# ============================================================
# 6. PREPARE FORECAST FEATURES
# ============================================================

print("\n" + "=" * 70)
print("PREPARING FORECAST FEATURES")
print("=" * 70)


X_forecast = latest_features_df[
    model_features
].copy()


# Encode categorical features if necessary

for column in X_forecast.columns:

    if (
        X_forecast[column].dtype == "object"
    ):

        X_forecast[column] = (
            X_forecast[column]
            .astype("category")
            .cat.codes
        )


# Convert to numeric

for column in X_forecast.columns:

    X_forecast[column] = pd.to_numeric(
        X_forecast[column],
        errors="coerce"
    )


# Handle missing values

X_forecast = X_forecast.fillna(0)


print(
    "\n✓ Forecast features prepared."
)


print(
    f"Missing values: "
    f"{X_forecast.isnull().sum().sum():,}"
)


# ============================================================
# 7. GENERATE 7-DAY DEMAND FORECAST
# ============================================================

print("\n" + "=" * 70)
print("GENERATING DEMAND FORECASTS")
print("=" * 70)


forecast_predictions = model.predict(
    X_forecast
)


# Demand cannot be negative

forecast_predictions = np.maximum(
    forecast_predictions,
    0
)


latest_features_df[
    "forecast_demand_7d"
] = forecast_predictions


# Calculate daily demand estimate

latest_features_df[
    "forecast_daily_demand"
] = (

    latest_features_df[
        "forecast_demand_7d"
    ]

    /

    FORECAST_HORIZON

)


print(
    "\n✓ 7-day demand forecasts generated."
)


print(
    f"\nAverage 7-day forecast: "
    f"{latest_features_df['forecast_demand_7d'].mean():.2f}"
)


# ============================================================
# 8. MERGE INVENTORY + FORECAST
# ============================================================

print("\n" + "=" * 70)
print("COMBINING INVENTORY AND FORECAST DATA")
print("=" * 70)


optimization_df = inventory_df.merge(

    latest_features_df[

        [

            "store_key",
            "product_key",
            "sales_date",
            "forecast_demand_7d",
            "forecast_daily_demand",
            "rolling_std_30",
            "rolling_mean_30",
            "demand_cv_30"

        ]

    ],

    on=[
        "store_key",
        "product_key"
    ],

    how="left"

)


print(
    f"\n✓ Inventory and forecast data combined."
)


print(
    f"Rows: "
    f"{len(optimization_df):,}"
)


# ============================================================
# 9. HANDLE MISSING FORECASTS
# ============================================================

print("\n" + "=" * 70)
print("HANDLING MISSING FORECASTS")
print("=" * 70)


forecast_columns = [

    "forecast_demand_7d",

    "forecast_daily_demand",

    "rolling_std_30",

    "rolling_mean_30",

    "demand_cv_30"

]


optimization_df[
    forecast_columns
] = (

    optimization_df[
        forecast_columns
    ]

    .fillna(0)

)


missing_forecasts = (

    optimization_df[
        "forecast_demand_7d"
    ]

    .isnull()

    .sum()

)


print(
    f"\nRemaining missing forecasts: "
    f"{missing_forecasts:,}"
)


# ============================================================
# 10. CALCULATE SAFETY STOCK
# ============================================================

print("\n" + "=" * 70)
print("CALCULATING SAFETY STOCK")
print("=" * 70)


# Safety Stock Formula:
#
# Safety Stock =
# Z-score × Demand Standard Deviation × sqrt(Lead Time)

optimization_df[
    "safety_stock"
] = (

    SERVICE_LEVEL_Z

    *

    optimization_df[
        "rolling_std_30"
    ]

    *

    np.sqrt(
        LEAD_TIME_DAYS
    )

)


optimization_df[
    "safety_stock"
] = (

    optimization_df[
        "safety_stock"
    ]

    .fillna(0)

    .clip(
        lower=0
    )

)


# ============================================================
# 11. CALCULATE REORDER POINT
# ============================================================

print("\n" + "=" * 70)
print("CALCULATING REORDER POINT")
print("=" * 70)


# Reorder Point =
#
# Expected demand during lead time
# +
# Safety Stock


optimization_df[
    "lead_time_demand"
] = (

    optimization_df[
        "forecast_daily_demand"
    ]

    *

    LEAD_TIME_DAYS

)


optimization_df[
    "reorder_point"
] = (

    optimization_df[
        "lead_time_demand"
    ]

    +

    optimization_df[
        "safety_stock"
    ]

)


# ============================================================
# 12. CALCULATE INVENTORY COVERAGE
# ============================================================

print("\n" + "=" * 70)
print("CALCULATING INVENTORY COVERAGE")
print("=" * 70)


optimization_df[
    "days_of_inventory"
] = np.where(

    optimization_df[
        "forecast_daily_demand"
    ] > 0,

    optimization_df[
        "qty_on_hand"
    ]

    /

    optimization_df[
        "forecast_daily_demand"
    ],

    np.nan

)


# ============================================================
# 13. CALCULATE INVENTORY GAP
# ============================================================

print("\n" + "=" * 70)
print("CALCULATING INVENTORY GAP")
print("=" * 70)


optimization_df[
    "inventory_gap"
] = (

    optimization_df[
        "qty_on_hand"
    ]

    -

    optimization_df[
        "reorder_point"
    ]

)


# ============================================================
# 14. INVENTORY RISK CLASSIFICATION
# ============================================================

print("\n" + "=" * 70)
print("CLASSIFYING INVENTORY RISK")
print("=" * 70)


def classify_inventory_risk(row):

    qty_on_hand = row[
        "qty_on_hand"
    ]

    reorder_point = row[
        "reorder_point"
    ]

    days_of_inventory = row[
        "days_of_inventory"
    ]


    # Critical stockout risk

    if qty_on_hand <= 0:

        return "CRITICAL"


    # Below reorder point

    if qty_on_hand <= reorder_point:

        return "HIGH RISK"


    # Low inventory coverage

    if (
        pd.notna(days_of_inventory)
        and
        days_of_inventory < LEAD_TIME_DAYS
    ):

        return "HIGH RISK"


    # Monitor

    if (
        pd.notna(days_of_inventory)
        and
        days_of_inventory < 21
    ):

        return "MONITOR"


    # Excess inventory

    if (
        pd.notna(days_of_inventory)
        and
        days_of_inventory > 90
    ):

        return "EXCESS STOCK"


    return "HEALTHY"


optimization_df[
    "inventory_risk"
] = optimization_df.apply(
    classify_inventory_risk,
    axis=1
)


# ============================================================
# 15. RECOMMENDED ACTION
# ============================================================

print("\n" + "=" * 70)
print("GENERATING RECOMMENDED ACTIONS")
print("=" * 70)


def generate_recommendation(row):

    risk = row[
        "inventory_risk"
    ]

    inventory_gap = row[
        "inventory_gap"
    ]


    if risk == "CRITICAL":

        return "URGENT REPLENISHMENT"


    elif risk == "HIGH RISK":

        return "REORDER NOW"


    elif risk == "MONITOR":

        return "MONITOR INVENTORY"


    elif risk == "EXCESS STOCK":

        return "REDUCE / REDISTRIBUTE STOCK"


    else:

        return "NO ACTION REQUIRED"


optimization_df[
    "recommended_action"
] = optimization_df.apply(
    generate_recommendation,
    axis=1
)


# ============================================================
# 16. CALCULATE RECOMMENDED REORDER QUANTITY
# ============================================================

print("\n" + "=" * 70)
print("CALCULATING REORDER QUANTITY")
print("=" * 70)


# Reorder quantity ensures
# inventory reaches reorder point

optimization_df[
    "recommended_reorder_qty"
] = np.where(

    optimization_df[
        "inventory_risk"
    ].isin(
        [
            "CRITICAL",
            "HIGH RISK"
        ]
    ),

    np.ceil(

        optimization_df[
            "reorder_point"
        ]

        -

        optimization_df[
            "qty_on_hand"
        ]

    ).clip(
        lower=0
    ),

    0

)


# ============================================================
# 17. ADD INVENTORY VALUE AT RISK
# ============================================================

print("\n" + "=" * 70)
print("CALCULATING INVENTORY VALUE AT RISK")
print("=" * 70)


optimization_df[
    "inventory_value"
] = optimization_df[
    "cost_of_stocks"
].fillna(0)


optimization_df[
    "inventory_value_at_risk"
] = np.where(

    optimization_df[
        "inventory_risk"
    ].isin(
        [
            "CRITICAL",
            "HIGH RISK"
        ]
    ),

    optimization_df[
        "inventory_value"
    ],

    0

)


# ============================================================
# 18. FINAL VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("FINAL VALIDATION")
print("=" * 70)


print(
    f"\nFinal rows: "
    f"{len(optimization_df):,}"
)


print(
    f"Duplicate rows: "
    f"{optimization_df.duplicated().sum():,}"
)


print(
    "\nInventory Risk Distribution:"
)


print(
    optimization_df[
        "inventory_risk"
    ]

    .value_counts()

)


print(
    "\nRecommended Action Distribution:"
)


print(
    optimization_df[
        "recommended_action"
    ]

    .value_counts()

)


# ============================================================
# 19. SAVE INVENTORY INTELLIGENCE DATASET
# ============================================================

print("\n" + "=" * 70)
print("SAVING INVENTORY INTELLIGENCE DATASET")
print("=" * 70)


optimization_df.to_csv(

    OUTPUT_PATH,

    index=False

)


print(
    f"\n✓ Inventory optimization dataset saved:"
    f"\n{OUTPUT_PATH}"
)


# ============================================================
# 20. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("STOCKSENSE AI INVENTORY OPTIMIZATION COMPLETE")
print("=" * 70)


print(
    f"\nTotal inventory records: "
    f"{len(optimization_df):,}"
)


print(
    f"Critical items: "
    f"{(optimization_df['inventory_risk'] == 'CRITICAL').sum():,}"
)


print(
    f"High-risk items: "
    f"{(optimization_df['inventory_risk'] == 'HIGH RISK').sum():,}"
)


print(
    f"Monitor items: "
    f"{(optimization_df['inventory_risk'] == 'MONITOR').sum():,}"
)


print(
    f"Healthy items: "
    f"{(optimization_df['inventory_risk'] == 'HEALTHY').sum():,}"
)


print(
    f"Excess stock items: "
    f"{(optimization_df['inventory_risk'] == 'EXCESS STOCK').sum():,}"
)


print(
    "\nGenerated file:"
)


print(
    f"• {OUTPUT_PATH}"
)


print(
    "\nNext step:"
    "\n05_business_recommendations.py"
)
