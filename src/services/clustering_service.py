import pandas as pd
import streamlit as st

from src.services.preprocessing import build_time_series
from src.services.dtw_clustering import dtw_cluster


@st.cache_data
def compute_dtw_clusters(df: pd.DataFrame, k: int):
    time_series_data, customer_ids = build_time_series(df)
    labels, model = dtw_cluster(time_series_data, k=k)
    cluster_df = pd.DataFrame({"customer_id": customer_ids, "dtw_cluster": labels})
    return cluster_df, model


def apply_cluster_labels(df: pd.DataFrame, cluster_df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    cid_to_cluster = dict(zip(cluster_df["customer_id"], cluster_df["dtw_cluster"]))
    out["dtw_cluster"] = out["customer_id"].map(cid_to_cluster)
    return out
