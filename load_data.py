import os
import pandas as pd
import pymongo

DB_NAME = "churn_db"
COL_NAME = "customers"
CSV_PATH = "netflix_customer_churn.csv"

def get_mongo_uri():
    """Retrieve MongoDB connection URI from environment variable or .env file."""
    uri = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI")
    if uri:
        return uri.strip().strip('"').strip("'")

    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("MONGO_URI="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
                if line.startswith("MONGODB_URI="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
                if line.startswith("mongodb://") or line.startswith("mongodb+srv://"):
                    return line.strip().strip('"').strip("'")

    return "mongodb://localhost:27017/"

MONGO_URI = get_mongo_uri()

def read_and_clean_csv(path):
    """Read the CSV file and remove rows with duplicate customer_id values."""
    df = pd.read_csv(path)
    before = len(df)
    df = df.drop_duplicates(subset="customer_id")
    after = len(df)
    print(f"Rows read: {before}  |  After dropping duplicates: {after}")
    return df

def build_document(row):
    """Convert one pandas row into the nested MongoDB document structure."""
    flags = []
    if row["avg_watch_time_per_day"] > 24:
        flags.append("invalid_daily_watch_time")

    document = {
        "customer_id": row["customer_id"],
        "profile": {
            "age": int(row["age"]),
            "gender": row["gender"],
            "region": row["region"],
        },
        "subscription": {
            "type": row["subscription_type"],
            "monthly_fee": float(row["monthly_fee"]),
            "payment_method": row["payment_method"],
        },
        "usage": {
            "watch_hours": float(row["watch_hours"]),
            "avg_watch_time_per_day": float(row["avg_watch_time_per_day"]),
            "last_login_days": int(row["last_login_days"]),
            "device": row["device"],
            "number_of_profiles": int(row["number_of_profiles"]),
            "favorite_genre": row["favorite_genre"],
        },
        "churned": bool(row["churned"]),
        "flags": flags,
    }
    return document

def create_indexes(collection):
    """Create MongoDB indexes for fast querying on common filter fields."""
    collection.create_index("customer_id", unique=True)
    collection.create_index("subscription.type")
    collection.create_index("profile.region")
    collection.create_index("churned")
    print("Indexes created: customer_id (unique), subscription.type, profile.region, churned")

def load_to_mongo(df):
    """Insert all cleaned rows into MongoDB and print summary statistics."""
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COL_NAME]

    collection.drop()
    print(f"Old '{COL_NAME}' collection dropped (if it existed).")

    documents = [build_document(row) for _, row in df.iterrows()]
    result = collection.insert_many(documents)
    saved = len(result.inserted_ids)
    flagged = collection.count_documents({"flags": {"$ne": []}})

    create_indexes(collection)

    print(f"Documents saved: {saved}")
    print(f"Documents with flags: {flagged}")
    client.close()

def main():
    """Orchestrate CSV reading, cleaning, and MongoDB loading."""
    df = read_and_clean_csv(CSV_PATH)
    load_to_mongo(df)
    print("Done. Run streamlit run app.py to open the dashboard.")

if __name__ == "__main__":
    main()
