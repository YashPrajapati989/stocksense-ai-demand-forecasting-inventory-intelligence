import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="StockSense AI",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

    /* Main application */
    .stApp {
        background-color: #121A2A;
        color: #E5E7EB;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1C2638;
    }

    /* Main heading */
    .main-title {
        font-size: 42px;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 0px;
    }

    /* Subtitle */
    .subtitle {
        font-size: 18px;
        color: #A0AEC0;
        margin-bottom: 30px;
    }

    /* KPI card */
    .kpi-card {
        background-color: #1C2638;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #3A465C;
    }

    .kpi-title {
        font-size: 14px;
        color: #A0AEC0;
    }

    .kpi-value {
        font-size: 28px;
        font-weight: bold;
        color: #FFFFFF;
    }

</style>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("# 📦 StockSense AI")

    st.caption(
        "Demand Forecasting & Inventory "
        "Decision Intelligence"
    )

    st.divider()

    st.success("System Status: Online")

    st.divider()

    st.markdown(
        """
        **Capabilities**

        📈 Demand Forecasting

        📦 Inventory Optimization

        ⚠️ Risk Intelligence

        💡 Insights & Recommendations
        """
    )


# ============================================================
# MAIN PAGE
# ============================================================

st.markdown(
    '<div class="main-title">StockSense AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Demand Forecasting & Inventory Decision Intelligence Platform'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# WELCOME SECTION
# ============================================================

col1, col2 = st.columns([2, 1])

with col1:

    st.markdown("## Welcome to StockSense AI")

    st.write(
        """
        An intelligent decision-support platform designed to help
        businesses forecast demand, optimize inventory, identify
        stockout risks, and generate actionable recommendations.
        """
    )

    st.info(
        "Use the navigation menu to explore forecasting, "
        "inventory optimization, risk intelligence, and "
        "insights & recommendations."
    )


with col2:

    st.markdown(
        """
        <div class="kpi-card">

        <div class="kpi-title">
        AI Decision Intelligence
        </div>

        <div class="kpi-value">
        READY
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )


st.divider()


# ============================================================
# PLATFORM MODULES
# ============================================================

st.markdown("## Explore the Platform")

col1, col2, col3, col4 = st.columns(4)

modules = [
    (
        "📈",
        "Demand Forecast",
        "Analyse historical demand and generate forecasts."
    ),
    (
        "📦",
        "Inventory Optimization",
        "Identify reorder requirements and inventory gaps."
    ),
    (
        "⚠️",
        "Risk Intelligence",
        "Discover critical stores, products, and stockout risks."
    ),
    (
        "💡",
        "Insights & Recommendations",
        "Turn inventory optimization results into actionable decisions."
    )
]


for column, (icon, title, description) in zip(
    [col1, col2, col3, col4],
    modules
):

    with column:

        st.markdown(
            f"""
            <div class="kpi-card">

            <h2>{icon}</h2>

            <h4>{title}</h4>

            <p style="color:#A0AEC0;">
            {description}
            </p>

            </div>
            """,
            unsafe_allow_html=True
        )