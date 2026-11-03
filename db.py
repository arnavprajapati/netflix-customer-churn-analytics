import pymongo
import streamlit as st

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "churn_db"
COL_NAME = "customers"

@st.cache_resource
def get_collection():
    """Return the MongoDB collection, reusing one connection per Streamlit session."""
    client = pymongo.MongoClient(MONGO_URI)
    return client[DB_NAME][COL_NAME]
