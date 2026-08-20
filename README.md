# StockSenseAI — Inventory Decision Support Platform

An end-to-end AI-driven decision-support platform designed to help retail and supply chain teams forecast demand, optimize safety stock and reorder points, classify inventory risks, and generate actionable business recommendations.

---

## Overview

StockSenseAI bridges the gap between machine learning demand forecasts and executive supply chain decision-making. By converting 7-day probabilistic demand predictions into item-level inventory buffers, safety stock thresholds, and risk-weighted reorder recommendations, StockSenseAI ensures supply chain managers maintain high customer service levels while minimizing excess capital exposure.

---

## Business Problem

Retail operations face two primary inventory management risks:
1. **Stockout Risks:** Under-stocking leads to lost revenue, unfulfilled customer demand, and damaged brand trust.
2. **Excess Capital Exposure:** Over-stocking ties up cash flow in working capital, increases holding/depreciation costs, and limits operational agility.
3. **Prioritization Paralysis:** Planning across thousands of SKUs across multiple retail locations makes manual monitoring and order prioritization inefficient.

---

## Solution

StockSenseAI implements an enterprise decision pipeline that transforms raw time-series sales records into prioritized business recommendations. The system evaluates current inventory levels against dynamic reorder thresholds, identifies critical stockout risks, quantifies financial value at risk, and prescribes exact reorder quantities for store and supply chain managers.

---

## Business Flow

```
Data
  ↓
Demand Forecasting
  ↓
Inventory Optimization
  ↓
Inventory Risk Identification
  ↓
Business Insights & Recommendations
```

---

## Key Features

### 📈 1. Demand Forecasting
- Generates 7-day horizon demand forecasts at the native **Store × Product** grain.
- Evaluates historical daily sales averages, rolling 30-day demand, and demand volatility ($CV_{30}$).
- Establishes daily baseline estimates ($d_{daily} = \text{Forecast}_{7D} / 7$).

### 📦 2. Inventory Optimization
- Calculates mathematically rigorous inventory buffers:
  - **Lead-Time Demand ($LTD$):** Expected demand during supplier lead time ($7 \text{ days}$).
  - **Safety Stock ($SS$):** Service-level buffered safety stock ($Z = 1.65$ for 95% service level, $\sigma_{30} \cdot \sqrt{L}$).
  - **Reorder Point ($ROP$):** Dynamic replenishment trigger ($ROP = LTD + SS$).
  - **Days of Inventory ($DOI$):** Inventory coverage horizon ($\text{Qty} / d_{daily}$).

### ⚠️ 3. Risk & Action Center
- Classifies each SKU into five authoritative risk categories:
  - `CRITICAL`: Out of stock ($\text{Qty} \le 0$).
  - `HIGH RISK`: At or below reorder point ($\text{Qty} \le ROP$) or low coverage ($DOI < 7 \text{ days}$).
  - `MONITOR`: Low inventory buffer ($7 \le DOI < 21 \text{ days}$).
  - `HEALTHY`: Optimal stock coverage.
  - `EXCESS STOCK`: Over-stocked coverage ($DOI > 90 \text{ days}$).

### 💡 4. Insights & Recommendations
- Converts production optimization metrics into executive decision intelligence:
  - **Executive KPI Summary:** Portfolio inventory value, value at risk, critical/high-risk item counts, total reorder quantity.
  - **Portfolio Risk Distribution:** Interactive Plotly donut visualization of inventory health.
  - **Priority Action Register:** Filterable, ranked register prioritised by risk rank and value at risk.
  - **Store & Product Attention Registers:** Aggregated financial and stockout risk metrics by retail location and SKU.
  - **Executive Management Summary:** Automated narrative bullet summary calculated directly from loaded data.

---

## Risk Classification Rules

The platform strictly enforces the five production risk tiers established in `analysis/04_inventory_optimization.py`:

| Risk Tier | Condition | Business Implication | Recommended Action |
|---|---|---|---|
| **`CRITICAL`** | $\text{Qty on Hand} \le 0$ | Depleted stock; active stockout | Immediate replenishment required |
| **`HIGH RISK`** | $\text{Qty} \le ROP$ or $DOI < 7$ | At or below dynamic reorder point | Reorder stock & prioritize supplier shipment |
| **`MONITOR`** | $7 \le DOI < 21$ | Buffer low; approaching reorder threshold | Monitor demand & inventory position closely |
| **`EXCESS STOCK`** | $DOI > 90$ | Substantial over-stocking | Review purchasing & consider stock redistribution |
| **`HEALTHY`** | Otherwise | Optimal stock coverage | No immediate action required |

---

## Key Metrics

- **Forecast Demand (7D):** Predicted total sales volume over the upcoming 7 days.
- **Forecast Daily Demand:** Average expected daily sales ($d_{daily} = \text{Forecast}_{7D} / 7$).
- **Lead-Time Demand ($LTD$):** Expected sales during supplier delivery window ($7 \text{ days}$).
- **Safety Stock ($SS$):** Buffer stock protecting against demand volatility ($Z \cdot \sigma_{30} \cdot \sqrt{7}$).
- **Reorder Point ($ROP$):** Dynamic replenishment trigger ($LTD + SS$).
- **Days of Inventory ($DOI$):** Inventory coverage in days ($\text{Qty} / d_{daily}$ when $d_{daily} > 0$, else `N/A`).
- **Inventory Gap:** Buffer deficit or surplus ($\text{Qty} - ROP$).
- **Recommended Reorder Qty:** Exact units required to reach reorder point ($\lceil ROP - \text{Qty} \rceil$ for `CRITICAL` / `HIGH RISK`, else $0$).
- **Inventory Value at Risk:** Financial exposure of items in `CRITICAL` or `HIGH RISK` state.

---

## Dataset & Grain

- **Total Records:** 60,968 inventory records.
- **Native Planning Grain:** **Store × Product** (`store_key` × `product_key`).
- **Data Integrity:** 0 duplicate Store × Product combinations. Production data is loaded read-only from `results/inventory_optimization_recommendations.csv`.

---

## Project Architecture

```
StockSenseAI/
├── analysis/
│   ├── 01_business_exploration.py
│   ├── 02_feature_engineering.py
│   ├── 02b_feature_engineering_timeseries.py
│   ├── 03_demand_forecasting_model.py
│   ├── 03b_demand_forecasting_model.py
│   ├── 04_inventory_optimization.py
│   └── 05_business_recommendations.py
│
├── data/
│   └── stocksense_ml_features.csv
│
├── models/
│   ├── best_demand_forecasting_model_timeseries.pkl
│   └── model_features_timeseries.pkl
│
├── notebooks/
│   ├── 01_data_profiling.ipynb
│   └── 02_data_quality_assessment.ipynb
│
├── results/
│   ├── inventory_optimization_recommendations.csv
│   └── All results CSVs
│
├── screenshots/
│   ├── 01_demand_forecast.png
│   ├── 02_inventory_optimization.png
│   ├── 03_risk_action_center.png
│   └── 04_insights_recommendations.png
│
├── sql/
│   ├── 01_create_staging_tables.sql
│   ├── 02_staging_validation.sql
│   ├── 03_create_core_tables.sql
│   ├── 04_load_core_tables.sql
│   ├── 05_core_data_validation.sql
│   ├── 06_create_analytics_views.sql
│   └── 07_analytics_validation.sql
│
├── streamlit/
│   ├── app.py
│   ├── requirements.txt
│   └── pages/
│       ├── 1_Demand_Forecast.py
│       ├── 2_Inventory_Optimization.py
│       ├── 3_Risk_Action_Center.py
│       └── 4_Insights_Recommendations.py
│
├── LICENSE
└── README.MD

```

---

## Technology Stack

- **Core Language:** Python 3.10+
- **Data Manipulation & Analytics:** Pandas, NumPy
- **Machine Learning & Time-Series:** scikit-learn, SQLAlchemy
- **User Interface:** Streamlit (Wide Layout, Dark Theme)
- **Data Visualization:** Plotly Graph Objects / Express

---

## Validation & Quality Assurance

The application underwent rigorous automated validation via a 20-test verification suite:

```
============================================================
FINAL RESULT: 20 PASSED, 0 FAILED
============================================================
  [OK] TEST 1: Production CSV loads successfully
  [OK] TEST 2: Required production columns exist
  [OK] TEST 3: Store x Product grain remains unique (60,968 records)
  [OK] TEST 4: Risk categories are valid (5 tiers)
  [OK] TEST 5: Critical count matches production CSV (9,109 items)
  [OK] TEST 6: High Risk count matches production CSV (1,344 items)
  [OK] TEST 7: Excess Stock count matches production CSV (7,043 items)
  [OK] TEST 8: Inventory Value at Risk total matches production CSV ($38,141.50)
  [OK] TEST 9: Recommended Reorder Quantity total matches production CSV (7,175 units)
  [OK] TEST 10: Recommended reorder quantities are non-negative
  [OK] TEST 11: Inventory value at risk column verified
  [OK] TEST 12: NaN days_of_inventory displays as N/A
  [OK] TEST 13: Zero What-If Simulator pages remain
  [OK] TEST 14: Exactly one Insights & Recommendations page exists
  [OK] TEST 15: Production CSV row count remains unchanged (60,968)
  [OK] TEST 16: Production CSV Store x Product grain remains unchanged
  [OK] TEST 17: No aggregate_portfolio logic remains
  [OK] TEST 18: No raw What-If references remain in Streamlit navigation
  [OK] TEST 19: Insights page exists and is accessible
  [OK] TEST 20: Insights page compiles successfully (py_compile OK)
```

---

## Screenshots

Below are preview links to the four core application pages:

| Module | Preview |
|---|---|
| **Demand Forecast** | `docs/screenshots/01_demand_forecast.png` |
| **Inventory Optimization** | `docs/screenshots/02_inventory_optimization.png` |
| **Risk & Action Center** | `docs/screenshots/03_risk_action_center.png` |
| **Insights & Recommendations** | `docs/screenshots/04_insights_recommendations.png` |

---

## How to Run the Application

1. Clone or navigate to the repository directory:
   ```bash
   cd c:/Users/YASH/Desktop/Data_Science_Projects/StockSenseAI
   ```
2. Install dependencies:
   ```bash
   pip install -r streamlit/requirements.txt
   ```
3. Launch the Streamlit application:
   ```bash
   streamlit run streamlit/app.py
   ```

---

## Business Impact

- **Risk Prioritization:** Immediately isolates 9,109 critical items and 1,344 high-risk items out of 60,968 total inventory records.
- **Capital Protection:** Prescribes replenishment order quantities targeting $38,141.50 in value at risk.
- **Working Capital Efficiency:** Identifies 7,043 excess stock SKUs carrying >90 days of inventory to prevent over-purchasing.
- **Operational Clarity:** Prescribes exact item-level reorder quantities without requiring manual spreadsheet analysis.

---

## Limitations

- **Fixed Lead Time:** Lead time is currently evaluated at a default supplier horizon of 7 days across SKUs.
- **Batch Processing:** Recommendations are pre-calculated from batch model predictions on historical sales features.

---

## Future Improvements

- **Supplier Lead Time Volatility:** Incorporating variable lead time distributions ($LTD_{std}$) into safety stock calculations.
- **Multi-Echelon Optimization:** Modeling inventory transfers between distribution centers and retail stores.
