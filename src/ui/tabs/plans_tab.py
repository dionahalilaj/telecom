import pandas as pd
import streamlit as st
from src.ui.tabs.plans import PLAN_LIMITS, COSTS


def render_plans_tab():
    st.header("Plans & Costs Catalog")

    st.subheader("Plan limits and base prices")
    plans_df = (
        pd.DataFrame.from_dict(PLAN_LIMITS, orient="index")
        .reset_index()
        .rename(columns={"index": "plan"})
    )

    col_order = [
        "plan",
        "base_price_eur",
        "data_limit_mb",
        "voice_limit_min",
        "sms_limit",
        "roaming_limit_mb",
        "roaming_limit_min",
    ]
    plans_df = plans_df[col_order]
    st.dataframe(plans_df, use_container_width=True)

    st.subheader("Overusage costs (billing rules)")
    costs_df = (
        pd.DataFrame([COSTS])
        .T.reset_index()
        .rename(columns={"index": "cost_type", 0: "cost_value"})
    )
    st.dataframe(costs_df, use_container_width=True)
