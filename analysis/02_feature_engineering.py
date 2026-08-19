# ============================================================
# StockSense AI
# Phase 4 - Feature Engineering
# File: 02_feature_engineering.py
# ============================================================

import os
import pandas as pd
import numpy as np

from sqlalchemy import create_engine, text


# ============================================================
# 1. CONFIGURATION
# ============================================================

print("=" * 70)
print("STOCKSENSE AI - FEATURE ENGINEERING")
print("=" * 70)


# PostgreSQL Configuration
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "stocksense_ai"
DB_USER = "postgres"
DB_PASSWORD = "yash7046"


# Output directory
OUTPUT_DIR = "../data/processed"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# 2. DATABASE CONNECTION
# ============================================================

connection_string = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(connection_string)


try:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    print("\n✓ PostgreSQL connection successful.")

except Exception as e:
    print("\n✗ Database connection failed.")
    raise e


# ============================================================
# 3. LOAD DEMAND DATA
# ============================================================

print("\n" + "=" * 70)
print("LOADING DEMAND DATA")
print("=" * 70)


demand_query = """
SELECT
    sales_date,

    store_key,
    store_id,
    store_type,

    product_key,
    product_no,
    product_description,
    product_division,
    product_category,
    product_subcategory,
    product_segment,

    gross_units_sold,
    returned_units,
    net_units_sold,

    gross_revenue,
    returned_revenue,
    net_revenue,

    transactions

FROM analytics.vw_demand_features

ORDER BY
    store_key,
    product_key,
    sales_date;
"""


df = pd.read_sql(
    demand_query,
    engine,
    parse_dates=["sales_date"]
)


print(f"\n✓ Dataset loaded successfully.")
print(f"Rows    : {df.shape[0]:,}")
print(f"Columns : {df.shape[1]:,}")

print(f"\nDate Range:")
print(f"Start : {df['sales_date'].min()}")
print(f"End   : {df['sales_date'].max()}")

print(
    f"\nStore × Product combinations : "
    f"{df[['store_key', 'product_key']].drop_duplicates().shape[0]:,}"
)


# ============================================================
# 4. SORT DATA
# ============================================================

print("\n" + "=" * 70)
print("SORTING DATA")
print("=" * 70)


df = df.sort_values(
    [
        "store_key",
        "product_key",
        "sales_date"
    ]
).reset_index(drop=True)


print("✓ Data sorted by Store → Product → Date.")


# ============================================================
# 5. CALENDAR FEATURES
# ============================================================

print("\n" + "=" * 70)
print("CREATING CALENDAR FEATURES")
print("=" * 70)


df["year"] = df["sales_date"].dt.year

df["month"] = df["sales_date"].dt.month

df["quarter"] = df["sales_date"].dt.quarter

df["day_of_week"] = df["sales_date"].dt.dayofweek

df["day_of_month"] = df["sales_date"].dt.day

df["week_of_year"] = (
    df["sales_date"]
    .dt.isocalendar()
    .week
    .astype(int)
)

df["is_weekend"] = (
    df["day_of_week"] >= 5
).astype(int)


print("✓ Calendar features created.")


# ============================================================
# 6. RETURN FEATURES
# ============================================================

print("\n" + "=" * 70)
print("CREATING RETURN FEATURES")
print("=" * 70)


df["return_rate"] = (
    df["returned_units"]
    /
    df["gross_units_sold"].replace(0, np.nan)
)

df["return_rate"] = (
    df["return_rate"]
    .replace([np.inf, -np.inf], np.nan)
    .fillna(0)
)


df["revenue_return_rate"] = (
    df["returned_revenue"]
    /
    df["gross_revenue"].replace(0, np.nan)
)

df["revenue_return_rate"] = (
    df["revenue_return_rate"]
    .replace([np.inf, -np.inf], np.nan)
    .fillna(0)
)


print("✓ Return features created.")


# ============================================================
# 7. LAG FEATURES
# ============================================================

print("\n" + "=" * 70)
print("CREATING LAG FEATURES")
print("=" * 70)


GROUP_COLS = [
    "store_key",
    "product_key"
]


for lag in [1, 7, 14, 30]:

    df[f"lag_{lag}"] = (
        df
        .groupby(GROUP_COLS)["gross_units_sold"]
        .shift(lag)
    )

    print(f"✓ Created lag_{lag}")


# ============================================================
# 8. ROLLING DEMAND FEATURES
# ============================================================

print("\n" + "=" * 70)
print("CREATING ROLLING DEMAND FEATURES")
print("=" * 70)


for window in [7, 14, 30]:

    # Shift by 1 to prevent target leakage.
    # Today's demand must not be used to predict today's target.

    df[f"rolling_mean_{window}"] = (
        df
        .groupby(GROUP_COLS)["gross_units_sold"]
        .transform(
            lambda x: (
                x
                .shift(1)
                .rolling(
                    window=window,
                    min_periods=window
                )
                .mean()
            )
        )
    )


    df[f"rolling_std_{window}"] = (
        df
        .groupby(GROUP_COLS)["gross_units_sold"]
        .transform(
            lambda x: (
                x
                .shift(1)
                .rolling(
                    window=window,
                    min_periods=window
                )
                .std()
            )
        )
    )


    print(
        f"✓ Created rolling_mean_{window} "
        f"and rolling_std_{window}"
    )


# ============================================================
# 9. DEMAND VOLATILITY
# ============================================================

print("\n" + "=" * 70)
print("CREATING DEMAND VOLATILITY FEATURES")
print("=" * 70)


df["demand_cv_7"] = (
    df["rolling_std_7"]
    /
    df["rolling_mean_7"].replace(0, np.nan)
)

df["demand_cv_30"] = (
    df["rolling_std_30"]
    /
    df["rolling_mean_30"].replace(0, np.nan)
)


df["demand_cv_7"] = (
    df["demand_cv_7"]
    .replace([np.inf, -np.inf], np.nan)
)

df["demand_cv_30"] = (
    df["demand_cv_30"]
    .replace([np.inf, -np.inf], np.nan)
)


print("✓ Demand volatility features created.")


# ============================================================
# 10. PRODUCT-LEVEL DEMAND FEATURES
# ============================================================

print("\n" + "=" * 70)
print("CREATING PRODUCT DEMAND FEATURES")
print("=" * 70)


df["product_avg_demand"] = (
    df
    .groupby("product_key")["gross_units_sold"]
    .transform(
        lambda x: (
            x
            .shift(1)
            .expanding()
            .mean()
        )
    )
)


df["store_avg_demand"] = (
    df
    .groupby("store_key")["gross_units_sold"]
    .transform(
        lambda x: (
            x
            .shift(1)
            .expanding()
            .mean()
        )
    )
)


print("✓ Product and store demand features created.")


# ============================================================
# 11. FUTURE DEMAND TARGET
# ============================================================

print("\n" + "=" * 70)
print("CREATING FORECAST TARGET")
print("=" * 70)


FORECAST_HORIZON = 7


df["target_demand_7d"] = (
    df
    .groupby(GROUP_COLS)["gross_units_sold"]
    .transform(
        lambda x: (
            x
            .shift(-1)
            .rolling(
                window=FORECAST_HORIZON,
                min_periods=FORECAST_HORIZON
            )
            .sum()
        )
    )
)


print(
    f"✓ Created {FORECAST_HORIZON}-day "
    f"future demand target."
)


# ============================================================
# 12. DATA QUALITY CHECK
# ============================================================

print("\n" + "=" * 70)
print("FEATURE DATA QUALITY CHECK")
print("=" * 70)


print("\nMissing values before cleaning:")

missing_before = (
    df
    .isnull()
    .sum()
)

print(
    missing_before[
        missing_before > 0
    ]
)


# ============================================================
# 13. REMOVE INCOMPLETE ROWS
# ============================================================

print("\n" + "=" * 70)
print("REMOVING INCOMPLETE FEATURE ROWS")
print("=" * 70)


rows_before = len(df)


required_features = [

    "lag_1",
    "lag_7",
    "lag_14",
    "lag_30",

    "rolling_mean_7",
    "rolling_std_7",

    "rolling_mean_14",
    "rolling_std_14",

    "rolling_mean_30",
    "rolling_std_30",

    "target_demand_7d"
]


df_model = df.dropna(
    subset=required_features
).copy()


rows_after = len(df_model)


print(f"\nRows before : {rows_before:,}")
print(f"Rows after  : {rows_after:,}")
print(
    f"Rows removed: "
    f"{rows_before - rows_after:,}"
)


# ============================================================
# 14. FINAL DATASET VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("FINAL DATASET VALIDATION")
print("=" * 70)


print(f"\nFinal rows    : {df_model.shape[0]:,}")
print(f"Final columns : {df_model.shape[1]:,}")


print(
    f"\nRemaining missing values: "
    f"{df_model.isnull().sum().sum():,}"
)


print(
    f"Duplicate rows: "
    f"{df_model.duplicated().sum():,}"
)


print(
    f"Negative target values: "
    f"{(df_model['target_demand_7d'] < 0).sum():,}"
)


print("\nTarget Statistics:")

print(
    df_model["target_demand_7d"]
    .describe()
)


# ============================================================
# 15. SAVE ML DATASET
# ============================================================

print("\n" + "=" * 70)
print("SAVING ML DATASET")
print("=" * 70)


output_path = os.path.join(
    OUTPUT_DIR,
    "stocksense_ml_features.csv"
)


df_model.to_csv(
    output_path,
    index=False
)


print("\n✓ Feature engineering completed successfully.")

print(f"\nSaved file:")
print(output_path)


print("\n" + "=" * 70)
print("STOCKSENSE AI FEATURE ENGINEERING COMPLETE")
print("=" * 70)
