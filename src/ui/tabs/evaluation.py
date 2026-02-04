import pandas as pd

from src.ui.tabs.recommendation import (
    PLAN_LIMITS,
    simulate_bill,                     # uses the cost model
    unexpected_bill_increase_metrics,  # percentage-only, new churn-aware metric
)

def month_overuse(row: pd.Series, plan: dict) -> int:
    return int(
        (row["data_usage_mb"] > plan["data_limit_mb"]) or
        (row["voice_minutes"] > plan["voice_limit_min"]) or
        (row["sms_count"] > plan["sms_limit"]) or
        (row["roaming_data_mb"] > plan["roaming_limit_mb"]) or
        (row["roaming_minutes"] > plan["roaming_limit_min"])
    )

def simulate_monthly_bills_under_plan(cust_df: pd.DataFrame, plan_name: str) -> pd.Series:
    plan = PLAN_LIMITS[plan_name]
    g = cust_df.sort_values("date")

    bills = g.apply(
        lambda r: simulate_bill({
            "data_usage_mb": float(r["data_usage_mb"]),
            "voice_minutes": float(r["voice_minutes"]),
            "sms_count": float(r["sms_count"]),
            "roaming_data_mb": float(r["roaming_data_mb"]),
            "roaming_minutes": float(r["roaming_minutes"]),
        }, plan)["expected_bill_eur"],
        axis=1
    )

    bills.index = g["date"].values
    return bills

def overuse_rate_under_plan(cust_df: pd.DataFrame, plan_name: str) -> float:
    plan = PLAN_LIMITS[plan_name]
    g = cust_df.sort_values("date")
    flags = g.apply(lambda r: month_overuse(r, plan), axis=1)
    return float(flags.mean()) if len(flags) else 0.0

def evaluate_plan(
    cust_df: pd.DataFrame,
    plan_name: str,
    increase_pct: float = 0.25,
) -> dict:
    bills = simulate_monthly_bills_under_plan(cust_df, plan_name)
    metrics = unexpected_bill_increase_metrics(bills, increase_pct=increase_pct)
    overuse_rate = overuse_rate_under_plan(cust_df, plan_name)

    return {
        "plan": plan_name,
        "avg_bill_eur": round(metrics["avg_bill"], 2),
        "bill_std_eur": round(metrics["std_bill"], 2),
        "unexpected_increase_rate": round(metrics["unexpected_increase_rate"], 3),
        "unexpected_increase_count": int(metrics["unexpected_increase_count"]),
        "overuse_rate": round(overuse_rate, 3),
    }

def evaluate_before_after(
    cust_df: pd.DataFrame,
    current_plan: str,
    recommended_plan: str,
    increase_pct: float = 0.25,
) -> pd.DataFrame:
    before = evaluate_plan(cust_df, current_plan, increase_pct=increase_pct)
    after = evaluate_plan(cust_df, recommended_plan, increase_pct=increase_pct)

    out = pd.DataFrame([before, after])

    delta = {
        "plan": "Delta (After - Before)",
        "avg_bill_eur": round(after["avg_bill_eur"] - before["avg_bill_eur"], 2),
        "bill_std_eur": round(after["bill_std_eur"] - before["bill_std_eur"], 2),
        "unexpected_increase_rate": round(after["unexpected_increase_rate"] - before["unexpected_increase_rate"], 3),
        "unexpected_increase_count": int(after["unexpected_increase_count"] - before["unexpected_increase_count"]),
        "overuse_rate": round(after["overuse_rate"] - before["overuse_rate"], 3),
    }

    return pd.concat([out, pd.DataFrame([delta])], ignore_index=True)
