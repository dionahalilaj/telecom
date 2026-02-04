import streamlit as st
from src.ui.tabs.churn_dashboard import cluster_churn_dashboard


def render_churn_tab(df):
    st.header("Churn Dashboard by Cluster")

    if "dtw_cluster" not in df.columns:
        st.info("Run DTW clustering first to enable the churn dashboard.")
        return

    increase_pct = st.slider(
        "Unexpected bill increase threshold (% increase)",
        0.05, 0.80, 0.25, 0.05,
        key="dash_increase_pct"
    )

    dash = cluster_churn_dashboard(
        df,
        cluster_col="dtw_cluster",
        increase_pct=increase_pct
    )

    st.subheader("Cluster risk table (customer-level churn + unexpected bill increases)")
    st.dataframe(
        dash[
            [
                "cluster", "customers",
                "churn_rate_pct",
                "avg_bill",
                "avg_overuse_pct",
                "avg_unexpected_increase_rate",
                "pct_customers_with_unexpected_increase",
            ]
        ],
        use_container_width=True
    )

    st.subheader("Churn rate by cluster (%)")
    st.bar_chart(dash.set_index("cluster")["churn_rate_pct"])

    st.subheader("Unexpected bill increase exposure by cluster (% customers with ≥1 unexpected increase)")
    st.bar_chart(dash.set_index("cluster")["pct_customers_with_unexpected_increase"])

    st.caption(
        "Churn rate is computed per customer (churned if churn_event occurs in any month). "
        "Unexpected bill increase rate is computed from actual bill history (current plan) using the percentage threshold above."
    )
