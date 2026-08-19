"""
StockSenseAI - Business Insights & Recommendations
Final decision-support page converting inventory optimization outputs into actionable decisions.
"""

from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Insights & Recommendations | StockSense AI",
    page_icon="💡",
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
    margin-bottom: 10px;
}

.disclaimer {
    text-align: center;
    font-size: 13px;
    color: #64748B;
    margin-bottom: 25px;
    font-style: italic;
}

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
    font-size: 13px;
    font-weight: 500;
    margin-bottom: 8px;
}

.kpi-value {
    font-size: 22px;
    font-weight: 700;
}

.section-title {
    font-size: 20px;
    font-weight: 700;
    color: #F1F5F9;
    margin-top: 25px;
    margin-bottom: 15px;
}

.summary-box {
    background-color: #1E293B;
    border-left: 4px solid #3B82F6;
    border-radius: 8px;
    padding: 18px 20px;
    margin-top: 15px;
    color: #E5E7EB;
    font-size: 14px;
    line-height: 1.6;
}

footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# BUSINESS CONSTANTS (from 04_inventory_optimization.py)
# ============================================================

LEAD_TIME_DAYS = 7
SERVICE_LEVEL_Z = 1.65
FORECAST_HORIZON = 7


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_inventory_data():
    """Load inventory optimization output CSV."""
    BASE_DIR = Path(__file__).resolve().parents[2]
    results_dir = BASE_DIR / "results"
    
    file_path = results_dir / "inventory_optimization_recommendations.csv"
    
    if not file_path.exists():
        st.error(f"Missing file: {file_path}")
        st.stop()
    
    df = pd.read_csv(file_path)
    
    # Ensure numeric columns are properly typed.
    # IMPORTANT: days_of_inventory must NOT receive fillna(0).
    # NaN DOI represents zero forecast / undefined coverage.
    numeric_cols_fill_zero = [
        'qty_on_hand', 'forecast_demand_7d', 'forecast_daily_demand',
        'rolling_std_30', 'rolling_mean_30', 'demand_cv_30',
        'safety_stock', 'lead_time_demand', 'reorder_point',
        'inventory_gap', 'recommended_reorder_qty',
        'inventory_value', 'inventory_value_at_risk', 'cost_of_stocks'
    ]
    
    for col in numeric_cols_fill_zero:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    if 'days_of_inventory' in df.columns:
        df['days_of_inventory'] = pd.to_numeric(df['days_of_inventory'], errors='coerce')
    
    return df


df_raw = load_inventory_data()


# ============================================================
# SECTION A — PAGE HEADER
# ============================================================

st.markdown(
    '<div class="dashboard-title">'
    '📊 INVENTORY INSIGHTS & RECOMMENDATIONS'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="dashboard-subtitle">'
    'Turn inventory optimization results into actionable business decisions'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="disclaimer">'
    '💡 Decision-support intelligence derived directly from production inventory optimization pipeline'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# FILTERS CONTROL SECTION
# ============================================================

st.markdown(
    '<div class="section-title">🔍 Decision Filters</div>',
    unsafe_allow_html=True
)

filter_cols = st.columns([2, 2, 2, 2])

with filter_cols[0]:
    available_stores = ['All Stores'] + sorted(df_raw['store_key'].dropna().unique().astype(int).astype(str).tolist())
    selected_store = st.selectbox(
        "Store Filter",
        available_stores,
        key="insights_store_filter"
    )

with filter_cols[1]:
    if selected_store == 'All Stores':
        available_products = ['All Products'] + sorted(df_raw['product_key'].dropna().unique().astype(int).astype(str).tolist()[:100])
    else:
        store_products = df_raw[df_raw['store_key'].astype(str) == selected_store]['product_key'].dropna().unique()
        available_products = ['All Products'] + sorted(store_products.astype(int).astype(str).tolist())
    
    selected_product = st.selectbox(
        "Product Filter",
        available_products,
        key="insights_product_filter"
    )

with filter_cols[2]:
    risk_options = ['All Risks', 'CRITICAL', 'HIGH RISK', 'MONITOR', 'HEALTHY', 'EXCESS STOCK']
    selected_risk = st.selectbox(
        "Risk Category",
        risk_options,
        key="insights_risk_filter"
    )

with filter_cols[3]:
    max_inv_val = float(df_raw['inventory_value'].max()) if not df_raw.empty else 1000.0
    min_inv_val = st.number_input(
        "Min Inventory Value ($)",
        min_value=0.0,
        max_value=max_inv_val,
        value=0.0,
        step=50.0,
        key="insights_min_val_filter"
    )

# Filter dataset
df = df_raw.copy()

if selected_store != 'All Stores':
    df = df[df['store_key'].astype(str) == selected_store]

if selected_product != 'All Products':
    df = df[df['product_key'].astype(str) == selected_product]

if selected_risk != 'All Risks':
    df = df[df['inventory_risk'] == selected_risk]

if min_inv_val > 0:
    df = df[df['inventory_value'] >= min_inv_val]

if df.empty:
    st.warning("No inventory records match the selected decision filters. Please adjust your selection.")
    st.stop()


# ============================================================
# SECTION B — EXECUTIVE KPI SUMMARY
# ============================================================

st.markdown(
    '<div class="section-title">📈 Executive KPI Summary</div>',
    unsafe_allow_html=True
)

kpi_cols = st.columns(6)

total_inv_value = df['inventory_value'].sum()
value_at_risk = df['inventory_value_at_risk'].sum()
crit_count = (df['inventory_risk'] == 'CRITICAL').sum()
high_risk_count = (df['inventory_risk'] == 'HIGH RISK').sum()
excess_count = (df['inventory_risk'] == 'EXCESS STOCK').sum()
reorder_qty_total = df['recommended_reorder_qty'].sum()

kpi_metrics = [
    ("Total Inventory Value", f"${total_inv_value:,.2f}", "#60A5FA"),
    ("Value at Risk", f"${value_at_risk:,.2f}", "#FF4B55"),
    ("Critical Items", f"{crit_count:,}", "#EF4444"),
    ("High Risk Items", f"{high_risk_count:,}", "#F97316"),
    ("Excess Stock Items", f"{excess_count:,}", "#A855F7"),
    ("Reorder Qty Total", f"{reorder_qty_total:,.0f} units", "#10B981"),
]

for col, (label, val, color) in zip(kpi_cols, kpi_metrics):
    with col:
        st.markdown(
            f"""<div class="kpi-card">
            <div class="kpi-title">{label}</div>
            <div class="kpi-value" style="color: {color};">{val}</div>
            </div>""",
            unsafe_allow_html=True
        )


# ============================================================
# SECTION C — INVENTORY RISK OVERVIEW & MANAGEMENT SUMMARY
# ============================================================

st.markdown(
    '<div class="section-title">📊 Portfolio Risk Intelligence & Management Summary</div>',
    unsafe_allow_html=True
)

col_chart, col_summary = st.columns([3, 3])

with col_chart:
    st.markdown("#### Inventory Risk Distribution")
    risk_order = ['CRITICAL', 'HIGH RISK', 'MONITOR', 'EXCESS STOCK', 'HEALTHY']
    risk_counts = df['inventory_risk'].value_counts().reindex(risk_order).fillna(0)
    
    colors = {
        'CRITICAL': '#EF4444',
        'HIGH RISK': '#F97316',
        'MONITOR': '#FBBF24',
        'EXCESS STOCK': '#A855F7',
        'HEALTHY': '#10B981'
    }
    
    fig_donut = go.Figure(data=[go.Pie(
        labels=risk_counts.index,
        values=risk_counts.values,
        hole=.5,
        marker=dict(colors=[colors[k] for k in risk_counts.index]),
        textinfo='label+percent',
        hoverinfo='label+value+percent'
    )])
    
    fig_donut.update_layout(
        paper_bgcolor='#111827',
        plot_bgcolor='#111827',
        font=dict(color='#E5E7EB'),
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False
    )
    
    st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})

with col_summary:
    st.markdown("#### Executive Management Summary")
    
    # Identify store with highest VAR
    store_var = df.groupby('store_key')['inventory_value_at_risk'].sum()
    top_store_key = store_var.idxmax() if not store_var.empty else "N/A"
    top_store_val = store_var.max() if not store_var.empty else 0.0
    
    summary_html = f"""
    <div class="summary-box">
        <ul style="margin: 0; padding-left: 18px; list-style-type: disc; line-height: 1.7;">
            <li style="margin-bottom: 10px;">
                <strong style="color: #EF4444;">Critical Replenishment:</strong> 
                <strong>{crit_count:,}</strong> inventory items are depleted or out of stock (<code style="background-color: #374151; color: #EF4444; padding: 2px 6px; border-radius: 4px;">CRITICAL</code>).
            </li>
            <li style="margin-bottom: 10px;">
                <strong style="color: #F97316;">High Stockout Risk:</strong> 
                <strong>{high_risk_count:,}</strong> items are currently at or below reorder points (<code style="background-color: #374151; color: #F97316; padding: 2px 6px; border-radius: 4px;">HIGH RISK</code>).
            </li>
            <li style="margin-bottom: 10px;">
                <strong style="color: #60A5FA;">Capital Exposure:</strong> 
                <strong>${value_at_risk:,.2f}</strong> of inventory value is exposed to stockout risk.
            </li>
            <li style="margin-bottom: 10px;">
                <strong style="color: #A855F7;">Excess Capital:</strong> 
                <strong>{excess_count:,}</strong> items carry excess stock (&gt;90 days of inventory).
            </li>
            <li style="margin-bottom: 0px;">
                <strong style="color: #FBBF24;">Top Risk Concentration:</strong> 
                Store <strong>{top_store_key}</strong> holds the largest concentration of value at risk (<strong>${top_store_val:,.2f}</strong>).
            </li>
        </ul>
    </div>
    """
    
    st.markdown(summary_html, unsafe_allow_html=True)


# ============================================================
# SECTION D, E & F — PRIORITY ACTIONS & RECOMMENDATION ENGINE
# ============================================================

st.markdown(
    '<div class="section-title">🚨 Priority Action Register</div>',
    unsafe_allow_html=True
)

# Prioritize non-healthy records
priority_order = {'CRITICAL': 1, 'HIGH RISK': 2, 'MONITOR': 3, 'EXCESS STOCK': 4, 'HEALTHY': 5}
df_priority = df.copy()
df_priority['sort_rank'] = df_priority['inventory_risk'].map(priority_order).fillna(5)
df_priority = df_priority.sort_values(by=['sort_rank', 'inventory_value_at_risk'], ascending=[True, False])

# Rule-based explanations and recommendations
def get_explanation_and_rec(row):
    risk = row['inventory_risk']
    qty = row['qty_on_hand']
    rop = row['reorder_point']
    doi = row['days_of_inventory']
    
    doi_str = f"{doi:.1f} days" if pd.notna(doi) else "N/A"
    
    if risk == 'CRITICAL':
        rec = "Immediate Replenishment Required"
        exp = f"Depleted stock ({qty:.0f} units on hand vs {rop:.1f}-unit reorder point)"
    elif risk == 'HIGH RISK':
        rec = "Reorder Stock & Prioritize Supplier Order"
        exp = f"At/below reorder point ({qty:.0f} units on hand vs {rop:.1f}-unit reorder point)"
    elif risk == 'MONITOR':
        rec = "Monitor Demand & Inventory Closely"
        exp = f"Low inventory coverage ({doi_str})"
    elif risk == 'EXCESS STOCK':
        rec = "Review & Redistribute Excess Inventory"
        exp = f"Excess stock coverage ({doi_str} vs 90-day threshold)"
    else:
        rec = "No Action Required"
        exp = f"Stock level optimal ({doi_str})"
    
    return pd.Series([rec, exp])

df_priority[['business_recommendation', 'action_explanation']] = df_priority.apply(get_explanation_and_rec, axis=1)

# Format table for display
display_df = pd.DataFrame()
display_df['Store'] = df_priority['store_key'].astype(str)
display_df['Product'] = df_priority['product_key'].astype(str)
display_df['Risk'] = df_priority['inventory_risk']
display_df['Qty on Hand'] = df_priority['qty_on_hand'].map('{:,.0f}'.format)
display_df['Reorder Point'] = df_priority['reorder_point'].map('{:,.2f}'.format)
display_df['Reorder Qty'] = df_priority['recommended_reorder_qty'].map('{:,.0f}'.format)
display_df['Days of Inventory'] = df_priority['days_of_inventory'].apply(lambda v: f"{v:.1f}" if pd.notna(v) else "N/A")
display_df['Inventory Value'] = df_priority['inventory_value'].map('${:,.2f}'.format)
display_df['Value at Risk'] = df_priority['inventory_value_at_risk'].map('${:,.2f}'.format)
display_df['Recommendation'] = df_priority['business_recommendation']
display_df['Why Item Needs Attention'] = df_priority['action_explanation']

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    height=400
)


# ============================================================
# SECTION G & H — STORE & PRODUCT ATTENTION REGISTERS
# ============================================================

st.markdown(
    '<div class="section-title">🏬 Store & Product Decision Intelligence</div>',
    unsafe_allow_html=True
)

col_store, col_prod = st.columns(2)

with col_store:
    st.markdown("#### Top Stores Requiring Attention")
    store_agg = df.groupby('store_key').agg(
        total_inv_value=('inventory_value', 'sum'),
        val_at_risk=('inventory_value_at_risk', 'sum'),
        critical_items=('inventory_risk', lambda x: (x == 'CRITICAL').sum()),
        high_risk_items=('inventory_risk', lambda x: (x == 'HIGH RISK').sum()),
        excess_items=('inventory_risk', lambda x: (x == 'EXCESS STOCK').sum()),
        total_reorder_qty=('recommended_reorder_qty', 'sum')
    ).reset_index().sort_values('val_at_risk', ascending=False)
    
    store_agg_display = pd.DataFrame()
    store_agg_display['Store'] = store_agg['store_key'].astype(str)
    store_agg_display['Total Value'] = store_agg['total_inv_value'].map('${:,.2f}'.format)
    store_agg_display['Value at Risk'] = store_agg['val_at_risk'].map('${:,.2f}'.format)
    store_agg_display['Critical'] = store_agg['critical_items']
    store_agg_display['High Risk'] = store_agg['high_risk_items']
    store_agg_display['Excess Stock'] = store_agg['excess_items']
    store_agg_display['Reorder Qty'] = store_agg['total_reorder_qty'].map('{:,.0f}'.format)
    
    st.dataframe(store_agg_display, use_container_width=True, hide_index=True, height=300)

with col_prod:
    st.markdown("#### Top Products Requiring Attention")
    prod_agg = df.groupby('product_key').agg(
        total_inv_value=('inventory_value', 'sum'),
        val_at_risk=('inventory_value_at_risk', 'sum'),
        critical_items=('inventory_risk', lambda x: (x == 'CRITICAL').sum()),
        high_risk_items=('inventory_risk', lambda x: (x == 'HIGH RISK').sum()),
        total_reorder_qty=('recommended_reorder_qty', 'sum')
    ).reset_index().sort_values('val_at_risk', ascending=False).head(50)
    
    prod_agg_display = pd.DataFrame()
    prod_agg_display['Product'] = prod_agg['product_key'].astype(str)
    prod_agg_display['Total Value'] = prod_agg['total_inv_value'].map('${:,.2f}'.format)
    prod_agg_display['Value at Risk'] = prod_agg['val_at_risk'].map('${:,.2f}'.format)
    prod_agg_display['Critical Count'] = prod_agg['critical_items']
    prod_agg_display['High Risk Count'] = prod_agg['high_risk_items']
    prod_agg_display['Reorder Qty'] = prod_agg['total_reorder_qty'].map('{:,.0f}'.format)
    
    st.dataframe(prod_agg_display, use_container_width=True, hide_index=True, height=300)


# ============================================================
# SECTION I — DEMAND & INVENTORY INSIGHTS
# ============================================================

st.markdown(
    '<div class="section-title">💡 Operational Insights</div>',
    unsafe_allow_html=True
)

col_ins1, col_ins2, col_ins3 = st.columns(3)

with col_ins1:
    st.markdown("##### High-Demand Products (7D)")
    top_demand = df.sort_values('forecast_demand_7d', ascending=False).head(5)
    for _, r in top_demand.iterrows():
        st.markdown(f"• **Store {int(r['store_key'])} - Product {int(r['product_key'])}:** {r['forecast_demand_7d']:.2f} units forecast")

with col_ins2:
    st.markdown("##### Demand Volatility Insights")
    top_cv = df[df['demand_cv_30'] > 0].sort_values('demand_cv_30', ascending=False).head(5)
    if not top_cv.empty:
        for _, r in top_cv.iterrows():
            st.markdown(f"• **Product {int(r['product_key'])}:** CV = {r['demand_cv_30']:.2f} (High variability)")
    else:
        st.markdown("• Demand variability is stable across selected inventory.")

with col_ins3:
    st.markdown("##### Excess Capital Exposure")
    top_excess = df[df['inventory_risk'] == 'EXCESS STOCK'].sort_values('inventory_value', ascending=False).head(5)
    if not top_excess.empty:
        for _, r in top_excess.iterrows():
            doi_val = f"{r['days_of_inventory']:.1f}d" if pd.notna(r['days_of_inventory']) else "N/A"
            st.markdown(f"• **Store {int(r['store_key'])} - Prod {int(r['product_key'])}:** ${r['inventory_value']:,.2f} tied up ({doi_val})")
    else:
        st.markdown("• No excess stock exposure identified in selection.")


# ============================================================
# FOOTER
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)

st.markdown(
    """
    <div style="text-align: center; font-size: 12px; color: #64748B; padding-top: 20px; border-top: 1px solid #334155;">
    🔒 <b>StockSense AI:</b> Production Inventory Intelligence & Decision Support Platform.
    </div>
    """,
    unsafe_allow_html=True
)
