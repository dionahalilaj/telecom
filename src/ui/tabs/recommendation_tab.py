import pandas as pd
import streamlit as st

from src.ui.tabs.recommendation import (
    recommend_plans,
    explain_recommendation,
    build_mismatch_table,
    recommend_plans_churn_rule_based,
    expected_usage_last_months,
)


def render_recommendation_tab(cust_df):
    st.subheader("Recommendation mode")
    use_churn_aware = st.toggle("Churn-aware (avoid unexpected bill increases)", value=True)

    if use_churn_aware:
        increase_pct = st.slider(
            "Unexpected bill increase threshold: % increase",
            0.05, 0.80, 0.25, 0.05
        )
        max_unexpected_increase_rate = st.slider(
            "Max allowed rate of unexpected bill increases",
            0.0, 0.50, 0.10, 0.01
        )
        min_months = st.slider(
            "Minimum months required for churn-aware evaluation",
            2, 12, 3, 1
        )

    st.subheader(
        "Plan Recommendation",
        help=(
            "We estimate the     expected monthly usage by averaging the last N months "
            "(data, voice, SMS, roaming). For each available plan, we simulate the monthly bill: "
            "base price + extra charges if usage exceeds plan limits. Plans are ranked by lowest "
            "estimated cost (and lowest overusage cost as a tie-breaker). "
            "If churn-aware mode is enabled, we instead simulate bills month-by-month and exclude plans "
            "that show frequent unexpected bill jumps (above a chosen % threshold), then recommend the cheapest stable plan."
        )
    )

    months = st.slider("Use last N months to estimate expected usage", 3, 12, 6)

    if use_churn_aware:
        ranked = recommend_plans_churn_rule_based(
            cust_df,
            increase_pct=increase_pct,
            max_unexpected_increase_rate=max_unexpected_increase_rate,
            min_months=min_months,
        )
        usage = expected_usage_last_months(cust_df, months=months)
        bill_col = "avg_bill_eur"
    else:
        ranked, usage = recommend_plans(cust_df, months=months)
        bill_col = "expected_bill_eur"

    st.subheader("Estimated monthly usage (average)")
    usage_df = pd.DataFrame([usage]).rename(columns={
        "data_usage_mb": "Data (MB)",
        "voice_minutes": "Voice (min)",
        "sms_count": "SMS",
        "roaming_data_mb": "Roaming data (MB)",
        "roaming_minutes": "Roaming minutes"
    })
    st.dataframe(usage_df, use_container_width=True)

    current_plan = cust_df["current_plan_type"].iloc[0]

    if use_churn_aware:
        st.subheader("Plan ranking (rule-based churn-aware)")
        st.caption(
            "Rule: exclude plans with frequent unexpected bill increases, then choose the cheapest stable plan."
        )
    else:
        st.subheader("Plan ranking (expected monthly bill)")

    st.dataframe(ranked, use_container_width=True)

    best_plan = ranked.iloc[0]["plan"]
    best_bill = float(ranked.iloc[0][bill_col])

    label = "avg bill" if use_churn_aware else "expected bill"
    extra = " (churn-aware: stable billing)" if use_churn_aware else ""
    st.success(f"Recommended plan: **{best_plan}** — {label}: **€{best_bill:.2f}**{extra}")

    st.subheader("Why this plan?")
    explanations = explain_recommendation(current_plan, best_plan, usage)
    for e in explanations:
        st.write("•", e)

    cur_row = ranked[ranked["plan"] == current_plan]
    if not cur_row.empty:
        cur_bill = float(cur_row.iloc[0][bill_col])
        diff = round(cur_bill - best_bill, 2)

        if diff > 0:
            st.info(f"Estimated savings vs current plan (**{current_plan}**): **€{diff:.2f}/month**")
        elif diff < 0:
            st.info(f"Estimated increase vs current plan (**{current_plan}**): **€{abs(diff):.2f}/month**")
        else:
            st.info(f"Current plan (**{current_plan}**) is already optimal based on this estimate.")

    st.subheader("Usage vs Plan Limits (Mismatch Table)")
    mismatch_df = build_mismatch_table(usage, current_plan, best_plan)
    st.dataframe(mismatch_df, use_container_width=True)

    st.caption("Expected usage is estimated from recent history. 'OVER' means the plan limit is likely exceeded.")
