# ============================================================
# StockSense AI
# Phase 5 - Demand Forecasting Model
# File: 03_demand_forecasting_model.py
# ============================================================

import os
import warnings
import pandas as pd
import numpy as np
import joblib

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor,
    RandomForestRegressor,
    HistGradientBoostingRegressor
)

warnings.filterwarnings("ignore")


# ============================================================
# 1. CONFIGURATION
# ============================================================

print("=" * 70)
print("STOCKSENSE AI - DEMAND FORECASTING MODEL")
print("=" * 70)


DATA_PATH = "../data/processed/stocksense_ml_features.csv"

MODEL_DIR = "../models"
RESULT_DIR = "../results"

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)


# ============================================================
# 2. LOAD FEATURE DATASET
# ============================================================

print("\n" + "=" * 70)
print("LOADING ML FEATURE DATASET")
print("=" * 70)


df = pd.read_csv(
    DATA_PATH,
    parse_dates=["sales_date"]
)


print(f"\n✓ Dataset loaded successfully.")
print(f"Rows    : {df.shape[0]:,}")
print(f"Columns : {df.shape[1]:,}")

print(f"\nDate range:")
print(f"Start: {df['sales_date'].min()}")
print(f"End  : {df['sales_date'].max()}")


# ============================================================
# 3. SORT DATA TEMPORALLY
# ============================================================

df = df.sort_values("sales_date").reset_index(drop=True)

print("\n✓ Dataset sorted chronologically.")


# ============================================================
# 4. DEFINE TARGET
# ============================================================

TARGET = "target_demand_7d"

y = df[TARGET].copy()


# ============================================================
# 5. DEFINE FEATURES
# ============================================================

print("\n" + "=" * 70)
print("SELECTING MODEL FEATURES")
print("=" * 70)


# Features that should NOT be used directly

EXCLUDE_COLUMNS = [

    # Target
    "target_demand_7d",

    # Date / identifiers
    "sales_date",
    "store_key",
    "product_key",

    # Business identifiers / descriptions
    "store_id",
    "product_no",
    "product_description",

    # Potentially high-cardinality categories
    "product_division",
    "product_category",
    "product_subcategory",
    "product_segment",

    # Current-day outcome variables
    # These are excluded to reduce leakage risk.
    "gross_units_sold",
    "returned_units",
    "net_units_sold",

    "gross_revenue",
    "returned_revenue",
    "net_revenue",

    "transactions"
]


FEATURE_COLUMNS = [
    column
    for column in df.columns
    if column not in EXCLUDE_COLUMNS
]


X = df[FEATURE_COLUMNS].copy()


print(f"\nNumber of features: {len(FEATURE_COLUMNS)}")

print("\nFeatures used:")

for feature in FEATURE_COLUMNS:
    print(f"  • {feature}")


# ============================================================
# 6. FINAL FEATURE CLEANING
# ============================================================

print("\n" + "=" * 70)
print("FEATURE VALIDATION AND ENCODING")
print("=" * 70)


# ------------------------------------------------------------
# Convert boolean columns to integers
# ------------------------------------------------------------

for column in X.columns:

    if X[column].dtype == bool:

        X[column] = X[column].astype(int)


# ------------------------------------------------------------
# Identify non-numeric columns
# ------------------------------------------------------------

non_numeric = X.select_dtypes(
    exclude=["number"]
).columns.tolist()


print("\nNon-numeric features detected:")

if non_numeric:

    for column in non_numeric:
        print(f"  • {column}")

else:

    print("  None")


# ------------------------------------------------------------
# One-Hot Encode Categorical Features
# ------------------------------------------------------------

if non_numeric:

    X = pd.get_dummies(
        X,
        columns=non_numeric,
        drop_first=False,
        dtype=int
    )

    print("\n✓ Categorical features encoded.")


# ------------------------------------------------------------
# Replace infinite values
# ------------------------------------------------------------

X = X.replace(
    [np.inf, -np.inf],
    np.nan
)


# ------------------------------------------------------------
# Fill missing values
# ------------------------------------------------------------

X = X.fillna(0)


# IMPORTANT:
# Update feature list after encoding
FEATURE_COLUMNS = X.columns.tolist()


print("\n✓ Feature validation completed.")

print(
    f"\nFinal number of features: "
    f"{len(FEATURE_COLUMNS)}"
)

print(
    f"Remaining missing values: "
    f"{X.isnull().sum().sum():,}"
)


# ============================================================
# 7. TIME-BASED TRAIN / VALIDATION / TEST SPLIT
# ============================================================

print("\n" + "=" * 70)
print("CREATING TIME-BASED DATA SPLITS")
print("=" * 70)


unique_dates = np.sort(
    df["sales_date"].unique()
)

n_dates = len(unique_dates)


train_end = int(n_dates * 0.70)

validation_end = int(n_dates * 0.85)


train_dates = unique_dates[:train_end]

validation_dates = unique_dates[
    train_end:validation_end
]

test_dates = unique_dates[
    validation_end:
]


train_mask = df["sales_date"].isin(train_dates)

validation_mask = df["sales_date"].isin(validation_dates)

test_mask = df["sales_date"].isin(test_dates)


X_train = X.loc[train_mask]

y_train = y.loc[train_mask]

X_validation = X.loc[validation_mask]

y_validation = y.loc[validation_mask]

X_test = X.loc[test_mask]

y_test = y.loc[test_mask]


print(f"\nTrain period:")
print(
    f"{df.loc[train_mask, 'sales_date'].min()} "
    f"to "
    f"{df.loc[train_mask, 'sales_date'].max()}"
)

print(f"Rows: {len(X_train):,}")


print(f"\nValidation period:")
print(
    f"{df.loc[validation_mask, 'sales_date'].min()} "
    f"to "
    f"{df.loc[validation_mask, 'sales_date'].max()}"
)

print(f"Rows: {len(X_validation):,}")


print(f"\nTest period:")
print(
    f"{df.loc[test_mask, 'sales_date'].min()} "
    f"to "
    f"{df.loc[test_mask, 'sales_date'].max()}"
)

print(f"Rows: {len(X_test):,}")


# ============================================================
# 8. EVALUATION FUNCTION
# ============================================================

def evaluate_model(
    model_name,
    y_true,
    predictions
):

    mae = mean_absolute_error(
        y_true,
        predictions
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_true,
            predictions
        )
    )

    r2 = r2_score(
        y_true,
        predictions
    )


    return {
        "Model": model_name,
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2
    }


# ============================================================
# 9. BASELINE MODEL
# ============================================================

print("\n" + "=" * 70)
print("TRAINING BASELINE MODEL")
print("=" * 70)


# Baseline:
# Predict next 7-day demand using
# recent 7-day average × 7

baseline_predictions = (
    X_validation["rolling_mean_7"] * 7
)


baseline_results = evaluate_model(
    "Naive 7-Day Demand Baseline",
    y_validation,
    baseline_predictions
)


print("\nBaseline Results:")

for key, value in baseline_results.items():

    if key != "Model":

        print(
            f"{key}: "
            f"{value:,.4f}"
        )


# ============================================================
# 10. TRAIN MODELS
# ============================================================

print("\n" + "=" * 70)
print("TRAINING FORECASTING MODELS")
print("=" * 70)


models = {

    "Random Forest": RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    ),

    "Gradient Boosting": GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=5,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42
    ),

    "Hist Gradient Boosting": HistGradientBoostingRegressor(
        max_iter=300,
        learning_rate=0.05,
        max_leaf_nodes=31,
        random_state=42
    )
}


results = [
    baseline_results
]


trained_models = {}


for model_name, model in models.items():

    print(f"\nTraining: {model_name}")

    model.fit(
        X_train,
        y_train
    )


    validation_predictions = model.predict(
        X_validation
    )


    model_results = evaluate_model(
        model_name,
        y_validation,
        validation_predictions
    )


    results.append(
        model_results
    )


    trained_models[
        model_name
    ] = model


    print(
        f"MAE  : {model_results['MAE']:,.4f}"
    )

    print(
        f"RMSE : {model_results['RMSE']:,.4f}"
    )

    print(
        f"R²   : {model_results['R2']:,.4f}"
    )


# ============================================================
# 11. MODEL COMPARISON
# ============================================================

print("\n" + "=" * 70)
print("MODEL COMPARISON")
print("=" * 70)


results_df = pd.DataFrame(
    results
)


results_df = results_df.sort_values(
    "RMSE"
).reset_index(
    drop=True
)


print("\n")
print(results_df)


results_path = os.path.join(
    RESULT_DIR,
    "model_comparison.csv"
)


results_df.to_csv(
    results_path,
    index=False
)


print(
    f"\n✓ Model comparison saved to:"
    f"\n{results_path}"
)


# ============================================================
# 12. SELECT BEST MODEL
# ============================================================

print("\n" + "=" * 70)
print("SELECTING BEST MODEL")
print("=" * 70)


model_results_only = results_df[
    results_df["Model"] !=
    "Naive 7-Day Demand Baseline"
]


best_model_name = (
    model_results_only
    .iloc[0]["Model"]
)


best_model = trained_models[
    best_model_name
]


print(
    f"\n✓ Best model: "
    f"{best_model_name}"
)


# ============================================================
# 13. RETRAIN BEST MODEL
# ============================================================

print("\n" + "=" * 70)
print("RETRAINING BEST MODEL")
print("=" * 70)


# Combine train + validation data

X_train_final = pd.concat(
    [
        X_train,
        X_validation
    ]
)

y_train_final = pd.concat(
    [
        y_train,
        y_validation
    ]
)


# Refit on historical training data

best_model.fit(
    X_train_final,
    y_train_final
)


print(
    "✓ Best model retrained on "
    "Train + Validation data."
)


# ============================================================
# 14. FINAL TEST EVALUATION
# ============================================================

print("\n" + "=" * 70)
print("FINAL TEST EVALUATION")
print("=" * 70)


test_predictions = best_model.predict(
    X_test
)


test_results = evaluate_model(
    best_model_name,
    y_test,
    test_predictions
)


print(
    f"\nBest Model: "
    f"{best_model_name}"
)

print(
    f"MAE  : "
    f"{test_results['MAE']:,.4f}"
)

print(
    f"RMSE : "
    f"{test_results['RMSE']:,.4f}"
)

print(
    f"R²   : "
    f"{test_results['R2']:,.4f}"
)


# ============================================================
# 15. FEATURE IMPORTANCE
# ============================================================

print("\n" + "=" * 70)
print("FEATURE IMPORTANCE")
print("=" * 70)


if hasattr(
    best_model,
    "feature_importances_"
):

    feature_importance = pd.DataFrame({

        "feature": FEATURE_COLUMNS,

        "importance":
        best_model.feature_importances_

    })


    feature_importance = (
        feature_importance
        .sort_values(
            "importance",
            ascending=False
        )
    )


    print(
        "\nTop 15 Most Important Features:\n"
    )

    print(
        feature_importance
        .head(15)
    )


    importance_path = os.path.join(
        RESULT_DIR,
        "feature_importance.csv"
    )


    feature_importance.to_csv(
        importance_path,
        index=False
    )


else:

    print(
        "\nFeature importance is not directly "
        "available for this model."
    )


# ============================================================
# 16. SAVE MODEL AND FEATURES
# ============================================================

print("\n" + "=" * 70)
print("SAVING MODEL ARTIFACTS")
print("=" * 70)


model_path = os.path.join(
    MODEL_DIR,
    "best_demand_forecasting_model.pkl"
)


feature_path = os.path.join(
    MODEL_DIR,
    "model_features.pkl"
)


joblib.dump(
    best_model,
    model_path
)


joblib.dump(
    FEATURE_COLUMNS,
    feature_path
)


print(
    f"\n✓ Model saved:"
    f"\n{model_path}"
)

print(
    f"\n✓ Feature list saved:"
    f"\n{feature_path}"
)


# ============================================================
# 17. SAVE TEST PREDICTIONS
# ============================================================

print("\n" + "=" * 70)
print("SAVING TEST PREDICTIONS")
print("=" * 70)


test_output = df.loc[
    test_mask,
    [
        "sales_date",
        "store_id",
        "product_no",
        "product_description",
        TARGET
    ]
].copy()


test_output["predicted_demand_7d"] = (
    test_predictions
)


test_output = test_output.rename(
    columns={
        TARGET:
        "actual_demand_7d"
    }
)


test_output["absolute_error"] = (
    np.abs(
        test_output["actual_demand_7d"]
        -
        test_output["predicted_demand_7d"]
    )
)


prediction_path = os.path.join(
    RESULT_DIR,
    "test_predictions.csv"
)


test_output.to_csv(
    prediction_path,
    index=False
)


print(
    f"\n✓ Test predictions saved:"
    f"\n{prediction_path}"
)


# ============================================================
# 18. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("STOCKSENSE AI FORECASTING COMPLETE")
print("=" * 70)


print(
    f"\nBest Model: "
    f"{best_model_name}"
)

print(
    f"Test MAE: "
    f"{test_results['MAE']:,.4f}"
)

print(
    f"Test RMSE: "
    f"{test_results['RMSE']:,.4f}"
)

print(
    f"Test R²: "
    f"{test_results['R2']:,.4f}"
)

print("\nGenerated files:")

print(f"• {results_path}")

print(f"• {model_path}")

print(f"• {feature_path}")

print(f"• {prediction_path}")
