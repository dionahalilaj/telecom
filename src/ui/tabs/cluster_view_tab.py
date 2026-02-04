import pandas as pd
import streamlit as st

from src.ui.tabs.churn_tab import render_churn_tab
from src.ui.tabs.cluster_summary_tab import render_cluster_summary_tab


def month_index_for_centers(df: pd.DataFrame, T: int) -> pd.DatetimeIndex:
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"])

    month_index = (
        d["date"]
        .dt.to_period("M")
        .drop_duplicates()
        .sort_values()
        .iloc[-T:]
        .dt.to_timestamp()
    )
    return pd.DatetimeIndex(month_index)


def render_cluster_view_tab(df: pd.DataFrame, centers, selected_cluster):

    st.header("Cluster Dashboard")

    tab_cluster, tab_summary, tab_churn = st.tabs(
        [
            "Cluster View",
            "Cluster Summary",
            "Churn Dashboard",
        ]
    )

    with tab_cluster:
        st.subheader("Average cluster behavior")

        if selected_cluster is None:
            st.info("Select a cluster to view its average behavior.")
            return

        if centers is None:
            st.info("No saved cluster centers found yet. Run DTW once to generate them.")
            return

        center = centers[int(selected_cluster)]
        center_df = pd.DataFrame(
            center,
            columns=[
                "Data usage (normalized)",
                "Voice minutes (normalized)",
                "Roaming data (normalized)",
                "Bill amount (normalized)",
            ],
        )

        T = len(center_df)
        center_df.index = month_index_for_centers(df, T)
        center_df.index.name = "Month"

        st.line_chart(center_df)
        st.caption(
            "Values are normalized (z-score). "
            "Positive values indicate above-average usage relative to the all clients."
        )

    with tab_summary:
        render_cluster_summary_tab(df, selected_cluster)

    with tab_churn:
        render_churn_tab(df)

