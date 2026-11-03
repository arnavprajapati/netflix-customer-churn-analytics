import importlib
import pandas as pd
import streamlit as st
import crud
import queries
import ui_helpers
from db import get_collection

importlib.reload(crud)

ui_helpers.setup_page()

def build_sidebar(collection):
    """Render sidebar filter widgets and return the MongoDB query dict."""
    st.sidebar.markdown("## Filters")

    try:
        sub_types = ["All"] + sorted(collection.distinct("subscription.type"))
        regions = ["All"] + sorted(collection.distinct("profile.region"))
        devices = ["All"] + sorted(collection.distinct("usage.device"))
    except Exception as err:
        st.error(
            "Could not connect to MongoDB. "
            "Please verify that MONGO_URI is added in Streamlit Cloud Secrets "
            "and MongoDB Atlas Network Access allows 0.0.0.0/0 (IP access from anywhere)."
        )
        st.stop()

    selected_sub = st.sidebar.selectbox("Subscription Plan", sub_types)
    selected_reg = st.sidebar.selectbox("Region", regions)
    selected_dev = st.sidebar.selectbox("Device", devices)
    churn_status = st.sidebar.selectbox(
        "Customer Status", ["All", "Churned", "Active"]
    )
    age_range = st.sidebar.slider(
        "Age Range", min_value=18, max_value=70, value=(18, 70)
    )

    query = {}
    if selected_sub != "All":
        query["subscription.type"] = selected_sub
    if selected_reg != "All":
        query["profile.region"] = selected_reg
    if selected_dev != "All":
        query["usage.device"] = selected_dev
    if churn_status == "Churned":
        query["churned"] = True
    elif churn_status == "Active":
        query["churned"] = False

    query["profile.age"] = {"$gte": age_range[0], "$lte": age_range[1]}
    return query

def show_metrics(collection, query):
    """Fetch five KPIs and display them as metric cards."""
    total, churned, churn_rate, avg_fee, revenue_lost = queries.get_metrics(
        collection, query
    )
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        ui_helpers.metric_card("Total Customers", f"{total:,}")
    with c2:
        ui_helpers.metric_card("Churned Customers", f"{churned:,}")
    with c3:
        ui_helpers.metric_card("Churn Rate", f"{churn_rate}%")
    with c4:
        ui_helpers.metric_card("Avg Monthly Fee", f"${avg_fee}")
    with c5:
        ui_helpers.metric_card("Monthly Revenue Lost", f"${revenue_lost:,.2f}")

def show_customer_table(collection, query):
    """Display a paginated, sortable customer table fetched from MongoDB."""
    ui_helpers.section_pill("Customer Table")

    total_matched = collection.count_documents(query)

    size_col, _ = st.columns([1, 4])
    with size_col:
        page_size = st.selectbox("Rows to show", [100, 200, 500, "All"], index=0)

    limit = 0 if page_size == "All" else int(page_size)
    docs = queries.get_customers(collection, query, limit)

    rows = []
    for doc in docs:
        rows.append({
            "Customer ID": doc["customer_id"],
            "Age": doc["profile"]["age"],
            "Gender": doc["profile"]["gender"],
            "Region": doc["profile"]["region"],
            "Plan": doc["subscription"]["type"],
            "Device": doc["usage"]["device"],
            "Last Seen (days ago)": doc["usage"]["last_login_days"],
            "Total Watch Hours": doc["usage"]["watch_hours"],
            "Monthly Fee": f"${doc['subscription']['monthly_fee']}",
            "Status": "Churned" if doc["churned"] else "Active",
        })

    showing = total_matched if page_size == "All" else min(limit, total_matched)
    st.caption(f"Showing {showing:,} of {total_matched:,} customers.")

    if rows:
        df = pd.DataFrame(rows)
        ui_helpers.render_table(df, max_height="380px")
    else:
        st.info("No customers match the selected filters.")

def show_crud_forms(collection):
    """Render Add Customer, Update Customer, and Delete Customer forms side by side."""
    col1, col2, col3 = st.columns([1.2, 1.2, 1.0])

    with col1:
        ui_helpers.section_pill("Add Customer")
        with st.form("add_customer_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                age = st.number_input("Age", min_value=18, max_value=100, value=28)
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                region = st.selectbox("Region", ["North America", "Europe", "Asia",
                                                 "Africa", "South America", "Australia"])
                plan = st.selectbox("Plan", ["Basic", "Standard", "Premium"])
            with col_b:
                device = st.selectbox("Device", ["TV", "Mobile", "Tablet", "Laptop"])
                payment_method = st.selectbox("Payment Method", ["Credit Card", "Debit Card",
                                                                 "PayPal", "Gift Card", "Crypto"])
                watch_hours = st.number_input("Total Watch Hours", min_value=0.0,
                                              max_value=1000.0, value=10.0, step=0.5)
                last_login_days = st.number_input("Days Since Last Login", min_value=0,
                                                  max_value=365, value=5)
            submitted = st.form_submit_button("Add Customer", use_container_width=True)

        if submitted:
            ok, msg = crud.insert_customer(
                collection, age, gender, region, plan,
                device, payment_method, watch_hours, last_login_days
            )
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    with col2:
        ui_helpers.section_pill("Update Customer")
        with st.form("update_customer_form"):
            cust_id = st.text_input("Customer ID to update")
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                u_plan = st.selectbox("New Plan", ["Basic", "Standard", "Premium"])
                u_status = st.selectbox("New Status", ["Active", "Churned"])
                u_device = st.selectbox("Device", ["TV", "Mobile", "Tablet", "Laptop"], key="u_dev")
            with col_u2:
                u_payment = st.selectbox("Payment Method", ["Credit Card", "Debit Card",
                                                            "PayPal", "Gift Card", "Crypto"], key="u_pay")
                u_watch = st.number_input("Watch Hours", min_value=0.0,
                                          max_value=1000.0, value=15.0, step=0.5, key="u_watch")
                u_login = st.number_input("Last Login (Days)", min_value=0,
                                          max_value=365, value=10, key="u_login")
            u_submitted = st.form_submit_button("Update Customer", use_container_width=True)

        if u_submitted:
            if not cust_id.strip():
                st.error("Please enter a Customer ID.")
            else:
                is_churned = (u_status == "Churned")
                ok, msg = crud.update_customer(
                    collection, cust_id.strip(), u_plan, is_churned,
                    u_device, u_payment, u_watch, u_login
                )
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    with col3:
        ui_helpers.section_pill("Delete Customer")
        with st.form("delete_customer_form"):
            del_cust_id = st.text_input("Paste Customer ID here")
            confirmed = st.checkbox("I understand this action cannot be undone")
            submitted = st.form_submit_button("Delete Customer", use_container_width=True)

        if submitted:
            if not del_cust_id.strip():
                st.error("Please enter a Customer ID.")
            elif not confirmed:
                st.error("Please tick the confirmation checkbox first.")
            else:
                ok, msg = crud.delete_customer(collection, del_cust_id)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

def show_insights(collection):
    """Render five churn insight charts in a two-column grid."""
    ui_helpers.section_pill("Churn Insights")
    st.write("")

    col1, col2 = st.columns(2)

    with col1:
        st.caption("Churn rate by subscription plan")
        data = queries.pipeline_churn_by_subscription(collection)
        if data:
            st.plotly_chart(
                ui_helpers.make_bar(data, "plan", "churn_rate",
                                    "Subscription Plan", "Churn Rate (%)"),
                use_container_width=True,
            )

    with col2:
        st.caption("Churn rate by region")
        data = queries.pipeline_churn_by_region(collection)
        if data:
            st.plotly_chart(
                ui_helpers.make_bar(data, "region", "churn_rate",
                                    "Region", "Churn Rate (%)"),
                use_container_width=True,
            )

    col3, col4 = st.columns(2)

    with col3:
        st.caption("Churn rate by days since last login")
        data = queries.pipeline_churn_by_last_login(collection)
        if data:
            data.sort(key=lambda r: r["bucket"] if isinstance(r["bucket"], (int, float)) else 999)
            st.plotly_chart(
                ui_helpers.make_bar(data, "label", "churn_rate",
                                    "Days Since Last Login", "Churn Rate (%)"),
                use_container_width=True,
            )

    with col4:
        st.caption("Churn rate by age group")
        data = queries.pipeline_churn_by_age_group(collection)
        if data:
            data.sort(key=lambda r: r["age_group"] if isinstance(r["age_group"], int) else 999)
            st.plotly_chart(
                ui_helpers.make_bar(data, "label", "churn_rate",
                                    "Age Group", "Churn Rate (%)"),
                use_container_width=True,
            )

    st.caption("Most popular genres among churned customers")
    data = queries.pipeline_top_genres_churned(collection)
    if data:
        st.plotly_chart(
            ui_helpers.make_bar(data, "_id", "count",
                                "Favorite Genre", "Churned Customers"),
            use_container_width=True,
        )

def show_advanced_analytics(collection):
    """Render four advanced analytics charts in a two-column grid."""
    ui_helpers.section_pill("Advanced Analytics")
    st.write("")

    col1, col2 = st.columns(2)

    with col1:
        st.caption("Monthly revenue earned vs revenue lost per plan")
        data = queries.pipeline_revenue_by_plan(collection)
        if data:
            fig = ui_helpers.make_grouped_bar(
                x_vals_a=[r["plan"] for r in data],
                y_vals_a=[r["total_revenue"] for r in data],
                name_a="Total Revenue",
                x_vals_b=[r["plan"] for r in data],
                y_vals_b=[r["lost_revenue"] for r in data],
                name_b="Revenue Lost",
                x_title="Subscription Plan",
                y_title="Revenue (USD)",
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.caption("Which device type has the highest churn rate")
        data = queries.pipeline_churn_by_device(collection)
        if data:
            st.plotly_chart(
                ui_helpers.make_bar(data, "device", "churn_rate",
                                    "Device Type", "Churn Rate (%)"),
                use_container_width=True,
            )

    col3, col4 = st.columns(2)

    with col3:
        st.caption("Churn rate broken down by payment method")
        data = queries.pipeline_churn_by_payment(collection)
        if data:
            st.plotly_chart(
                ui_helpers.make_bar(data, "payment", "churn_rate",
                                    "Payment Method", "Churn Rate (%)"),
                use_container_width=True,
            )

    with col4:
        st.caption("Do churned customers watch less than active ones?")
        data = queries.pipeline_avg_watch_by_plan(collection)
        if data:
            active_rows = [r for r in data if not r["churned"]]
            churned_rows = [r for r in data if r["churned"]]
            fig = ui_helpers.make_grouped_bar(
                x_vals_a=[r["plan"] for r in active_rows],
                y_vals_a=[r["avg_hours"] for r in active_rows],
                name_a="Active",
                x_vals_b=[r["plan"] for r in churned_rows],
                y_vals_b=[r["avg_hours"] for r in churned_rows],
                name_b="Churned",
                x_title="Subscription Plan",
                y_title="Avg Watch Hours",
            )
            st.plotly_chart(fig, use_container_width=True)

def show_data_quality(collection):
    """Show flagged records in a plain-English table."""
    ui_helpers.section_pill("Data Quality Report")
    st.write("")

    docs = queries.get_flagged_documents(collection)

    rows = []
    for doc in docs:
        issues = []
        for flag in doc["flags"]:
            if flag == "invalid_daily_watch_time":
                issues.append("Daily watch hours exceed 24 — physically impossible")
            else:
                issues.append(flag)
        rows.append({
            "Customer ID": doc["customer_id"],
            "Age": doc["profile"]["age"],
            "Region": doc["profile"]["region"],
            "Plan": doc["subscription"]["type"],
            "Daily Watch Hours": doc["usage"]["avg_watch_time_per_day"],
            "Issue": " | ".join(issues),
        })

    if rows:
        st.warning(f"{len(rows)} record(s) have data quality issues and may need review.")
        df = pd.DataFrame(rows)
        ui_helpers.render_table(df, max_height="280px")
    else:
        st.success("No data quality issues found in the dataset.")

def main():
    """Assemble the full dashboard from top to bottom."""
    collection = get_collection()

    st.title("Customer Churn Analytics")
    st.write(
        "Interactive dashboard for exploring Netflix subscription churn patterns "
        "using MongoDB aggregation pipelines."
    )
    st.markdown("---")

    query = build_sidebar(collection)

    show_metrics(collection, query)
    st.markdown("---")

    show_customer_table(collection, query)
    st.markdown("---")

    show_crud_forms(collection)
    st.markdown("---")

    show_insights(collection)
    st.markdown("---")

    show_advanced_analytics(collection)
    st.markdown("---")

    show_data_quality(collection)

if __name__ == "__main__":
    main()
