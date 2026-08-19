# ============================================================
# StockSense AI
# Phase 5 - Demand Forecasting Model
# File: 03b_demand_forecasting_model.py
# ============================================================

import os
import pickle
import warnings

import numpy as np
import pandas as pd

from sklearn.ensemble import (
    HistGradientBoostingRegressor,
    GradientBoostingRegressor
)

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)


warnings.filterwarnings("ignore")


# ============================================================
# 1. CONFIGURATION
# ============================================================

print("=" * 70)
print("STOCKSENSE AI - DEMAND FORECASTING MODEL")
print("=" * 70)


DATA_PATH = "../data/processed/stocksense_ml_timeseries_features.csv"

RESULTS_DIR = "../results"
MODELS_DIR = "../models"

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)


RANDOM_STATE = 42

# Gradient Boosting is expensive on 1.9M rows
MAX_GB_TRAIN_ROWS = 300_000


# ============================================================
# 2. LOAD ML DATASET
# ============================================================

print("\n" + "=" * 70)
print("LOADING ML FEATURE DATASET")
print("=" * 70)


df = pd.read_csv(
    DATA_PATH,
    parse_dates=["sales_date"]
)


print("\n✓ Dataset loaded successfully.")

print(f"Rows    : {len(df):,}")
print(f"Columns : {df.shape[1]:,}")

print(
    f"\nDate range:"
    f"\nStart: {df['sales_date'].min()}"
    f"\nEnd  : {df['sales_date'].max()}"
)


# ============================================================
# 3. SORT CHRONOLOGICALLY
# ============================================================

df = df.sort_values(
    [
        "sales_date",
        "store_key",
        "product_key"
    ]
).reset_index(drop=True)


print("\n✓ Dataset sorted chronologically.")


# ============================================================
# 4. SELECT MODEL FEATURES
# ============================================================

print("\n" + "=" * 70)
print("SELECTING MODEL FEATURES")
print("=" * 70)


feature_columns = [

    # Store information
    "store_type",

    # Calendar features
    "year",
    "month",
    "quarter",
    "day_of_week",
    "day_of_month",
    "week_of_year",
    "is_weekend",

    # Returns
    "return_rate",
    "revenue_return_rate",

    # Lag features
    "lag_1",
    "lag_7",
    "lag_14",
    "lag_30",

    # Rolling demand
    "rolling_mean_7",
    "rolling_std_7",
    "rolling_mean_14",
    "rolling_std_14",
    "rolling_mean_30",
    "rolling_std_30",

    # Demand volatility
    "demand_cv_7",
    "demand_cv_30",

    # Historical demand
    "product_avg_demand",
    "store_avg_demand"
]


TARGET_COLUMN = "target_demand_7d"


print(f"\nNumber of features: {len(feature_columns)}")

print("\nFeatures used:")

for feature in feature_columns:
    print(f"  • {feature}")


# ============================================================
# 5. VALIDATE FEATURES
# ============================================================

print("\n" + "=" * 70)
print("FEATURE VALIDATION AND ENCODING")
print("=" * 70)


missing_features = [

    feature
    for feature in feature_columns
    if feature not in df.columns

]


if missing_features:

    raise ValueError(
        f"Missing model features: {missing_features}"
    )


if TARGET_COLUMN not in df.columns:

    raise ValueError(
        f"Target column '{TARGET_COLUMN}' not found."
    )


# Create model dataframe

model_df = df[
    feature_columns
    +
    [
        TARGET_COLUMN,
        "sales_date"
    ]
].copy()


# Identify categorical columns

categorical_features = model_df[
    feature_columns
].select_dtypes(
    include=["object", "category"]
).columns.tolist()


if categorical_features:

    print("\nCategorical features detected:")

    for column in categorical_features:
        print(f"  • {column}")

        model_df[column] = (
            model_df[column]
            .astype("category")
            .cat.codes
        )

    print("\n✓ Categorical features encoded.")

else:

    print("\n✓ All model features are numeric.")


# Convert all feature columns to numeric

for column in feature_columns:

    model_df[column] = pd.to_numeric(
        model_df[column],
        errors="coerce"
    )


# Final missing-value check

missing_before = model_df[
    feature_columns
].isnull().sum().sum()


if missing_before > 0:

    print(
        f"\nMissing feature values detected: "
        f"{missing_before:,}"
    )

    model_df[
        feature_columns
    ] = model_df[
        feature_columns
    ].fillna(0)

    print("✓ Missing feature values filled with 0.")


# Remove invalid target rows

model_df = model_df.dropna(
    subset=[TARGET_COLUMN]
).copy()


print("\n✓ Feature validation completed.")

print(
    f"\nFinal modeling rows: "
    f"{len(model_df):,}"
)

print(
    f"Remaining missing values: "
    f"{model_df.isnull().sum().sum():,}"
)


# ============================================================
# 6. CREATE TIME-BASED TRAIN / VALIDATION / TEST SPLITS
# ============================================================

print("\n" + "=" * 70)
print("CREATING TIME-BASED DATA SPLITS")
print("=" * 70)


unique_dates = np.sort(
    model_df["sales_date"]
    .dropna()
    .unique()
)


n_dates = len(unique_dates)


train_end_idx = int(
    n_dates * 0.70
)


validation_end_idx = int(
    n_dates * 0.85
)


train_end_date = unique_dates[
    train_end_idx - 1
]


validation_end_date = unique_dates[
    validation_end_idx - 1
]


train_df = model_df[
    model_df["sales_date"] <= train_end_date
].copy()


validation_df = model_df[
    (
        model_df["sales_date"] > train_end_date
    )
    &
    (
        model_df["sales_date"] <= validation_end_date
    )
].copy()


test_df = model_df[
    model_df["sales_date"] > validation_end_date
].copy()


print(
    f"\nTrain period:"
    f"\n{train_df['sales_date'].min().date()} "
    f"to "
    f"{train_df['sales_date'].max().date()}"
)

print(
    f"Rows: {len(train_df):,}"
)


print(
    f"\nValidation period:"
    f"\n{validation_df['sales_date'].min().date()} "
    f"to "
    f"{validation_df['sales_date'].max().date()}"
)

print(
    f"Rows: {len(validation_df):,}"
)


print(
    f"\nTest period:"
    f"\n{test_df['sales_date'].min().date()} "
    f"to "
    f"{test_df['sales_date'].max().date()}"
)

print(
    f"Rows: {len(test_df):,}"
)


# ============================================================
# 7. CREATE X AND y DATASETS
# ============================================================

X_train = train_df[
    feature_columns
]

y_train = train_df[
    TARGET_COLUMN
]


X_validation = validation_df[
    feature_columns
]

y_validation = validation_df[
    TARGET_COLUMN
]


X_test = test_df[
    feature_columns
]

y_test = test_df[
    TARGET_COLUMN
]


# ============================================================
# 8. EVALUATION FUNCTION
# ============================================================

def evaluate_model(
    model_name,
    y_true,
    y_pred
):

    # Demand cannot be negative
    y_pred = np.maximum(
        y_pred,
        0
    )


    mae = mean_absolute_error(
        y_true,
        y_pred
    )


    rmse = np.sqrt(
        mean_squared_error(
            y_true,
            y_pred
        )
    )


    r2 = r2_score(
        y_true,
        y_pred
    )


    total_actual = np.sum(
        np.abs(y_true)
    )


    if total_actual == 0:

        wape = np.nan

    else:

        wape = (
            np.sum(
                np.abs(
                    y_true - y_pred
                )
            )
            /
            total_actual
        ) * 100


    return {
        "Model": model_name,
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2,
        "WAPE": wape
    }


# ============================================================
# 9. BASELINE MODEL
# ============================================================

print("\n" + "=" * 70)
print("TRAINING BASELINE MODEL")
print("=" * 70)


# Baseline:
# Predict next 7-day demand using
# 7 × recent 7-day average demand

baseline_predictions = (
    X_validation["rolling_mean_7"]
    * 7
)


baseline_results = evaluate_model(

    "7-Day Rolling Mean Baseline",

    y_validation,

    baseline_predictions

)


print("\nBaseline Results:")

print(
    f"MAE  : {baseline_results['MAE']:.4f}"
)

print(
    f"RMSE : {baseline_results['RMSE']:.4f}"
)

print(
    f"R²   : {baseline_results['R2']:.4f}"
)

print(
    f"WAPE : {baseline_results['WAPE']:.2f}%"
)


results = [
    baseline_results
]


# ============================================================
# 10. HIST GRADIENT BOOSTING MODEL
# ============================================================

print("\n" + "=" * 70)
print("TRAINING HIST GRADIENT BOOSTING")
print("=" * 70)


hist_model = HistGradientBoostingRegressor(

    learning_rate=0.08,

    max_iter=300,

    max_leaf_nodes=31,

    l2_regularization=1.0,

    random_state=RANDOM_STATE

)


hist_model.fit(
    X_train,
    y_train
)


hist_predictions = hist_model.predict(
    X_validation
)


hist_results = evaluate_model(

    "Hist Gradient Boosting",

    y_validation,

    hist_predictions

)


print(
    f"\nMAE  : {hist_results['MAE']:.4f}"
)

print(
    f"RMSE : {hist_results['RMSE']:.4f}"
)

print(
    f"R²   : {hist_results['R2']:.4f}"
)

print(
    f"WAPE : {hist_results['WAPE']:.2f}%"
)


results.append(
    hist_results
)


# ============================================================
# 11. GRADIENT BOOSTING MODEL
# ============================================================

print("\n" + "=" * 70)
print("TRAINING GRADIENT BOOSTING")
print("=" * 70)


if len(X_train) > MAX_GB_TRAIN_ROWS:

    print(
        f"\nSampling "
        f"{MAX_GB_TRAIN_ROWS:,} rows "
        f"from training data."
    )


    sample_index = np.random.RandomState(
        RANDOM_STATE
    ).choice(

        X_train.index,

        size=MAX_GB_TRAIN_ROWS,

        replace=False

    )


    X_train_gb = X_train.loc[
        sample_index
    ]


    y_train_gb = y_train.loc[
        sample_index
    ]


else:

    X_train_gb = X_train

    y_train_gb = y_train


gb_model = GradientBoostingRegressor(

    n_estimators=300,

    learning_rate=0.05,

    max_depth=5,

    subsample=0.8,

    random_state=RANDOM_STATE

)


gb_model.fit(
    X_train_gb,
    y_train_gb
)


gb_predictions = gb_model.predict(
    X_validation
)


gb_results = evaluate_model(

    "Gradient Boosting",

    y_validation,

    gb_predictions

)


print(
    f"\nMAE  : {gb_results['MAE']:.4f}"
)

print(
    f"RMSE : {gb_results['RMSE']:.4f}"
)

print(
    f"R²   : {gb_results['R2']:.4f}"
)

print(
    f"WAPE : {gb_results['WAPE']:.2f}%"
)


results.append(
    gb_results
)


# ============================================================
# 12. MODEL COMPARISON
# ============================================================

print("\n" + "=" * 70)
print("MODEL COMPARISON")
print("=" * 70)


results_df = pd.DataFrame(
    results
)


results_df = results_df.sort_values(
    by=["RMSE", "MAE"],
    ascending=[True, True]
).reset_index(
    drop=True
)


print("\n")

print(
    results_df.to_string(
        index=False
    )
)


comparison_path = os.path.join(
    RESULTS_DIR,
    "model_comparison_timeseries.csv"
)


results_df.to_csv(
    comparison_path,
    index=False
)


print(
    f"\n✓ Model comparison saved to:"
    f"\n{comparison_path}"
)


# ============================================================
# 13. SELECT BEST MODEL
# ============================================================

print("\n" + "=" * 70)
print("SELECTING BEST MODEL")
print("=" * 70)


best_model_name = results_df.iloc[
    0
]["Model"]


print(
    f"\n✓ Best model based on Validation RMSE:"
    f"\n{best_model_name}"
)


# ============================================================
# 14. RETRAIN BEST MODEL
# ============================================================

print("\n" + "=" * 70)
print("RETRAINING BEST MODEL")
print("=" * 70)


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


# ------------------------------------------------------------
# BASELINE MODEL
# ------------------------------------------------------------

if best_model_name == "7-Day Rolling Mean Baseline":

    # The baseline is a rule, not a fitted sklearn model.
    best_model = "baseline"

    print(
        "\n✓ Baseline selected as best model."
    )


# ------------------------------------------------------------
# HIST GRADIENT BOOSTING
# ------------------------------------------------------------

elif best_model_name == "Hist Gradient Boosting":

    best_model = HistGradientBoostingRegressor(

        learning_rate=0.08,

        max_iter=300,

        max_leaf_nodes=31,

        l2_regularization=1.0,

        random_state=RANDOM_STATE

    )


    best_model.fit(
        X_train_final,
        y_train_final
    )


# ------------------------------------------------------------
# GRADIENT BOOSTING
# ------------------------------------------------------------

elif best_model_name == "Gradient Boosting":

    if len(X_train_final) > MAX_GB_TRAIN_ROWS:

        sample_index = np.random.RandomState(
            RANDOM_STATE
        ).choice(

            X_train_final.index,

            size=MAX_GB_TRAIN_ROWS,

            replace=False

        )


        X_final_gb = X_train_final.loc[
            sample_index
        ]


        y_final_gb = y_train_final.loc[
            sample_index
        ]


    else:

        X_final_gb = X_train_final

        y_final_gb = y_train_final


    best_model = GradientBoostingRegressor(

        n_estimators=300,

        learning_rate=0.05,

        max_depth=5,

        subsample=0.8,

        random_state=RANDOM_STATE

    )


    best_model.fit(
        X_final_gb,
        y_final_gb
    )


else:

    raise ValueError(
        f"Unknown best model: {best_model_name}"
    )


print(
    "\n✓ Best model prepared using "
    "Train + Validation data."
)

# ============================================================
# 15. FINAL TEST EVALUATION
# ============================================================

print("\n" + "=" * 70)
print("FINAL TEST EVALUATION")
print("=" * 70)


# Generate test predictions

if best_model_name == "7-Day Rolling Mean Baseline":

    # Predict next 7-day demand using
    # 7 × recent 7-day average demand

    test_predictions = (
        X_test["rolling_mean_7"] * 7
    ).values


else:

    test_predictions = best_model.predict(
        X_test
    )


# Demand cannot be negative

test_predictions = np.maximum(
    test_predictions,
    0
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
    f"MAE  : {test_results['MAE']:.4f}"
)

print(
    f"RMSE : {test_results['RMSE']:.4f}"
)

print(
    f"R²   : {test_results['R2']:.4f}"
)

print(
    f"WAPE : {test_results['WAPE']:.2f}%"
)


# ============================================================
# 16. FEATURE IMPORTANCE
# ============================================================

print("\n" + "=" * 70)
print("FEATURE IMPORTANCE")
print("=" * 70)


if hasattr(
    best_model,
    "feature_importances_"
):

    importance_df = pd.DataFrame({

        "feature": feature_columns,

        "importance": (
            best_model
            .feature_importances_
        )

    })


    importance_df = importance_df.sort_values(

        "importance",

        ascending=False

    )


    print("\nTop 15 Most Important Features:\n")

    print(
        importance_df
        .head(15)
        .to_string(
            index=False
        )
    )


    importance_path = os.path.join(

        RESULTS_DIR,

        "feature_importance_timeseries.csv"

    )


    importance_df.to_csv(

        importance_path,

        index=False

    )


    print(
        f"\n✓ Feature importance saved to:"
        f"\n{importance_path}"
    )


else:

    print(
        "\nFeature importance is not directly "
        "available for this model."
    )


# ============================================================
# 17. SAVE MODEL ARTIFACTS
# ============================================================

print("\n" + "=" * 70)
print("SAVING MODEL ARTIFACTS")
print("=" * 70)


feature_path = os.path.join(
    MODELS_DIR,
    "model_features_timeseries.pkl"
)


with open(feature_path, "wb") as file:

    pickle.dump(
        feature_columns,
        file
    )


print(
    f"\n✓ Feature list saved:"
    f"\n{feature_path}"
)


# Save model only if an actual ML model won

if best_model_name != "7-Day Rolling Mean Baseline":

    model_path = os.path.join(
        MODELS_DIR,
        "best_demand_forecasting_model_timeseries.pkl"
    )


    with open(
        model_path,
        "wb"
    ) as file:

        pickle.dump(
            best_model,
            file
        )


    print(
        f"\n✓ Best model saved:"
        f"\n{model_path}"
    )


else:

    model_path = "Baseline forecasting rule"

    baseline_config_path = os.path.join(
        MODELS_DIR,
        "baseline_forecasting_rule.txt"
    )


    with open(
        baseline_config_path,
        "w"
    ) as file:

        file.write(
            "Forecast Rule:\n"
            "predicted_demand_7d = rolling_mean_7 * 7\n"
        )


    print(
        "\n✓ Baseline forecasting rule saved:"
        f"\n{baseline_config_path}"
    )

# ============================================================
# 18. SAVE TEST PREDICTIONS
# ============================================================

print("\n" + "=" * 70)
print("SAVING TEST PREDICTIONS")
print("=" * 70)


predictions_df = test_df[

    [

        "sales_date"

    ]

].copy()


predictions_df["actual_demand_7d"] = (
    y_test.values
)


predictions_df["predicted_demand_7d"] = (
    test_predictions
)


predictions_df["absolute_error"] = (

    predictions_df["actual_demand_7d"]

    -

    predictions_df["predicted_demand_7d"]

).abs()


prediction_path = os.path.join(

    RESULTS_DIR,

    "test_predictions_timeseries.csv"

)


predictions_df.to_csv(

    prediction_path,

    index=False

)


print(
    f"\n✓ Test predictions saved:"
    f"\n{prediction_path}"
)


# ============================================================
# 19. SAVE FINAL METRICS
# ============================================================

final_metrics = pd.DataFrame(
    [test_results]
)


metrics_path = os.path.join(

    RESULTS_DIR,

    "final_test_metrics_timeseries.csv"

)


final_metrics.to_csv(

    metrics_path,

    index=False

)


print(
    f"\n✓ Final test metrics saved:"
    f"\n{metrics_path}"
)


# ============================================================
# 20. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("STOCKSENSE AI DEMAND FORECASTING COMPLETE")
print("=" * 70)


print(
    f"\nBest Model: "
    f"{best_model_name}"
)

print(
    f"Test MAE  : "
    f"{test_results['MAE']:.4f}"
)

print(
    f"Test RMSE : "
    f"{test_results['RMSE']:.4f}"
)

print(
    f"Test R²   : "
    f"{test_results['R2']:.4f}"
)

print(
    f"Test WAPE : "
    f"{test_results['WAPE']:.2f}%"
)


print(
    "\nGenerated files:"
)

print(
    f"• {comparison_path}"
)

print(
    f"• {model_path}"
)

print(
    f"• {feature_path}"
)

print(
    f"• {prediction_path}"
)

print(
    f"• {metrics_path}"
)

print(
    "\nNext step:"
    "\n04_inventory_optimization.py"
)
