# Customer Churn Analytics

A beginner-friendly college project that loads a Netflix customer churn dataset
into MongoDB and visualises it through a Streamlit dashboard.

---

## 1. Prerequisites

- Python 3.9 or higher
- MongoDB Community Edition running locally on port 27017

### Start MongoDB

**Windows (if installed as a service)**
```
net start MongoDB
```

**Windows (manual)**
```
"C:\Program Files\MongoDB\Server\<version>\bin\mongod.exe" --dbpath "C:\data\db"
```

**macOS / Linux**
```
mongod --dbpath /data/db
```

---

## 2. Install Dependencies

```
pip install -r requirements.txt
```

`requirements.txt` installs: `pymongo`, `pandas`, `streamlit`, `plotly`.

---

## 3. Run Order

**Step 1 — load the data (run only once, or whenever you want a fresh start)**
```
python load_data.py
```

Expected output:
```
Rows read: 5000  |  After dropping duplicates: 5000
Old 'customers' collection dropped (if it existed).
Indexes created: customer_id (unique), subscription.type, profile.region, churned
Documents saved : 5000
Documents with flags: <n>
Done. Run  streamlit run app.py  to open the dashboard.
```

**Step 2 — start the dashboard**
```
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 4. MongoDB Document Structure

Each row in the CSV is stored as one nested document:

```json
{
  "customer_id": "a9b75100-...",
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

> [!NOTE]
> `churned` is stored as a boolean (`true` / `false`), not an integer.
> `flags` contains `"invalid_daily_watch_time"` when `avg_watch_time_per_day > 24`.

---

## 5. Indexes Created

| Index field            | Type   | Purpose                                  |
|------------------------|--------|------------------------------------------|
| `customer_id`          | Unique | Prevents duplicate inserts               |
| `subscription.type`    | Single | Fast filter by plan (Basic/Standard/...) |
| `profile.region`       | Single | Fast filter by geographic region         |
| `churned`              | Single | Fast split between churned and active     |

---

## 6. Aggregation Pipelines

### Pipeline 1 — Churn Rate by Subscription Type
Stages: `$group`, `$project` (`$multiply`, `$divide`), `$sort`

- `$group` on `subscription.type`: counts total and churned customers per plan.
- `$project`: computes `churn_rate = (churned_count / total) * 100`.
- `$sort`: orders results by churn rate descending.

---

### Pipeline 2 — Churn Rate by Region
Stages: `$group`, `$project` (`$multiply`, `$divide`), `$sort`

- `$group` on `profile.region`: counts total and churned customers per region.
- `$project`: computes `churn_rate`.
- `$sort`: orders by churn rate descending.

---

### Pipeline 3 — Churn Rate by Last Login Recency
Stages: `$bucket`, `$project` (`$multiply`, `$divide`)

- `$bucket` on `usage.last_login_days` with boundaries `[0, 8, 15, 22, 30, 38, 46, 54, 61]`.
  Each bucket counts total and churned customers who last logged in within that window.
- `$project`: computes `churn_rate` for each recency bucket.

---

### Pipeline 4 — Churn Rate by Age Group
Stages: `$bucket`, `$project` (`$multiply`, `$divide`)

- `$bucket` on `profile.age` with boundaries `[18, 25, 35, 45, 55, 71]`.
- `$project`: computes `churn_rate` per age band.

---

### Pipeline 5 — Top Favorite Genres Among Churned Customers
Stages: `$match`, `$group`, `$sort`, `$limit`

- `$match`: keeps only documents where `churned` is `true`.
- `$group` on `usage.favorite_genre`: counts occurrences.
- `$sort`: most popular genre first.
- `$limit 8`: keeps only the top 8 genres.

---

## 7. Project File Structure

```
arnav-project/
|-- netflix_customer_churn.csv   # Source dataset (5000 rows)
|-- load_data.py                 # One-time script: CSV -> MongoDB
|-- app.py                       # Main Streamlit dashboard application
|-- db.py                        # MongoDB connection and database initialization
|-- crud.py                      # Create, Update, Delete customer functions
|-- queries.py                   # Aggregation pipelines and data retrieval
|-- ui_helpers.py                # Visual styling, cards, and Plotly chart builders
|-- requirements.txt             # Python dependencies
|-- .streamlit/
|   `-- config.toml              # Dark theme, red accent
`-- README.md                    # Project documentation and viva guide
```

---

## 8. CRUD Operations Overview

The application supports complete CRUD functionality with MongoDB:

| Operation | PyMongo Method | Description |
|-----------|----------------|-------------|
| **Create** | `collection.insert_one(new_doc)` | Generates a UUID for `customer_id` and inserts a new nested customer document. |
| **Read** | `collection.find(query, projection)` and `collection.aggregate(pipeline)` | Retrieves filtered customer records and computes analytics metrics. |
| **Update** | `collection.update_one({"customer_id": id}, {"$set": update_fields})` | Updates subscription plan, monthly fee, status, device, and usage stats. |
| **Delete** | `collection.delete_one({"customer_id": id})` | Permanently deletes a customer by ID after user confirmation. |

---

## 9. Viva Questions and Answers

**Q1. What is MongoDB and why did you use it instead of a plain CSV file?**
MongoDB is a NoSQL document database that stores data as JSON-like documents.
It was used because it supports nested documents (profile, subscription, usage),
efficient querying with indexes, and powerful aggregation pipelines that let us
compute statistics directly inside the database without loading all data into Python.

---

**Q2. What is the difference between a flat document and a nested document?**
A flat document stores every field at the top level (like a spreadsheet row).
A nested document groups related fields into sub-objects, for example all profile
fields (age, gender, region) live under a single `profile` key. This makes the
schema more organised and closer to how the data is conceptually structured.

---

**Q3. What does an aggregation pipeline do?**
An aggregation pipeline is a sequence of stages that transform documents step by
step. Each stage takes the output of the previous one as its input. Common stages
are `$match` (filter), `$group` (aggregate values), `$project` (compute or rename
fields), `$sort`, `$limit`, and `$bucket` (histogram-style grouping).

---

**Q4. What is `$bucket` and how is it used in this project?**
`$bucket` divides documents into ranges (buckets) based on a numeric field.
In this project it is used on `last_login_days` and `profile.age` to create
recency windows and age bands, similar to a histogram. You define the bucket
boundaries as an array; each value becomes the start of a new bucket.

---

**Q5. Why did you create indexes in MongoDB?**
Indexes work like the index at the back of a book: instead of scanning every
document, MongoDB can jump directly to matching ones. Without indexes, every
query does a full collection scan (slow for 5000+ documents). The project
creates indexes on `customer_id`, `subscription.type`, `profile.region`, and
`churned` because these fields are used most often in filters.

---

**Q6. What is the purpose of the `flags` field?**
The `flags` array stores data quality problems found during data loading.
Currently, if `avg_watch_time_per_day > 24` (impossible because a day only has
24 hours), the string `"invalid_daily_watch_time"` is added to the array.
This lets analysts quickly find and review bad records without deleting them.

---

**Q7. How does the `$cond` operator work in the `$group` stage?**
`$cond` is MongoDB's if-then-else operator. In this project it is written as
`{ "$cond": ["$churned", 1, 0] }`, which means: if the `churned` field is
`true`, return 1; otherwise return 0. Summing these 1s and 0s across the group
gives the count of churned customers.

---

**Q8. What does `insert_many` do and why is it better than inserting one document at a time?**
`insert_many` sends the entire list of documents to MongoDB in a single network
request, while calling `insert_one` in a loop sends one request per document.
For 5000 rows, a single `insert_many` is dramatically faster because it avoids
the overhead of 5000 separate round-trips between Python and the database.

---

**Q9. How does the Update operation work in PyMongo?**
The Update operation uses `collection.update_one(filter, {"$set": update_fields})`.
The filter finds the document matching the given `customer_id`. The `$set` operator
updates only the specified fields (e.g. plan, fee, churn status, device, watch hours)
without overwriting or deleting other existing fields in the document.
