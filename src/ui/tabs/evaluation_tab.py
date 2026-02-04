import streamlit as st

from src.ui.tabs.recommendation import recommend_plans, recommend_plans_churn_rule_based
from src.ui.tabs.evaluation import evaluate_before_after


def render_evaluation_tab(cust_df, selected_customer: int):
    st.header("Evaluation: Current Plan vs Recommended Plan")

    increase_pct_eval = st.slider(
        "Unexpected bill increase threshold (% increase)",
        0.05, 0.80, 0.25, 0.05,
        key="eval_increase_pct"
    )

    eval_mode = st.radio(
        "Recommendation to evaluate",
        ["Cost-based recommendation", "Churn-aware recommendation (rule-based)"],
        horizontal=True
    )

    current_plan = cust_df["current_plan_type"].iloc[0]

    if eval_mode == "Cost-based recommendation":
        ranked_eval, _ = recommend_plans(cust_df, months=6)
        recommended_plan = ranked_eval.iloc[0]["plan"]
    else:
        ranked_eval = recommend_plans_churn_rule_based(
            cust_df,
            increase_pct=increase_pct_eval,
            max_unexpected_increase_rate=0.10,
            min_months=3,
        )
        recommended_plan = ranked_eval.iloc[0]["plan"]

    st.subheader(f"Customer: {selected_customer}")
    st.write(f"Current plan: **{current_plan}**")
    st.write(f"Recommended plan: **{recommended_plan}**")

    eval_df = evaluate_before_after(
        cust_df,
        current_plan=current_plan,
        recommended_plan=recommended_plan,
        increase_pct=increase_pct_eval
    )

    st.subheader("Before / After metrics (simulated under each plan)")
    st.dataframe(eval_df, use_container_width=True)

    before = eval_df.iloc[0]
    after = eval_df.iloc[1]

    c1, c2, c3 = st.columns(3)
    c1.metric(
        "Avg bill (€)",
        f"{before['avg_bill_eur']:.2f}",
        f"{after['avg_bill_eur'] - before['avg_bill_eur']:+.2f}"
    )
    c2.metric(
        "Unexpected bill increase rate",
        f"{before['unexpected_increase_rate']:.3f}",
        f"{after['unexpected_increase_rate'] - before['unexpected_increase_rate']:+.3f}"
    )
    c3.metric(
        "Overuse rate",
        f"{before['overuse_rate']:.3f}",
        f"{after['overuse_rate'] - before['overuse_rate']:+.3f}"
    )

    st.caption(
        "Bills are simulated from the customer’s actual monthly usage under each candidate plan. "
        "Unexpected bill increase rate is the fraction of month-to-month transitions where the bill rises "
        f"by more than {increase_pct_eval:.0%}. "
        "Overuse rate is the fraction of months where any plan limit is exceeded."
    )
