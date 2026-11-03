# Customer Churn Analytics Platform

An enterprise-grade subscription analytics dashboard and data management pipeline engineered with Python, MongoDB, and Streamlit. The platform provides real-time visibility into customer retention, churn drivers, revenue leakage, and cohort behaviors across multi-tier subscription plans.

---

## Architecture Overview

The system is built on a decoupled architecture separating data ingestion, database persistence, analytical aggregation, and presentation layers:

- **Storage Engine**: MongoDB Community Server for flexible, schema-free document persistence and nested attribute modeling.
- **Data Ingestion**: Automated ETL pipeline (`load_data.py`) performing deduplication, schema normalization, and data validation rules.
- **Aggregation Framework**: Native MongoDB pipelines for server-side analytical processing, minimizing memory footprint and network overhead.
- **Application Layer**: Streamlit dashboard with real-time reactive filters, interactive Plotly visualizations, and full CRUD transactional support.

---

## Tech Stack

| Component | Technology | Role |
|-----------|------------|------|
| Language | Python 3.9+ | Core application runtime and ETL processing |
| Database | MongoDB 6.0+ | Document store and aggregation engine |
| Driver | PyMongo | Native Python driver for MongoDB operations |
| Data Processing | Pandas | CSV batch ingestion and preprocessing |
| Web Framework | Streamlit | Reactive web dashboard and UI state management |
| Visualizations | Plotly | Interactive GPU-accelerated charting engine |

---

## Key Features

### 1. Real-Time Analytical Metrics
- Real-time KPI cards tracking total customer base, churn count, churn rate percentage, average revenue per user (ARPU), and monthly revenue loss due to churn.
- Cohort analysis broken down by subscription tiers, geographic regions, device categories, and customer tenure.

### 2. Full CRUD Operations
- **Create**: Register new customers with auto-generated UUIDs, subscription tier mapping, and dynamic pricing assignment.
- **Read**: Server-side filtered querying with pagination controls (100, 200, 500, or full dataset views).
- **Update**: Modify customer subscription plans, churn status, device preferences, and usage metrics with real-time database synchronisation via `$set`.
- **Delete**: Secure customer deletion with mandatory confirmation safeguards.

### 3. Server-Side Aggregation Pipelines
- Analytical processing executed directly on the MongoDB server via multi-stage aggregation pipelines (`$match`, `$group`, `$project`, `$bucket`, `$sort`, `$limit`).
- Minimizes application memory usage and accelerates dashboard response times.

### 4. Automated Data Quality Flagging
- Ingestion-level anomaly detection auditing daily watch metrics.
- Flags physically impossible metrics (e.g. daily watch hours exceeding 24 hours) into a dedicated audit array for manual compliance review without data loss.

---

## Data Model and Schema Design

Data is modeled using nested document architecture, categorizing customer properties into logical sub-documents:

```json
{
  "customer_id": "a9b75100-82a8-427a-a208-72f24052884a",
  "profile": {
    "age": 51,
    "gender": "Other",
    "region": "Africa"
  },
  "subscription": {
    "type": "Basic",
    "monthly_fee": 8.99,
    "payment_method": "Gift Card"
  },
  "usage": {
    "watch_hours": 14.73,
    "avg_watch_time_per_day": 0.49,
    "last_login_days": 29,
    "device": "TV",
    "number_of_profiles": 1,
    "favorite_genre": "Action"
  },
  "churned": true,
  "flags": []
}
```

### Indexing Strategy

To support high-throughput analytical queries and fast filtering, dedicated B-tree indexes are configured:

| Index Target | Type | Optimization Objective |
|--------------|------|------------------------|
| `customer_id` | Unique | Enforces record identity and prevents duplicate entries |
| `subscription.type` | Single Field | Accelerates plan-based aggregations and sidebar filters |
| `profile.region` | Single Field | Optimizes geographic grouping and cohort segmentation |
| `churned` | Single Field | Speeds up churn-specific filtering and KPI calculations |

---

## Analytics Pipeline Specifications

The analytics engine leverages dedicated MongoDB pipelines:

1. **Churn Rate by Plan**: Groups records by `subscription.type`, derives total vs churned counts, projects the percentage via `$divide` and `$multiply`, and sorts descending.
2. **Geographic Churn Distribution**: Groups by `profile.region` to identify regions with elevated subscriber attrition.
3. **Engagement Recency Analysis**: Uses `$bucket` across `usage.last_login_days` (boundaries: 0 to 60+ days) to map attrition against inactivity intervals.
4. **Demographic Age Grouping**: Employs `$bucket` across `profile.age` (brackets: 18-24, 25-34, 35-44, 45-54, 55-70) to correlate user age with retention likelihood.
5. **Content Affinity of Churned Users**: Filters with `$match: { churned: true }`, groups by `usage.favorite_genre`, and sorts to return the top 8 churned genres.
6. **Revenue Leakage Comparison**: Grouped comparative bar charts contrasting total contract revenue against lost monthly revenue per subscription tier.
7. **Device and Payment Risk Profiling**: Evaluates churn rates across hardware form factors and payment gateways.

---

## Project Structure

```
netflix-customer-churn-analytics/
|-- netflix_customer_churn.csv   # Source dataset (5,000 customer records)
|-- requirements.txt             # Project runtime dependencies
|-- .gitignore                   # Git exclusion rules
|-- load_data.py                 # ETL ingestion and index creation script
|-- db.py                        # Centralized MongoDB client connection provider
|-- crud.py                      # Data mutation services (Insert, Update, Delete)
|-- queries.py                   # Aggregation pipeline definitions and queries
|-- ui_helpers.py                # Reusable chart components and CSS injection
|-- app.py                       # Main Streamlit dashboard application
|-- .streamlit/
|   `-- config.toml              # Theme configurations (dark mode with red accent)
`-- README.md                    # System architecture and technical documentation
```

---

## Getting Started

### Prerequisites

- Python 3.9 or higher
- MongoDB Community Server running locally on `localhost:27017`

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/<YOUR-USERNAME>/netflix-customer-churn-analytics.git
   cd netflix-customer-churn-analytics
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure MongoDB service is running:
   ```bash
   # Windows (Service)
   net start MongoDB

   # Linux / macOS
   sudo systemctl start mongod
   ```

### Data Ingestion

Execute the data loader to clean the dataset, construct nested document structures, populate MongoDB, and build database indexes:

```bash
python load_data.py
```

### Launching the Dashboard

Start the Streamlit application:

```bash
streamlit run app.py
```

Access the dashboard at `http://localhost:8501`.

---

## License

This project is licensed under the MIT License.
