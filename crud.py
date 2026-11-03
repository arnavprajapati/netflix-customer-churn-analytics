import uuid

PLAN_FEE = {
    "Basic": 8.99,
    "Standard": 13.99,
    "Premium": 17.99,
}

def insert_customer(collection, age, gender, region, plan,
                    device, payment_method, watch_hours, last_login_days):
    """Build a nested document and insert it into MongoDB; return (ok, message)."""
    new_doc = {
        "customer_id": str(uuid.uuid4()),
        "profile": {
            "age": int(age),
            "gender": gender,
            "region": region,
        },
        "subscription": {
            "type": plan,
            "monthly_fee": PLAN_FEE[plan],
            "payment_method": payment_method,
        },
        "usage": {
            "watch_hours": float(watch_hours),
            "avg_watch_time_per_day": 0.0,
            "last_login_days": int(last_login_days),
            "device": device,
            "number_of_profiles": 1,
            "favorite_genre": "Unknown",
        },
        "churned": False,
        "flags": [],
    }
    try:
        collection.insert_one(new_doc)
        return True, f"Customer added. ID: {new_doc['customer_id']}"
    except Exception as err:
        return False, f"Could not add customer: {err}"

def update_customer(collection, customer_id, plan, churned,
                    device, payment_method, watch_hours, last_login_days):
    """Update subscription and usage details for an existing customer; return (ok, message)."""
    update_data = {
        "subscription.type": plan,
        "subscription.monthly_fee": PLAN_FEE[plan],
        "subscription.payment_method": payment_method,
        "churned": bool(churned),
        "usage.device": device,
        "usage.watch_hours": float(watch_hours),
        "usage.last_login_days": int(last_login_days),
    }
    try:
        result = collection.update_one(
            {"customer_id": customer_id.strip()},
            {"$set": update_data}
        )
        if result.matched_count == 0:
            return False, "No customer found with that ID."
        return True, f"Customer '{customer_id.strip()}' updated successfully."
    except Exception as err:
        return False, f"Could not update customer: {err}"

def delete_customer(collection, customer_id):
    """Delete the customer with the given customer_id; return (ok, message)."""
    result = collection.delete_one({"customer_id": customer_id.strip()})
    if result.deleted_count == 1:
        return True, "Customer deleted successfully."
    return False, "No customer found with that ID."
