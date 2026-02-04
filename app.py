import streamlit as st
import pandas as pd

from src.config import get_paths
from src.storage import (
    load_raw, load_enriched, save_enriched,
    load_centers, save_centers, load_meta,
)
from src.services.clustering_service import compute_dtw_clusters, apply_cluster_labels
from src.ui.sidebar import sidebar_clustering_controls, sidebar_customer_controls

from src.ui.tabs.plans_tab import render_plans_tab
from src.ui.tabs.customer_tab import render_customer_tab
from src.ui.tabs.recommendation_tab import render_recommendation_tab
from src.ui.tabs.evaluation_tab import render_evaluation_tab
from src.ui.tabs.cluster_view_tab import render_cluster_view_tab
from src.ui.tabs.cluster_summary_tab import render_cluster_summary_tab
from src.ui.tabs.churn_tab import render_churn_tab
from src.ui.tabs.prediction_tab import render_prediction_system_tab


def main():
    st.set_page_config(page_title="Telecom Behavior Analyzer", layout="wide")
    st.title("Telecom Customer Behavior & Plan Recommendation System")

    paths = get_paths()

    # Load artifacts
    loaded_df, fmt = load_enriched(paths)
    centers = load_centers(paths)
    meta = load_meta(paths)
    saved_k = int(meta["k"]) if meta and "k" in meta else None

    k = sidebar_clustering_controls(paths, saved_k=saved_k)

    if loaded_df is not None:
        df = loaded_df
        df["date"] = pd.to_datetime(df["date"])
        st.sidebar.success(f"Loaded enriched dataset ({fmt})")
    else:
        df = load_raw(paths)
        st.sidebar.info("Loaded raw dataset (not enriched yet)")

        if st.sidebar.button("Run DTW + Save Enriched"):
            progress = st.progress(0)
            status = st.text("Running DTW time-series clustering...")

            progress.progress(15)
            cluster_df, model = compute_dtw_clusters(df, k)

            progress.progress(70)
            df = apply_cluster_labels(df, cluster_df)

            progress.progress(85)
            save_centers(model.cluster_centers_, k, paths)
            fmt_saved, path_saved = save_enriched(df, paths)

            progress.progress(100)
            status.text("DTW complete. Saved enriched dataset ✅")
            st.sidebar.success(f"Saved ({fmt_saved}) → {path_saved}")

            st.cache_data.clear()
            st.rerun()

    selected_customer, selected_cluster = sidebar_customer_controls(df)

    # Filter customer
    cust_df = df[df["customer_id"] == selected_customer].sort_values("date")

    # Tabs
    tab_plans, tab_customer, tab_cluster, tab_pred = st.tabs(
        [
            "Plans & Costs",
            "Customer",
            "Cluster",
            "Prediction System",
        ]
    )

    with tab_plans:
        render_plans_tab()

    with tab_customer:
        render_customer_tab(cust_df, selected_customer)

    with tab_cluster:
        render_cluster_view_tab(df, centers, selected_cluster)

    with tab_pred:
        render_prediction_system_tab(df, centers)


if __name__ == "__main__":
    main()
