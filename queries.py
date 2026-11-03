def get_metrics(collection, query):
    """Run one aggregation pipeline and return five KPI numbers for the metric cards."""
    pipeline = [
        # Filter matching records
        {"$match": query},
        # Group and calculate totals
        {
            "$group": {
                "_id": None,
                "total": {"$sum": 1},
                "churned_count": {"$sum": {"$cond": ["$churned", 1, 0]}},
                "total_fee": {"$sum": "$subscription.monthly_fee"},
                "churned_fee": {
                    "$sum": {
                        "$cond": ["$churned", "$subscription.monthly_fee", 0]
                    }
                },
            }
        },
    ]

    results = list(collection.aggregate(pipeline))
    if not results:
        return 0, 0, 0.0, 0.0, 0.0

    r = results[0]
    total = r["total"]
    churned_count = r["churned_count"]
    churn_rate = round((churned_count / total) * 100, 2) if total > 0 else 0.0
    avg_fee = round(r["total_fee"] / total, 2) if total > 0 else 0.0
    revenue_lost = round(r["churned_fee"], 2)

    return total, churned_count, churn_rate, avg_fee, revenue_lost


def get_customers(collection, query, limit):
    """Fetch customer documents matching query, up to limit rows (0 = no limit)."""
    projection = {
        "_id": 0,
        "customer_id": 1,
        "profile.age": 1,
        "profile.gender": 1,
        "profile.region": 1,
        "subscription.type": 1,
        "usage.device": 1,
        "usage.last_login_days": 1,
        "usage.watch_hours": 1,
        "subscription.monthly_fee": 1,
        "churned": 1,
    }
    return list(collection.find(query, projection).limit(limit))


def pipeline_churn_by_subscription(collection):
    """Compute churn rate for each subscription plan using group, project, sort."""
    pipeline = [
        # Group by subscription type
        {
            "$group": {
                "_id": "$subscription.type",
                "total": {"$sum": 1},
                "churned_count": {"$sum": {"$cond": ["$churned", 1, 0]}},
            }
        },
        # Calculate churn rate percentage
        {
            "$project": {
                "plan": "$_id",
                "total": 1,
                "churn_rate": {
                    "$multiply": [
                        {"$divide": ["$churned_count", "$total"]},
                        100,
                    ]
                },
            }
        },
        # Sort descending by churn rate
        {"$sort": {"churn_rate": -1}},
    ]
    return list(collection.aggregate(pipeline))


def pipeline_churn_by_region(collection):
    """Compute churn rate for each geographic region using group, project, sort."""
    pipeline = [
        # Group by customer region
        {
            "$group": {
                "_id": "$profile.region",
                "total": {"$sum": 1},
                "churned_count": {"$sum": {"$cond": ["$churned", 1, 0]}},
            }
        },
        # Calculate churn rate percentage
        {
            "$project": {
                "region": "$_id",
                "total": 1,
                "churn_rate": {
                    "$multiply": [
                        {"$divide": ["$churned_count", "$total"]},
                        100,
                    ]
                },
            }
        },
        # Sort descending by churn rate
        {"$sort": {"churn_rate": -1}},
    ]
    return list(collection.aggregate(pipeline))


def pipeline_churn_by_last_login(collection):
    """Bucket customers by days since last login and compute churn rate per bucket."""
    boundaries = [0, 8, 15, 22, 30, 38, 46, 54, 61]
    pipeline = [
        # Bucket by last login recency
        {
            "$bucket": {
                "groupBy": "$usage.last_login_days",
                "boundaries": boundaries,
                "default": "Other",
                "output": {
                    "total": {"$sum": 1},
                    "churned_count": {"$sum": {"$cond": ["$churned", 1, 0]}},
                },
            }
        },
        # Calculate churn rate
        {
            "$project": {
                "bucket": "$_id",
                "total": 1,
                "churn_rate": {
                    "$multiply": [
                        {"$divide": ["$churned_count", "$total"]},
                        100,
                    ]
                },
            }
        },
    ]
    rows = list(collection.aggregate(pipeline))
    for row in rows:
        b = row["bucket"]
        if isinstance(b, (int, float)):
            idx = boundaries.index(b)
            row["label"] = (
                f"{boundaries[idx]}-{boundaries[idx+1]} days"
                if idx + 1 < len(boundaries)
                else f"{b}+ days"
            )
        else:
            row["label"] = "Other"
    return rows


def pipeline_churn_by_age_group(collection):
    """Bucket customers into age bands and compute churn rate for each band."""
    boundaries = [18, 25, 35, 45, 55, 71]
    pipeline = [
        # Bucket by age ranges
        {
            "$bucket": {
                "groupBy": "$profile.age",
                "boundaries": boundaries,
                "default": "Other",
                "output": {
                    "total": {"$sum": 1},
                    "churned_count": {"$sum": {"$cond": ["$churned", 1, 0]}},
                },
            }
        },
        # Calculate churn rate
        {
            "$project": {
                "age_group": "$_id",
                "total": 1,
                "churn_rate": {
                    "$multiply": [
                        {"$divide": ["$churned_count", "$total"]},
                        100,
                    ]
                },
            }
        },
    ]
    rows = list(collection.aggregate(pipeline))
    for row in rows:
        b = row["age_group"]
        if isinstance(b, int):
            idx = boundaries.index(b)
            row["label"] = (
                f"{boundaries[idx]}-{boundaries[idx+1]-1} yrs"
                if idx + 1 < len(boundaries)
                else f"{b}+ yrs"
            )
        else:
            row["label"] = "Other"
    return rows


def pipeline_top_genres_churned(collection):
    """Return top 8 favorite genres among churned customers using match, group, sort, limit."""
    pipeline = [
        # Filter for churned customers
        {"$match": {"churned": True}},
        # Group by genre and count
        {
            "$group": {
                "_id": "$usage.favorite_genre",
                "count": {"$sum": 1},
            }
        },
        # Sort descending by count
        {"$sort": {"count": -1}},
        # Limit to top 8
        {"$limit": 8},
    ]
    return list(collection.aggregate(pipeline))


def pipeline_revenue_by_plan(collection):
    """Compute total monthly revenue and revenue lost to churn, grouped by plan."""
    pipeline = [
        # Group by subscription plan and sum revenues
        {
            "$group": {
                "_id": "$subscription.type",
                "total_revenue": {"$sum": "$subscription.monthly_fee"},
                "lost_revenue": {
                    "$sum": {
                        "$cond": ["$churned", "$subscription.monthly_fee", 0]
                    }
                },
            }
        },
        # Project output fields
        {
            "$project": {
                "plan": "$_id",
                "total_revenue": 1,
                "lost_revenue": 1,
            }
        },
        # Sort by total revenue
        {"$sort": {"total_revenue": -1}},
    ]
    return list(collection.aggregate(pipeline))


def pipeline_churn_by_device(collection):
    """Compute churn rate for each device type using group, project, sort."""
    pipeline = [
        # Group by device
        {
            "$group": {
                "_id": "$usage.device",
                "total": {"$sum": 1},
                "churned_count": {"$sum": {"$cond": ["$churned", 1, 0]}},
            }
        },
        # Calculate churn rate
        {
            "$project": {
                "device": "$_id",
                "total": 1,
                "churn_rate": {
                    "$multiply": [
                        {"$divide": ["$churned_count", "$total"]},
                        100,
                    ]
                },
            }
        },
        # Sort descending
        {"$sort": {"churn_rate": -1}},
    ]
    return list(collection.aggregate(pipeline))


def pipeline_churn_by_payment(collection):
    """Compute churn rate for each payment method using group, project, sort."""
    pipeline = [
        # Group by payment method
        {
            "$group": {
                "_id": "$subscription.payment_method",
                "total": {"$sum": 1},
                "churned_count": {"$sum": {"$cond": ["$churned", 1, 0]}},
            }
        },
        # Calculate churn rate
        {
            "$project": {
                "payment": "$_id",
                "total": 1,
                "churn_rate": {
                    "$multiply": [
                        {"$divide": ["$churned_count", "$total"]},
                        100,
                    ]
                },
            }
        },
        # Sort descending
        {"$sort": {"churn_rate": -1}},
    ]
    return list(collection.aggregate(pipeline))


def pipeline_avg_watch_by_plan(collection):
    """Compare average watch hours of active vs churned customers, grouped by plan."""
    pipeline = [
        # Group by plan and churn status
        {
            "$group": {
                "_id": {
                    "plan": "$subscription.type",
                    "churned": "$churned",
                },
                "avg_hours": {"$avg": "$usage.watch_hours"},
                "count": {"$sum": 1},
            }
        },
        # Project and round average hours
        {
            "$project": {
                "plan": "$_id.plan",
                "churned": "$_id.churned",
                "avg_hours": {"$round": ["$avg_hours", 1]},
                "count": 1,
            }
        },
        # Sort by plan
        {"$sort": {"plan": 1, "churned": 1}},
    ]
    return list(collection.aggregate(pipeline))


def get_flagged_documents(collection):
    """Return all documents that have at least one data quality flag."""
    projection = {
        "_id": 0,
        "customer_id": 1,
        "profile.age": 1,
        "profile.region": 1,
        "subscription.type": 1,
        "usage.avg_watch_time_per_day": 1,
        "flags": 1,
    }
    return list(collection.find({"flags": {"$ne": []}}, projection))
