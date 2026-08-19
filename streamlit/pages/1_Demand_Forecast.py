from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Demand Forecast Intelligence | StockSense AI",
    page_icon="📈",
    layout="wide"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

.stApp {
    background-color: #121A2A;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

/* Page title */

.dashboard-title {
    text-align: center;
    font-size: 38px;
    font-weight: 800;
    color: #F1F5F9;
    margin-bottom: 0px;
}

.dashboard-subtitle {
    text-align: center;
    color: #94A3B8;
    font-size: 15px;
    margin-bottom: 25px;
}

/* KPI Cards */

.kpi-card {
    background-color: #1F2937;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 22px 10px;
    text-align: center;
    min-height: 115px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.kpi-title {
    color: #CBD5E1;
    font-size: 15px;
    font-weight: 500;
    margin-bottom: 10px;
}

.kpi-value {
    font-size: 25px;
    font-weight: 700;
}

/* Chart containers */

.chart-title {
    text-align: center;
    font-size: 18px;
    font-weight: 700;
    color: #E5E7EB;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="dashboard-title">'
    'DEMAND FORECAST INTELLIGENCE'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="dashboard-subtitle">'
    '7-Day Demand Forecasting & Model Performance Analysis'
    '</div>',
    unsafe_allow_html=True
)

# ============================================================
# KPI CARDS
# ============================================================

@st.cache_data
def load_forecast_data():
    base_dir = Path(__file__).resolve().parents[2]
    results_dir = base_dir / "results"

    metrics_path = results_dir / "final_test_metrics_timeseries.csv"
    predictions_path = results_dir / "test_predictions_timeseries.csv"

    if not metrics_path.exists() or not predictions_path.exists():
        st.error("Missing forecast output files.")
        st.stop()

    metrics_df = pd.read_csv(metrics_path)
    predictions_df = pd.read_csv(predictions_path)
    predictions_df["sales_date"] = pd.to_datetime(predictions_df["sales_date"])

    metric_row = metrics_df.iloc[0].copy()
    model_name = str(metric_row.get("Model", "Gradient Boosting"))

    kpi_data = [
        ("Best Model", model_name, "#60A5FA"),
        ("Test MAE", f"{float(metric_row.get('MAE', 0)):.2f}", "#F87171"),
        ("Test RMSE", f"{float(metric_row.get('RMSE', 0)):.2f}", "#FB923C"),
        ("Test R²", f"{float(metric_row.get('R2', 0)):.2f}", "#C084FC"),
        ("Test WAPE", f"{float(metric_row.get('WAPE', 0)):.2f}%", "#4ADE80"),
    ]

    forecast_df = (
        predictions_df.groupby("sales_date", as_index=False)
        .agg(
            actual_demand_7d=("actual_demand_7d", "sum"),
            predicted_demand_7d=("predicted_demand_7d", "sum")
        )
        .sort_values("sales_date")
        .reset_index(drop=True)
    )

    error_df = (
        predictions_df.assign(
            forecast_error=pd.to_numeric(
                predictions_df["absolute_error"],
                errors="coerce"
            ).fillna(0)
        )
        .groupby("sales_date", as_index=False)
        .agg(forecast_error=("forecast_error", "sum"))
        .sort_values("forecast_error", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )

    return kpi_data, forecast_df, error_df


kpi_data, forecast_df, error_df = load_forecast_data()

cols = st.columns(5)

for col, (title, value, color) in zip(cols, kpi_data):
    with col:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">{title}</div>
                <div class="kpi-value" style="color: {color};">
                    {value}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# ============================================================
# ACTUAL VS PREDICTED
# ============================================================

st.markdown(
    '<div class="chart-title">'
    'Actual vs Predicted 7-Day Demand'
    '</div>',
    unsafe_allow_html=True
)

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=forecast_df["sales_date"],
        y=forecast_df["actual_demand_7d"],
        mode="lines",
        name="Actual Demand",
        line=dict(
            color="#60A5FA",
            width=3
        )
    )
)

fig.add_trace(
    go.Scatter(
        x=forecast_df["sales_date"],
        y=forecast_df["predicted_demand_7d"],
        mode="lines",
        name="Predicted Demand",
        line=dict(
            color="#C084FC",
            width=3,
            dash="dot"
        )
    )
)

fig.update_layout(

    height=400,

    paper_bgcolor="#121A2A",

    plot_bgcolor="#121A2A",

    font=dict(
        color="#CBD5E1"
    ),

    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0
    ),

    margin=dict(
        l=30,
        r=30,
        t=30,
        b=30
    ),

    xaxis=dict(
        title="Forecast Date",
        gridcolor="#1E293B"
    ),

    yaxis=dict(
        title="Actual Demand",
        gridcolor="#1E293B"
    )

)

st.plotly_chart(
    fig,
    width="stretch"
)


# ============================================================
# BOTTOM CHARTS
# ============================================================

col1, col2 = st.columns(2)


# ------------------------------------------------------------
# MODEL PERFORMANCE
# ------------------------------------------------------------

with col1:

    st.markdown(
        '<div class="chart-title">'
        'Model Performance Comparison (RMSE)'
        '</div>',
        unsafe_allow_html=True
    )

    metrics_df = pd.read_csv(Path(__file__).resolve().parents[2] / "results" / "final_test_metrics_timeseries.csv")
    models = [str(metrics_df.iloc[0]["Model"])]
    rmse = [float(metrics_df.iloc[0]["RMSE"])]

    fig_rmse = go.Figure()

    fig_rmse.add_trace(

        go.Bar(

            x=models,

            y=rmse,

            marker_color=["#22C55E"],

            text=rmse,

            textposition="outside"

        )

    )

    fig_rmse.update_layout(

        height=350,

        paper_bgcolor="#121A2A",

        plot_bgcolor="#121A2A",

        font=dict(
            color="#CBD5E1"
        ),

        margin=dict(
            l=30,
            r=30,
            t=30,
            b=50
        ),

        yaxis=dict(
            title="RMSE",
            gridcolor="#1E293B"
        ),

        xaxis=dict(
            title="Model"
        )

    )

    st.plotly_chart(
        fig_rmse,
        width="stretch"
    )


# ------------------------------------------------------------
# HIGHEST FORECAST ERROR
# ------------------------------------------------------------

with col2:

    st.markdown(
        '<div class="chart-title">'
        'Highest Forecast Error Dates'
        '</div>',
        unsafe_allow_html=True
    )

    error_dates = pd.to_datetime(error_df["sales_date"]).dt.strftime("%d %b")
    errors = error_df["forecast_error"].astype(float)

    fig_error = go.Figure()

    fig_error.add_trace(

        go.Bar(

            x=error_dates,

            y=errors,

            marker_color="#FF7A1A",

            text=errors,

            textposition="outside"

        )

    )

    fig_error.update_layout(

        height=350,

        paper_bgcolor="#121A2A",

        plot_bgcolor="#121A2A",

        font=dict(
            color="#CBD5E1"
        ),

        margin=dict(
            l=30,
            r=30,
            t=30,
            b=50
        ),

        yaxis=dict(
            title="Forecast Error",
            gridcolor="#1E293B"
        ),

        xaxis=dict(
            title="Date"
        )

    )

    st.plotly_chart(
        fig_error,
        width="stretch"
    )