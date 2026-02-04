import pandas as pd
import streamlit as st
from src.ui.tabs.prediction_system import render_prediction_tab


def render_prediction_system_tab(df: pd.DataFrame, centers):
    st.header("Prediction System (Data Usage)")

    sub_overview, sub_prediction = st.tabs(["Data Usage overview", "Prediction"])

    with sub_overview:
        st.subheader("Data usage overview between clusters")

        if centers is None:
            st.info("No saved cluster centers found yet. Run DTW once to generate them.")
        else:
            k_centers = centers.shape[0]
            t_steps = centers.shape[1]

            min_date = pd.to_datetime(df["date"]).min()
            start_month = min_date.to_period("M").to_timestamp()
            x_dates = pd.date_range(start=start_month, periods=t_steps, freq="MS")

            usage_lines = {f"Cluster {c}": centers[c, :, 0] for c in range(k_centers)}
            usage_df = pd.DataFrame(usage_lines, index=x_dates)
            usage_df.index.name = "Month"

            st.line_chart(usage_df)

            st.caption(
                "Each line is the DTW cluster center for **Data usage (normalized)** over time. "
                "Values are z-scores (above 0 = above-average usage)."
            )

    with sub_prediction:
        render_prediction_tab(df, centers)
