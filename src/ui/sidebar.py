from typing import Optional, Tuple
import streamlit as st

from src.config import AppPaths
from src.storage import reset_artifacts


def sidebar_clustering_controls(paths: AppPaths, saved_k: Optional[int]) -> int:
    st.sidebar.subheader("Clustering")
    k = st.sidebar.slider("Number of clusters", 3, 10, 6)

    if saved_k is not None and int(saved_k) != int(k):
        st.sidebar.warning(
            f"Saved clusters were computed with k={saved_k}. "
            f"Slider is k={k}. Re-run DTW to update."
        )

    if st.sidebar.button("Reset saved DTW + enriched data"):
        reset_artifacts(paths)
        st.cache_data.clear()
        st.rerun()

    return int(k)


def sidebar_customer_controls(df) -> Tuple[int, Optional[int]]:
    st.sidebar.header("Controls")

    customer_ids = df["customer_id"].unique()
    selected_customer = st.sidebar.selectbox("Select customer", customer_ids)

    selected_cluster = None
    if "dtw_cluster" in df.columns:
        clusters = sorted(df["dtw_cluster"].dropna().unique())
        selected_cluster = st.sidebar.selectbox("Select cluster", clusters)
    else:
        st.sidebar.warning("Run DTW to enable clusters.")

    st.session_state["customer_ids"] = customer_ids
    st.session_state["labels"] = df["dtw_cluster"].unique() if "dtw_cluster" in df.columns else []

    return selected_customer, selected_cluster
