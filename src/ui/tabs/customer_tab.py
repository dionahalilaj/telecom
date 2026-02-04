import streamlit as st

from src.ui.tabs.evaluation_tab import render_evaluation_tab
from src.ui.tabs.recommendation_tab import render_recommendation_tab


def render_customer_tab(cust_df, selected_customer: int):

    st.header("Customer Dashboard")

    tab_customer, tab_reco, tab_eval = st.tabs(
        [
            "Customer view",
            "Recommendation",
            "Evaluation"
        ]
    )

    with tab_customer:
        st.subheader(f"Customer {selected_customer}")
        st.write(cust_df[["current_plan_type", "base_price_eur"]].iloc[0])

        if "dtw_cluster" in cust_df.columns and cust_df["dtw_cluster"].notna().any():
            cluster_id = int(cust_df["dtw_cluster"].iloc[0])
            st.subheader(f"Behavior Cluster: {cluster_id}")

        st.subheader("Usage over time")
        st.line_chart(
            cust_df.set_index("date")[["data_usage_mb", "voice_minutes", "roaming_data_mb"]]
        )

        st.subheader("Billing & Overuse")
        st.line_chart(cust_df.set_index("date")[["bill_amount_eur"]])

        st.write("Overuse months:", cust_df[cust_df["overuse_flag"] == 1].shape[0])
        st.write("Churned:", "Yes" if cust_df["churn_event"].sum() > 0 else "No")
        
    with tab_reco:
        render_recommendation_tab(cust_df)

    with tab_eval:
        render_evaluation_tab(cust_df, selected_customer)

