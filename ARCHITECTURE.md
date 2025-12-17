# PYLON Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         PYLON Platform                          │
│              Energy Operations Backbone                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Presentation Layer                           │
├─────────────────────────────────────────────────────────────────┤
│  app.py (Home)                                                  │
│  ├─ Global Controls (Filters, Governance Badges)               │
│  ├─ Action Inbox                                               │
│  └─ Quick Links                                                │
│                                                                  │
│  pages/                                                         │
│  ├─ 1_energy_intelligence.py                                   │
│  │   ├─ Overview                                               │
│  │   ├─ Plan vs Actual                                         │
│  │   └─ Bill vs Actual                                         │
│  │                                                              │
│  ├─ 2_performance_risk.py                                      │
│  │   ├─ Project Performance                                    │
│  │   └─ Risk Monitoring                                        │
│  │                                                              │
│  ├─ 3_optimization.py                                          │
│  │   ├─ Contract Power Optimization                            │
│  │   ├─ Anomaly Detection                                      │
│  │   └─ Zero Usage Sites                                       │
│  │                                                              │
│  └─ 4_validation.py                                            │
│      ├─ 3G Phase-Out Validation                                │
│      └─ IDEA Experiments                                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Component Layer                              │
├─────────────────────────────────────────────────────────────────┤
│  components/                                                    │
│  ├─ global_controls.py                                         │
│  │   ├─ render_global_controls()                              │
│  │   ├─ render_governance_badges()                            │
│  │   └─ apply_filters()                                       │
│  │                                                              │
│  ├─ action_inbox.py                                            │
│  │   ├─ render_action_inbox()                                 │
│  │   └─ render_compact_action_inbox()                         │
│  │                                                              │
│  └─ widget_card.py                                             │
│      ├─ render_widget_card()                                   │
│      └─ render_simple_metric_card()                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                         │
├─────────────────────────────────────────────────────────────────┤
│  src/                                                           │
│  ├─ models.py                                                  │
│  │   ├─ Action (dataclass)                                    │
│  │   ├─ Experiment (dataclass)                                │
│  │   ├─ GovernanceBadge (dataclass)                           │
│  │   └─ Enums (Status, Category, Source, State)              │
│  │                                                              │
│  ├─ analytics.py                                               │
│  │   ├─ calculate_plan_variance()                             │
│  │   ├─ calculate_bill_actual_error()                         │
│  │   ├─ calculate_risk_score()                                │
│  │   ├─ classify_bill_actual_mismatch()                       │
│  │   ├─ detect_zero_usage_sites()                             │
│  │   ├─ recommend_contract_power_adjustment()                 │
│  │   ├─ decompose_cost_variance()                             │
│  │   ├─ calculate_yoy_comparison()                            │
│  │   ├─ calculate_anomaly_score()                             │
│  │   └─ calculate_kwh_per_traffic()                           │
│  │                                                              │
│  ├─ actions.py                                                 │
│  │   └─ ActionManager                                          │
│  │       ├─ create_action()                                   │
│  │       ├─ update_action_status()                            │
│  │       ├─ get_actions_by_owner()                            │
│  │       └─ get_action_stats()                                │
│  │                                                              │
│  └─ experiments.py                                             │
│      └─ ExperimentManager                                      │
│          ├─ create_experiment()                                │
│          ├─ update_experiment()                                │
│          └─ get_active_experiments()                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Data Access Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  src/data_access.py                                            │
│  └─ DataAccessLayer                                            │
│      ├─ load_bills()           [@st.cache_data]               │
│      ├─ load_actual()          [@st.cache_data]               │
│      ├─ load_plan()            [@st.cache_data]               │
│      ├─ load_traffic()         [@st.cache_data]               │
│      ├─ load_site_master()     [@st.cache_data]               │
│      └─ upload_data()                                          │
│                                                                  │
│  src/sample_data.py                                            │
│  └─ generate_sample_data()                                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Persistence Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  data/                                                          │
│  ├─ sample_bills.parquet                                       │
│  ├─ sample_actual.parquet                                      │
│  ├─ sample_plan.parquet                                        │
│  ├─ sample_traffic.parquet                                     │
│  ├─ sample_site_master.parquet                                 │
│  ├─ actions.parquet           (persistent)                     │
│  └─ experiments.parquet        (persistent)                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. Read Operation (조회)
```
User Request
    ↓
Page Component
    ↓
Business Logic (analytics.py)
    ↓
Data Access Layer (with caching)
    ↓
Parquet Files
    ↓
[Return DataFrame]
    ↓
Component Rendering (Plotly charts)
    ↓
Display to User
```

### 2. Write Operation (조치 생성)
```
User Action (Click "조치 생성")
    ↓
Widget Card Component
    ↓
ActionManager.create_action()
    ↓
Generate Action ID
    ↓
Save to actions.parquet
    ↓
Success Feedback
    ↓
st.rerun() → Refresh UI
```

### 3. Filter Application
```
User selects filters (기간, 지역, 설비유형)
    ↓
Global Controls Component
    ↓
Return filter dict
    ↓
apply_filters() helper
    ↓
Filtered DataFrame
    ↓
Analysis & Visualization
```

---

## Component Interaction Diagram

```
┌──────────────┐
│   app.py     │  ← Main Entry Point
│   (Home)     │
└──────┬───────┘
       │
       ├─────────────────────────────────────────┐
       │                                         │
       ▼                                         ▼
┌─────────────┐                         ┌──────────────┐
│  Pages/     │                         │ Components/  │
│  4 Menus    │◄────────────────────────│ Reusable UI  │
└──────┬──────┘                         └──────┬───────┘
       │                                       │
       │  uses                          uses   │
       ▼                                       ▼
┌──────────────────────────────────────────────────────┐
│              Business Logic (src/)                    │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐ │
│  │ analytics  │  │   actions   │  │ experiments  │ │
│  └────────────┘  └─────────────┘  └──────────────┘ │
└────────────────────┬─────────────────────────────────┘
                     │
                     │  reads/writes
                     ▼
┌──────────────────────────────────────────────────────┐
│            Data Access Layer (DAL)                    │
│         with @st.cache_data caching                   │
└────────────────────┬─────────────────────────────────┘
                     │
                     │  reads/writes
                     ▼
┌──────────────────────────────────────────────────────┐
│             Parquet Files (data/)                     │
│     Auto-generated on first run if missing            │
└──────────────────────────────────────────────────────┘
```

---

## Action Lifecycle Flow

```
┌──────────────────────────────────────────────────────────────┐
│                     Action Lifecycle                         │
└──────────────────────────────────────────────────────────────┘

1. Discovery Phase
   ┌──────────────┐
   │ User browses │
   │ analytics    │
   │ pages        │
   └──────┬───────┘
          │
          │ identifies issue
          ▼
   ┌──────────────┐
   │ Widget Card  │
   │ displays     │
   │ evidence     │
   └──────┬───────┘

2. Action Creation
          │
          │ click "조치 생성"
          ▼
   ┌──────────────┐
   │ Fill form:   │
   │ - Owner      │
   │ - Due date   │
   │ - Category   │
   └──────┬───────┘
          │
          │ submit
          ▼
   ┌──────────────┐
   │ ActionManager│
   │ .create()    │
   └──────┬───────┘
          │
          │ save
          ▼
   ┌──────────────┐
   │ actions      │
   │ .parquet     │
   └──────┬───────┘

3. Tracking Phase
          │
          │ periodic review
          ▼
   ┌──────────────┐
   │ Action Inbox │
   │ shows status │
   └──────┬───────┘
          │
          │ update status
          ▼
   ┌──────────────┐
   │ TODO →       │
   │ DOING →      │
   │ DONE         │
   └──────┬───────┘

4. Validation Phase
          │
          │ completed
          ▼
   ┌──────────────┐
   │ Validation   │
   │ Page         │
   │ (Page 4)     │
   └──────┬───────┘
          │
          │ verify results
          ▼
   ┌──────────────┐
   │ Mark as      │
   │ Verified     │
   └──────────────┘
```

---

## Risk Calculation Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  Risk Score Calculation                       │
└──────────────────────────────────────────────────────────────┘

Input Data:
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Bills     │   │   Actual    │   │   History   │
│  (청구서)    │   │ (실사용량)    │   │  (과거이력)  │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │
       └────────┬────────┴────────┬────────┘
                │                 │
                ▼                 ▼
         ┌────────────┐    ┌────────────┐
         │  Impact    │    │ Likelihood │
         │  Calc      │    │   Calc     │
         └──────┬─────┘    └──────┬─────┘
                │                 │
                └────────┬────────┘
                         │
                         ▼
                  ┌─────────────┐
                  │ Confidence  │
                  │   Factor    │
                  └──────┬──────┘
                         │
                         ▼
            ┌────────────────────────┐
            │  Risk Score Formula:   │
            │  (impact/10M) ×        │
            │  likelihood ×          │
            │  confidence            │
            └────────┬───────────────┘
                     │
                     ▼
            ┌────────────────────┐
            │  Classification:   │
            │  High (>0.7)       │
            │  Medium (0.4-0.7)  │
            │  Low (<0.4)        │
            └────────────────────┘
```

---

## Testing Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Test Structure                             │
└──────────────────────────────────────────────────────────────┘

tests/
└─ test_analytics.py
   │
   ├─ TestPlanVariance
   │  ├─ test_basic_variance()
   │  ├─ test_negative_variance()
   │  └─ test_zero_plan()
   │
   ├─ TestBillActualError
   │  ├─ test_positive_error()
   │  ├─ test_negative_error()
   │  └─ test_zero_bill()
   │
   ├─ TestRiskScore
   │  ├─ test_high_risk()
   │  ├─ test_low_risk()
   │  └─ test_zero_impact()
   │
   ├─ TestBillActualClassification
   │  ├─ test_normal_range()
   │  ├─ test_investigation_needed()
   │  ├─ test_urgent_investigation()
   │  ├─ test_explainable_fixed_rate()
   │  └─ test_missing_data()
   │
   ├─ TestZeroUsageDetection
   │  ├─ test_detect_zero_sites()
   │  └─ test_no_zero_sites()
   │
   ├─ TestCostVarianceDecomposition
   │  ├─ test_usage_effect_only()
   │  ├─ test_price_effect_only()
   │  └─ test_zero_plan_kwh()
   │
   ├─ TestYoYComparison
   │  ├─ test_basic_yoy()
   │  ├─ test_no_previous_year()
   │  └─ test_zero_previous_value()
   │
   └─ TestContractPowerRecommendation
      ├─ test_reduction_recommendation()
      └─ test_no_data()

Total: 30+ test cases covering all analytics functions
```

---

## Deployment Options

### Option 1: Local Development
```
Developer Machine
    ↓
python -m venv venv
    ↓
pip install -r requirements.txt
    ↓
streamlit run app.py
    ↓
Browser: http://localhost:8501
```

### Option 2: Streamlit Cloud
```
GitHub Repository
    ↓
Push code
    ↓
Streamlit Cloud
    ↓
Auto-deploy
    ↓
Public URL: https://pylon.streamlit.app
```

### Option 3: Docker
```
Dockerfile
    ↓
docker build -t pylon .
    ↓
docker run -p 8501:8501 pylon
    ↓
Browser: http://localhost:8501
```

### Option 4: On-Premises
```
Production Server
    ↓
systemd service
    ↓
nginx reverse proxy
    ↓
HTTPS: https://pylon.skt.com
```

---

## Security Considerations

```
┌──────────────────────────────────────────────────────────────┐
│                    Security Layers                            │
└──────────────────────────────────────────────────────────────┘

1. Input Validation
   ├─ Schema validation (required columns)
   ├─ Data type checking
   └─ File type restrictions (.csv, .parquet only)

2. Data Access Control
   ├─ File-based persistence (local access only)
   ├─ No external database credentials in code
   └─ Environment variables for sensitive config

3. Error Handling
   ├─ Try-except blocks for all I/O operations
   ├─ Graceful degradation (empty DataFrames)
   └─ User-friendly error messages

4. Future Enhancements
   ├─ SSO integration (SKT authentication)
   ├─ Role-based access control (RBAC)
   ├─ Audit logging (who did what when)
   └─ Data encryption at rest
```

---

## Performance Optimization

```
┌──────────────────────────────────────────────────────────────┐
│                 Performance Strategy                          │
└──────────────────────────────────────────────────────────────┘

1. Caching
   @st.cache_data(ttl=3600)
   ├─ All data loading functions
   ├─ 1-hour cache lifetime
   └─ Automatic invalidation on file change

2. Data Format
   Parquet files
   ├─ Columnar storage (10x faster than CSV)
   ├─ Built-in compression
   └─ Efficient filtering

3. Query Optimization
   ├─ Filter early (before aggregation)
   ├─ Select only needed columns
   └─ Use vectorized operations (pandas)

4. UI Optimization
   ├─ Lazy loading (expanders)
   ├─ Pagination (head/tail)
   └─ Progressive rendering
```

---

*PYLON Architecture v1.0.0 | SKT Network센터*






