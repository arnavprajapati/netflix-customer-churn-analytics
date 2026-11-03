import os
import pymongo
import streamlit as st

DB_NAME = "churn_db"
COL_NAME = "customers"

def get_mongo_uri():
    """Retrieve MongoDB connection URI from Streamlit secrets, env variables, or .env file."""
    try:
        if hasattr(st, "secrets") and "MONGO_URI" in st.secrets:
            return st.secrets["MONGO_URI"].strip().strip('"').strip("'")
    except Exception:
        pass

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

@st.cache_resource
def get_collection():
    """Return the MongoDB collection, reusing one connection per Streamlit session."""
    client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return client[DB_NAME][COL_NAME]
