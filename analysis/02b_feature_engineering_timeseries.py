# ============================================================
# StockSense AI
# Phase 4B - Time Series Feature Engineering
# File: 02b_feature_engineering_timeseries.py
# ============================================================

import os
import pandas as pd
import numpy as np

from sqlalchemy import create_engine, text


# ============================================================
# 1. CONFIGURATION
# ============================================================

print("=" * 70)
print("STOCKSENSE AI - TIME SERIES FEATURE ENGINEERING")
print("=" * 70)


# PostgreSQL Configuration
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "stocksense_ai"
DB_USER = "aiubvaibbibvv"
DB_PASSWORD = "Enter your DB password"


# Output directory
OUTPUT_DIR = "../data/processed"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# Forecast horizon
FORECAST_HORIZON = 7


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
# 3. LOAD DAILY DEMAND DATA
# ============================================================

print("\n" + "=" * 70)
print("LOADING DAILY DEMAND DATA")
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

# Save original row count before transforming df
ORIGINAL_DEMAND_ROW_COUNT = len(df)
print(f"DEBUG - original_rows immediately after loading: {ORIGINAL_DEMAND_ROW_COUNT:,}")
print("\n✓ Original demand data loaded.")

print(f"Rows    : {ORIGINAL_DEMAND_ROW_COUNT:,}")
print(f"Columns : {df.shape[1]:,}")

print(
    f"\nDate range:"
    f"\nStart : {df['sales_date'].min().date()}"
    f"\nEnd   : {df['sales_date'].max().date()}"
)


print(
    f"\nStore × Product combinations: "
    f"{df[['store_key', 'product_key']].drop_duplicates().shape[0]:,}"
)


# ============================================================
# 4. DATA PREPARATION
# ============================================================

print("\n" + "=" * 70)
print("PREPARING DAILY TIME SERIES")
print("=" * 70)


df = df.sort_values(
    [
        "store_key",
        "product_key",
        "sales_date"
    ]
).reset_index(drop=True)


# Ensure numeric demand columns are numeric
numeric_columns = [
    "gross_units_sold",
    "returned_units",
    "net_units_sold",
    "gross_revenue",
    "returned_revenue",
    "net_revenue",
    "transactions"
]


for column in numeric_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    ).fillna(0)


print("✓ Data sorted and numeric columns validated.")


# ============================================================
# 5. CREATE COMPLETE DAILY TIME SERIES - MEMORY EFFICIENT
# ============================================================

print("\n" + "=" * 70)
print("CREATING COMPLETE DAILY TIME SERIES")
print("=" * 70)


GROUP_COLS = [
    "store_key",
    "product_key"
]


# Static columns describing each Store × Product combination

STATIC_COLUMNS = [
    "store_key",
    "store_id",
    "store_type",

    "product_key",
    "product_no",
    "product_description",
    "product_division",
    "product_category",
    "product_subcategory",
    "product_segment"
]


print(
    f"\nStore × Product combinations: "
    f"{df[GROUP_COLS].drop_duplicates().shape[0]:,}"
)


# ============================================================
# BUILD TIME SERIES GROUP BY GROUP
# ============================================================

print("\nBuilding continuous daily time series...")


time_series_list = []

grouped = df.groupby(
    GROUP_COLS,
    sort=False
)


total_groups = len(grouped)


for i, ((store_key, product_key), group) in enumerate(
    grouped,
    start=1
):

    group = group.sort_values(
        "sales_date"
    ).copy()


    # --------------------------------------------------------
    # Combination-specific date range
    # --------------------------------------------------------

    start_date = group[
        "sales_date"
    ].min()


    end_date = group[
        "sales_date"
    ].max()


    full_dates = pd.date_range(
        start=start_date,
        end=end_date,
        freq="D"
    )


    # --------------------------------------------------------
    # Static information
    # --------------------------------------------------------

    static_data = (
        group[STATIC_COLUMNS]
        .iloc[0]
        .to_dict()
    )


    # --------------------------------------------------------
    # Create continuous daily calendar
    # --------------------------------------------------------

    group_calendar = pd.DataFrame({

        "sales_date": full_dates

    })


    # Add static columns

    for column, value in static_data.items():

        group_calendar[column] = value


    # --------------------------------------------------------
    # Merge actual daily sales
    # --------------------------------------------------------

    sales_data = group[
        [
            "sales_date",
            *numeric_columns
        ]
    ].copy()


    group_calendar = group_calendar.merge(

        sales_data,

        on="sales_date",

        how="left"

    )


    # --------------------------------------------------------
    # Missing dates = zero demand
    # --------------------------------------------------------

    for column in numeric_columns:

        group_calendar[column] = (
            group_calendar[column]
            .fillna(0)
        )


    time_series_list.append(
        group_calendar
    )


    # Progress update every 1,000 groups

    if i % 1000 == 0:

        print(
            f"✓ Processed "
            f"{i:,} / {total_groups:,} "
            f"Store × Product combinations"
        )


# ============================================================
# COMBINE TIME SERIES
# ============================================================

print("\nCombining time series...")


df = pd.concat(

    time_series_list,

    ignore_index=True

)


print(
    f"\n✓ Continuous daily time series created."
)


print(
    f"Total rows: "
    f"{len(df):,}"
)


# ============================================================
# 6. VALIDATE TIME SERIES
# ============================================================

print("\n" + "=" * 70)
print("VALIDATING TIME SERIES")
print("=" * 70)


duplicate_dates = (

    df.duplicated(

        subset=[
            "store_key",
            "product_key",
            "sales_date"
        ]

    )

    .sum()

)


print(
    f"\nDuplicate Store × Product × Date rows: "
    f"{duplicate_dates:,}"
)


missing_demand = (

    df[numeric_columns]
    .isna()
    .sum()
    .sum()

)


print(
    f"Remaining missing demand values: "
    f"{missing_demand:,}"
)


# ============================================================
# 7. SORT COMPLETE TIME SERIES
# ============================================================

df = df.sort_values(

    [
        "store_key",
        "product_key",
        "sales_date"
    ]

).reset_index(
    drop=True
)


print(
    "\n✓ Continuous time series sorted successfully."
)

# ============================================================
# 8. SORT TIME SERIES
# ============================================================

df = df.sort_values(
    [
        "store_key",
        "product_key",
        "sales_date"
    ]
).reset_index(drop=True)


GROUP_COLS = [
    "store_key",
    "product_key"
]


print("✓ Continuous time series sorted.")


# ============================================================
# 9. CALENDAR FEATURES
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
# 10. RETURN FEATURES
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
# 11. LAG FEATURES
# ============================================================

print("\n" + "=" * 70)
print("CREATING TRUE DAILY LAG FEATURES")
print("=" * 70)


for lag in [1, 7, 14, 30]:

    df[f"lag_{lag}"] = (
        df
        .groupby(GROUP_COLS)["gross_units_sold"]
        .shift(lag)
    )

    print(f"✓ Created lag_{lag}")


# ============================================================
# 12. ROLLING DEMAND FEATURES
# ============================================================

print("\n" + "=" * 70)
print("CREATING ROLLING DEMAND FEATURES")
print("=" * 70)


for window in [7, 14, 30]:

    # shift(1) ensures today's demand
    # is not used as a feature for today's forecast

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
        f"✓ Created rolling_mean_{window}"
    )

    print(
        f"✓ Created rolling_std_{window}"
    )


# ============================================================
# 13. DEMAND VOLATILITY FEATURES
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
# 14. PRODUCT AND STORE HISTORICAL DEMAND FEATURES
# ============================================================

print("\n" + "=" * 70)
print("CREATING HISTORICAL DEMAND FEATURES")
print("=" * 70)


# Expanding historical average.
# shift(1) prevents current day's demand
# from leaking into today's feature.

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


print("✓ Product historical demand created.")

print("✓ Store historical demand created.")


# ============================================================
# 15. CREATE CORRECT 7-DAY FUTURE DEMAND TARGET
# ============================================================

print("\n" + "=" * 70)
print("CREATING TRUE 7-DAY FUTURE DEMAND TARGET")
print("=" * 70)


def create_future_target(series, horizon=7):
    """
    For each day t:

    target =
    demand(t+1) +
    demand(t+2) +
    ...
    demand(t+horizon)
    """

    return (
        series
        .shift(-1)
        .rolling(
            window=horizon,
            min_periods=horizon
        )
        .sum()
        .shift(-(horizon - 1))
    )


df["target_demand_7d"] = (
    df
    .groupby(GROUP_COLS)["gross_units_sold"]
    .transform(
        lambda x: create_future_target(
            x,
            FORECAST_HORIZON
        )
    )
)


print(
    f"✓ Created future {FORECAST_HORIZON}-day demand target."
)


# ============================================================
# 16. TARGET VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("VALIDATING FORECAST TARGET")
print("=" * 70)


print(
    f"\nMissing target values: "
    f"{df['target_demand_7d'].isna().sum():,}"
)


print(
    f"Negative target values: "
    f"{(df['target_demand_7d'] < 0).sum():,}"
)


print("\nTarget statistics:")

print(
    df["target_demand_7d"]
    .describe()
)


# ============================================================
# 17. REMOVE INCOMPLETE FEATURE ROWS
# ============================================================

print("\n" + "=" * 70)
print("CREATING ML-READY DATASET")
print("=" * 70)


rows_before = len(df)


required_columns = [

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
    subset=required_columns
).copy()


# Replace remaining infinity values
df_model = df_model.replace(
    [np.inf, -np.inf],
    np.nan
)


# Volatility can be undefined when
# historical mean demand is zero.
df_model["demand_cv_7"] = (
    df_model["demand_cv_7"]
    .fillna(0)
)


df_model["demand_cv_30"] = (
    df_model["demand_cv_30"]
    .fillna(0)
)


# Historical averages may only be missing
# at the earliest observations.
df_model["product_avg_demand"] = (
    df_model["product_avg_demand"]
    .fillna(0)
)


df_model["store_avg_demand"] = (
    df_model["store_avg_demand"]
    .fillna(0)
)


rows_after = len(df_model)


print(f"\nRows before cleaning : {rows_before:,}")

print(f"Rows after cleaning  : {rows_after:,}")

print(
    f"Rows removed         : "
    f"{rows_before - rows_after:,}"
)


# ============================================================
# 18. FINAL VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("FINAL DATASET VALIDATION")
print("=" * 70)


print(
    f"\nFinal rows    : "
    f"{df_model.shape[0]:,}"
)

print(
    f"Final columns : "
    f"{df_model.shape[1]:,}"
)


print(
    f"\nDate range:"
    f"\nStart : {df_model['sales_date'].min().date()}"
    f"\nEnd   : {df_model['sales_date'].max().date()}"
)


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


print(
    f"\nUnique Store × Product combinations: "
    f"{df_model[['store_key', 'product_key']].drop_duplicates().shape[0]:,}"
)


# ============================================================
# 19. DATASET QUALITY SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("TIME SERIES QUALITY SUMMARY")
print("=" * 70)


expected_rows = (
    df_model[
        ["store_key", "product_key"]
    ]
    .drop_duplicates()
    .shape[0]
)


print(
    f"\nAverage observations per "
    f"Store × Product combination: "
    f"{len(df_model) / expected_rows:.2f}"
)


# Check chronological uniqueness
duplicate_dates = (
    df_model
    .duplicated(
        subset=[
            "store_key",
            "product_key",
            "sales_date"
        ]
    )
    .sum()
)


print(
    f"Duplicate Store × Product × Date rows: "
    f"{duplicate_dates:,}"
)


# ============================================================
# 20. SAVE IMPROVED ML DATASET
# ============================================================

print("\n" + "=" * 70)
print("SAVING TIME SERIES ML DATASET")
print("=" * 70)


output_path = os.path.join(
    OUTPUT_DIR,
    "stocksense_ml_timeseries_features.csv"
)


df_model.to_csv(
    output_path,
    index=False
)


print("\n✓ Improved ML dataset saved successfully.")

print(
    f"\nFile:"
    f"\n{output_path}"
)


# ============================================================
# 21. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("STOCKSENSE AI TIME SERIES FEATURE ENGINEERING COMPLETE")
print("=" * 70)

print(
    f"\nOriginal demand rows: "
    f"{ORIGINAL_DEMAND_ROW_COUNT:,}"
)

print(
    f"Complete daily time-series rows: "
    f"{len(df):,}"
)


print(
    f"ML-ready rows: "
    f"{len(df_model):,}"
)

print(
    f"\nForecast target: "
    f"Next {FORECAST_HORIZON} days of demand"
)

print(
    "\nNext step:"
    "\n03b_demand_forecasting_model.py"
)
