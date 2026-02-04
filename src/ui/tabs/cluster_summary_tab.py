import pandas as pd
import streamlit as st
from src.ui.tabs.recommendation import recommend_plans_from_usage


def render_cluster_summary_tab(df: pd.DataFrame, selected_cluster):
    st.header("Cluster Summary")

    if selected_cluster is None or "dtw_cluster" not in df.columns:
        st.info("Run DTW and select a cluster to view summary.")
        return

    cluster_df = df[df["dtw_cluster"] == selected_cluster].copy()

    st.subheader(f"Cluster {int(selected_cluster)} overview")
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Customers", int(cluster_df["customer_id"].nunique()))
    col2.metric("Churn rate", f"{cluster_df['churn_event'].mean() * 100:.2f}%")
    col3.metric("Overuse rate", f"{cluster_df['overuse_flag'].mean() * 100:.2f}%")
    col4.metric("Avg bill (€)", f"{cluster_df['bill_amount_eur'].mean():.2f}")

    months_cluster = st.slider("Months used for cluster averages", 3, 12, 6, key="cluster_months")

    last_n = (
        cluster_df.sort_values("date")
        .groupby("customer_id", as_index=False)
        .tail(months_cluster)
    )

    usage = {
        "data_usage_mb": float(last_n["data_usage_mb"].mean()),
        "voice_minutes": float(last_n["voice_minutes"].mean()),
        "sms_count": float(last_n["sms_count"].mean()),
        "roaming_data_mb": float(last_n["roaming_data_mb"].mean()),
        "roaming_minutes": float(last_n["roaming_minutes"].mean()),
    }

    st.subheader("Cluster-average usage (estimated)")
    usage_view = pd.DataFrame([usage]).rename(columns={
        "data_usage_mb": "Data (MB)",
        "voice_minutes": "Voice (min)",
        "sms_count": "SMS",
        "roaming_data_mb": "Roaming data (MB)",
        "roaming_minutes": "Roaming minutes"
    })
    st.dataframe(usage_view, use_container_width=True)

    ranked_cluster = recommend_plans_from_usage(usage)
    st.subheader("Recommended plans for this cluster (based on cluster-average behavior)")
    st.dataframe(ranked_cluster.head(5), use_container_width=True)

    best_plan = ranked_cluster.iloc[0]["plan"]
    best_bill = float(ranked_cluster.iloc[0]["expected_bill_eur"])
    st.success(f"Best plan for this cluster: **{best_plan}** (expected bill ≈ **€{best_bill:.2f}**)")

    st.subheader("Current plan distribution inside this cluster")
    plan_counts = (
        cluster_df[["customer_id", "current_plan_type"]]
        .drop_duplicates()
        ["current_plan_type"]
        .value_counts()
    )
    st.bar_chart(plan_counts)
