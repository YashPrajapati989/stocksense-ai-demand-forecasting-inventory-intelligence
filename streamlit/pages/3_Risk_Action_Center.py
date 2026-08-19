import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Risk & Action Center | StockSense AI",
    page_icon="🚨",
    layout="wide"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

.stApp {
    background-color: #111827;
    color: #E5E7EB;
}

.main {
    background-color: #111827;
}

.dashboard-title {
    text-align: center;
    font-size: 38px;
    font-weight: 800;
    color: #F1F5F9;
    margin-bottom: 0px;
}

.dashboard-subtitle {
    text-align: center;
    font-size: 16px;
    color: #94A3B8;
    margin-bottom: 30px;
}

.kpi-card {
    background-color: #1F2937;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 20px 10px;
    text-align: center;
    min-height: 110px;
}

.kpi-title {
    color: #CBD5E1;
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 10px;
}

.kpi-value {
    font-size: 26px;
    font-weight: 700;
}

.section-title {
    font-size: 21px;
    font-weight: 700;
    color: #F1F5F9;
    margin-top: 20px;
    margin-bottom: 10px;
}

footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    BASE_DIR = Path(__file__).resolve().parents[2]

    results_dir = BASE_DIR / "results"

    required_files = [
        "inventory_optimization_recommendations.csv",
        "top_stockout_priorities.csv",
        "top_excess_stock_opportunities.csv",
        "product_risk_analysis.csv",
        "store_risk_analysis.csv",
    ]

    missing_files = [
        name for name in required_files
        if not (results_dir / name).exists()
    ]

    if missing_files:
        st.error(
            "Missing result file(s): "
            + ", ".join(missing_files)
            + f"\\nExpected folder: {results_dir}"
        )
        st.stop()

    stockout_df = pd.read_csv(
        results_dir / "top_stockout_priorities.csv"
    )

    excess_df = pd.read_csv(
        results_dir / "top_excess_stock_opportunities.csv"
    )

    product_risk_df = pd.read_csv(
        results_dir / "product_risk_analysis.csv"
    )

    store_risk_df = pd.read_csv(
        results_dir / "store_risk_analysis.csv"
    )

    inventory_df = pd.read_csv(
        results_dir / "inventory_optimization_recommendations.csv"
    )

    return (
        stockout_df,
        excess_df,
        product_risk_df,
        store_risk_df,
        inventory_df
    )


(
    stockout_df,
    excess_df,
    product_risk_df,
    store_risk_df,
    inventory_df
) = load_data()


# ============================================================
# PAGE HEADER
# ============================================================

st.markdown("""
<div class="dashboard-title">
    RISK & ACTION CENTER
</div>

<div class="dashboard-subtitle">
    Prioritize Stockout Risks, Excess Inventory & Business Actions
</div>
""", unsafe_allow_html=True)


# ============================================================
# KPI CALCULATIONS
# ============================================================

inventory_df["inventory_risk"] = (
    inventory_df["inventory_risk"]
    .astype(str)
    .str.strip()
    .str.upper()
)

inventory_df["qty_on_hand"] = pd.to_numeric(
    inventory_df["qty_on_hand"],
    errors="coerce"
).fillna(0)

inventory_df["reorder_point"] = pd.to_numeric(
    inventory_df["reorder_point"],
    errors="coerce"
).fillna(0)

inventory_df["days_of_inventory"] = pd.to_numeric(
    inventory_df["days_of_inventory"],
    errors="coerce"
).fillna(0)

inventory_df["inventory_value_at_risk"] = pd.to_numeric(
    inventory_df["inventory_value_at_risk"],
    errors="coerce"
).fillna(0)

if "inventory_value" in inventory_df.columns:
    inventory_df["inventory_value"] = pd.to_numeric(
        inventory_df["inventory_value"],
        errors="coerce"
    ).fillna(0)
elif "cost_of_stocks" in inventory_df.columns:
    inventory_df["inventory_value"] = pd.to_numeric(
        inventory_df["cost_of_stocks"],
        errors="coerce"
    ).fillna(0)
else:
    inventory_df["inventory_value"] = 0

critical_mask = inventory_df["inventory_risk"].eq("CRITICAL")
high_risk_mask = inventory_df["inventory_risk"].eq("HIGH RISK")
stockout_risk_mask = inventory_df["inventory_risk"].isin(["CRITICAL", "HIGH RISK"])
excess_mask = inventory_df["inventory_risk"].eq("EXCESS STOCK")

critical_count = int(critical_mask.sum())
high_risk_count = int(high_risk_mask.sum())
reorder_risk_count = high_risk_count
excess_count = int(excess_mask.sum())
stockout_value_at_risk = float(
    inventory_df.loc[
        stockout_risk_mask,
        "inventory_value_at_risk"
    ].sum()
)

if "store" in store_risk_df.columns:
    store_field = "store"
elif "store_key" in store_risk_df.columns:
    store_field = "store_key"
elif "store" in inventory_df.columns:
    store_field = "store"
elif "store_key" in inventory_df.columns:
    store_field = "store_key"
else:
    store_field = None

if store_field is not None and not store_risk_df.empty:
    high_risk_store_count = int(
        store_risk_df[store_field].astype(str).nunique()
    )
elif store_field is not None:
    high_risk_store_count = int(
        inventory_df.loc[
            stockout_risk_mask,
            store_field
        ].astype(str).nunique()
    )
else:
    high_risk_store_count = 0

critical_stockouts = critical_count
excess_opportunities = excess_count
total_value_at_risk = stockout_value_at_risk
high_risk_stores = high_risk_store_count

# ============================================================
# KPI CARDS
# ============================================================

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpis = [
    (
        "Critical Stockout Priorities",
        f"{critical_stockouts:,}",
        "#FF4B55"
    ),
    (
        "Excess Stock Opportunities",
        f"{excess_opportunities:,}",
        "#A78BFA"
    ),
    (
        "Inventory Value at Risk",
        f"${total_value_at_risk/1000:,.0f}K",
        "#FACC15"
    ),
    (
        "High-Risk Stores",
        f"{high_risk_stores:,}",
        "#FB923C"
    )
]

for column, (title, value, color) in zip(
    [kpi1, kpi2, kpi3, kpi4],
    kpis
):
    with column:
        st.markdown(
f"""<div class="kpi-card">
<div class="kpi-title">{title}</div>
<div class="kpi-value" style="color: {color};">{value}</div>
</div>""",
            unsafe_allow_html=True
        )


# ============================================================
# TOP RISK VISUALIZATIONS
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)

left_col, right_col = st.columns(2)


# ============================================================
# STOCKOUT PRIORITIES
# ============================================================

with left_col:

    st.markdown(
        '<div class="section-title">🚨 Top Stockout Priorities</div>',
        unsafe_allow_html=True
    )

    top_stockouts = stockout_df.copy()

    if "inventory_risk" in top_stockouts.columns:
        top_stockouts = top_stockouts.loc[
            top_stockouts["inventory_risk"].isin(["CRITICAL", "HIGH RISK"])
        ].copy()

    if "priority_score" in top_stockouts.columns:
        top_stockouts["priority_score"] = pd.to_numeric(
            top_stockouts["priority_score"],
            errors="coerce"
        ).fillna(0)
        top_stockouts = top_stockouts.sort_values(
            "priority_score",
            ascending=False
        )

    top_stockouts = top_stockouts.head(10).copy()

    top_stockouts["product_label"] = (
        top_stockouts["product_description"]
        .astype(str)
        .str[:35]
    )

    fig_stockout = px.bar(
        top_stockouts,
        x="priority_score",
        y="product_label",
        orientation="h",
        color="priority_score",
        color_continuous_scale="Reds",
        text="priority_score"
    )

    fig_stockout.update_layout(
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font=dict(color="#E5E7EB"),
        height=420,
        margin=dict(l=10, r=20, t=20, b=30),
        coloraxis_showscale=False,
        xaxis_title="Priority Score",
        yaxis_title=""
    )

    fig_stockout.update_traces(
        texttemplate="%{text:.1f}",
        textposition="outside"
    )

    st.plotly_chart(
        fig_stockout,
        width="stretch",
        config={"displayModeBar": False}
    )


# ============================================================
# EXCESS STOCK OPPORTUNITIES
# ============================================================

with right_col:

    st.markdown(
        '<div class="section-title">📦 Top Excess Stock Opportunities</div>',
        unsafe_allow_html=True
    )

    excess_chart_df = excess_df.copy()

    if "inventory_risk" in excess_chart_df.columns:
        excess_chart_df = excess_chart_df.loc[
            excess_chart_df["inventory_risk"].eq("EXCESS STOCK")
        ].copy()

    value_field = None
    if "inventory_value" in excess_chart_df.columns:
        value_field = "inventory_value"
    elif "cost_of_stocks" in excess_chart_df.columns:
        value_field = "cost_of_stocks"

    if value_field is None:
        excess_chart_df["inventory_value"] = 0
    else:
        excess_chart_df["inventory_value"] = pd.to_numeric(
            excess_chart_df[value_field],
            errors="coerce"
        ).fillna(0)

    top_excess = (
        excess_chart_df
        .groupby(
            "product_description",
            as_index=False
        )
        .agg(
            excess_inventory_value=(
                "inventory_value",
                "sum"
            )
        )
        .sort_values(
            "excess_inventory_value",
            ascending=False
        )
        .head(10)
        .copy()
    )

    # Shorten product names for cleaner chart labels
    top_excess["product_label"] = (
        top_excess["product_description"]
        .astype(str)
        .str[:35]
    )

    # Create chart
    fig_excess = px.bar(
        top_excess,
        x="excess_inventory_value",
        y="product_label",
        orientation="h",
        color="excess_inventory_value",
        color_continuous_scale="Purples",
        text="excess_inventory_value"
    )

    fig_excess.update_layout(
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font=dict(color="#E5E7EB"),
        height=420,
        margin=dict(l=10, r=60, t=20, b=30),
        coloraxis_showscale=False,
        xaxis_title="Excess Inventory Value",
        yaxis_title="",
        yaxis=dict(
            categoryorder="total ascending"
        )
    )

    fig_excess.update_traces(
        texttemplate="$%{text:,.0f}",
        textposition="outside"
    )

    st.plotly_chart(
        fig_excess,
        width="stretch",
        config={"displayModeBar": False}
    )


# ============================================================
# STORE RISK ANALYSIS
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])


with col1:

    st.markdown(
        '<div class="section-title">🏪 Store Risk Analysis</div>',
        unsafe_allow_html=True
    )

    store_chart = (
        store_risk_df
        .sort_values(
            "inventory_value_at_risk",
            ascending=False
        )
        .head(10)
    )

    fig_store = px.bar(
        store_chart,
        x="store",
        y="inventory_value_at_risk",
        color="inventory_value_at_risk",
        color_continuous_scale="Oranges"
    )

    fig_store.update_layout(
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font=dict(color="#E5E7EB"),
        height=420,
        margin=dict(l=20, r=20, t=20, b=70),
        coloraxis_showscale=False,
        xaxis_title="Store",
        yaxis_title="Value at Risk"
    )

    st.plotly_chart(
        fig_store,
        width="stretch",
        config={"displayModeBar": False}
    )


# ============================================================
# PRODUCT RISK ANALYSIS
# ============================================================

with col2:

    st.markdown(
        '<div class="section-title">📊 Product Risk Breakdown</div>',
        unsafe_allow_html=True
    )

    product_chart = (
        product_risk_df
        .sort_values(
            "risk_items",
            ascending=False
        )
        .head(10)
        .copy()
    )

    product_chart["product_label"] = (
        product_chart["product_description"]
        .astype(str)
        .str[:30]
    )

    fig_product = px.bar(
        product_chart,
        x="product_label",
        y=[
            "critical_items",
            "high_risk_items",
            "excess_stock_items"
        ],
        barmode="stack",
        color_discrete_map={
            "critical_items": "#FF4B55",
            "high_risk_items": "#FB923C",
            "excess_stock_items": "#A78BFA"
        }
    )

    fig_product.update_layout(
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font=dict(color="#E5E7EB"),
        height=420,
        margin=dict(l=20, r=20, t=20, b=100),
        legend_title="Risk Type",
        xaxis_title="Product",
        yaxis_title="Risk Items"
    )

    st.plotly_chart(
        fig_product,
        width="stretch",
        config={"displayModeBar": False}
    )


# ============================================================
# EXECUTIVE RECOMMENDATIONS
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)

st.markdown(
    '<div class="section-title">🎯 Executive Recommendations</div>',
    unsafe_allow_html=True
)

reorder_risk_count = high_risk_count
excess_90d_count = excess_count

recommendations_display = pd.DataFrame([
    {
        "priority": "P1 - URGENT",
        "recommendation": "Immediately replenish critical inventory items.",
        "business_reason": (
            f"{critical_count:,} inventory records are currently "
            "at critical stock levels."
        )
    },
    {
        "priority": "P2 - HIGH",
        "recommendation": "Prioritize purchase orders for high-risk inventory.",
        "business_reason": (
            f"{reorder_risk_count:,} inventory records are below the "
            "recommended reorder threshold."
        )
    },
    {
        "priority": "P2 - HIGH",
        "recommendation": (
            "Review excess inventory for redistribution, promotions "
            "or purchasing reductions."
        ),
        "business_reason": (
            f"{excess_count:,} inventory records have more than "
            "90 days of estimated inventory coverage."
        )
    },
    {
        "priority": "P1 - URGENT",
        "recommendation": "Prioritize high-value inventory at risk.",
        "business_reason": (
            "Total inventory value exposed to stockout risk is "
            f"${stockout_value_at_risk:,.2f}."
        )
    }
])

st.dataframe(
    recommendations_display,
    width="stretch",
    hide_index=True,
    height=300
)


# ============================================================
# DETAILED ACTION TABLE
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)

st.markdown(
    '<div class="section-title">📋 Critical Inventory Action Queue</div>',
    unsafe_allow_html=True
)

# Columns to display
action_columns = [
    "store",
    "product_description",
    "inventory_risk",
    "recommended_action",
    "recommended_reorder_qty",
    "inventory_value_at_risk",
    "business_priority"
]

# Make sure required columns exist
available_columns = [
    col for col in action_columns
    if col in stockout_df.columns
]

# ------------------------------------------------------------
# SORT SAFELY using priority_score when available
# ------------------------------------------------------------

action_source = stockout_df.copy()

if "inventory_risk" in action_source.columns:
    action_source = action_source.loc[
        action_source["inventory_risk"].isin(["CRITICAL", "HIGH RISK"])
    ].copy()

if "priority_score" in action_source.columns:
    action_source["priority_score"] = pd.to_numeric(
        action_source["priority_score"],
        errors="coerce"
    ).fillna(0)
    action_source = action_source.sort_values(
        "priority_score",
        ascending=False
    )
elif "business_priority" in action_source.columns:
    action_source = action_source.copy()
    action_source["_business_priority_sort"] = (
        action_source["business_priority"]
        .astype(str)
        .str.extract(r"P\s*(\d+)", expand=False)
        .astype(float)
    )
    action_source = action_source.sort_values(
        "_business_priority_sort",
        ascending=True,
        na_position="last"
    ).drop(columns=["_business_priority_sort"])

action_table = (
    action_source[available_columns]
    .head(25)
    .copy()
)


# ------------------------------------------------------------
# DISPLAY TABLE
# ------------------------------------------------------------

st.dataframe(
    action_table,
    width="stretch",
    hide_index=True,
    height=500
)