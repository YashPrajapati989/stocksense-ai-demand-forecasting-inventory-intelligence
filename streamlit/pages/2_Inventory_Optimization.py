import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Inventory Optimization | StockSense AI",
    page_icon="📦",
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

/* Dashboard Header */

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


/* KPI Cards */

.kpi-card {
    background-color: #1F2937;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 20px 10px;
    text-align: center;
    min-height: 110px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.kpi-title {
    color: #CBD5E1;
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 10px;
}

.kpi-value {
    font-size: 25px;
    font-weight: 700;
}


/* Hide Streamlit Footer */

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

    file_path = (
        BASE_DIR
        / "results"
        / "inventory_optimization_recommendations.csv"
    )

    df = pd.read_csv(file_path)

    return df


df = load_data()


# ============================================================
# PAGE HEADER
# ============================================================

st.markdown(
    """
    <div class="dashboard-title">
        INVENTORY OPTIMIZATION INTELLIGENCE
    </div>

    <div class="dashboard-subtitle">
        Safety Stock, Reorder Strategy & Inventory Action Planning
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# KPI CALCULATIONS
# ============================================================

total_inventory_records = len(df)

inventory_value_at_risk = df["inventory_value_at_risk"].sum()

critical_items = (
    df["inventory_risk"]
    .astype(str)
    .str.upper()
    .eq("CRITICAL")
    .sum()
)

recommended_reorder_qty = df["recommended_reorder_qty"].sum()

stockout_risk_pct = (
    critical_items / total_inventory_records * 100
    if total_inventory_records > 0
    else 0
)

excess_stock_items = (
    df["inventory_risk"]
    .astype(str)
    .str.upper()
    .eq("EXCESS STOCK")
    .sum()
)

excess_stock_pct = (
    excess_stock_items / total_inventory_records * 100
    if total_inventory_records > 0
    else 0
)


# ============================================================
# KPI CARDS
# ============================================================

kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

kpis = [
    (
        "Total Inventory Records",
        f"{total_inventory_records:,}",
        "#60A5FA"
    ),
    (
        "Inventory Value at Risk",
        f"${inventory_value_at_risk / 1000:,.0f}K",
        "#FAC515"
    ),
    (
        "Critical Items",
        f"{critical_items:,}",
        "#FF4B55"
    ),
    (
        "Recommended Reorder Qty",
        f"{recommended_reorder_qty:,.0f}",
        "#FB923C"
    ),
    (
        "Stockout Risk %",
        f"{stockout_risk_pct:.1f}%",
        "#F87171"
    ),
    (
        "Excess Stock %",
        f"{excess_stock_pct:.1f}%",
        "#A78BFA"
    )
]

for column, (title, value, color) in zip(
    [kpi1, kpi2, kpi3, kpi4, kpi5, kpi6],
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
# INVENTORY RISK DISTRIBUTION
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)

risk_counts = (
    df["inventory_risk"]
    .astype(str)
    .str.upper()
    .value_counts()
    .reset_index()
)

risk_counts.columns = [
    "Inventory Risk",
    "Count"
]


risk_colors = {
    "HEALTHY": "#2FB36D",
    "CRITICAL": "#FF4B55",
    "EXCESS STOCK": "#9B6BDB",
    "HIGH RISK": "#FF8C24",
    "MONITOR": "#4DA3FF"
}


fig_risk = px.pie(
    risk_counts,
    names="Inventory Risk",
    values="Count",
    hole=0.58,
    color="Inventory Risk",
    color_discrete_map=risk_colors
)

fig_risk.update_traces(
    textinfo="percent+label"
)

fig_risk.update_layout(
    title="Inventory Risk Distribution",
    paper_bgcolor="#111827",
    plot_bgcolor="#111827",
    font=dict(color="#E5E7EB"),
    height=380,
    margin=dict(l=20, r=20, t=60, b=20),
    legend=dict(
        orientation="h",
        y=-0.1
    )
)


# ============================================================
# STORES REQUIRING INVENTORY ATTENTION
# ============================================================

attention_df = df[
    df["inventory_risk"]
    .astype(str)
    .str.upper()
    .isin(["CRITICAL", "HIGH RISK"])
].copy()


store_attention = (
    attention_df
    .groupby("store_key")
    .size()
    .reset_index(name="Items Requiring Attention")
    .sort_values(
        "Items Requiring Attention",
        ascending=False
    )
    .head(10)
)


fig_stores = px.bar(
    store_attention,
    x="Items Requiring Attention",
    y="store_key",
    orientation="h",
    text="Items Requiring Attention"
)

fig_stores.update_traces(
    marker_color="#3B82F6",
    textposition="outside"
)

fig_stores.update_layout(
    title="Stores Requiring Inventory Attention",
    paper_bgcolor="#111827",
    plot_bgcolor="#111827",
    font=dict(color="#E5E7EB"),
    height=380,
    margin=dict(l=20, r=40, t=60, b=30),
    yaxis=dict(
        categoryorder="total ascending",
        title="Store"
    ),
    xaxis=dict(
        title="Items Requiring Attention"
    )
)


# ============================================================
# DISPLAY ROW 1
# ============================================================

col1, col2 = st.columns([1, 2])

with col1:

    st.plotly_chart(
        fig_risk,
        width="stretch",
        config={"displayModeBar": False}
    )

with col2:

    st.plotly_chart(
        fig_stores,
        width="stretch",
        config={"displayModeBar": False}
    )