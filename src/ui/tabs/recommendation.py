import pandas as pd
import numpy as np

from src.ui.tabs.plans import PLAN_LIMITS, COSTS

def expected_usage_last_months(cust_df: pd.DataFrame, months: int = 6) -> dict:
    g = cust_df.sort_values("date").tail(months)
    return {
        "data_usage_mb": float(g["data_usage_mb"].mean()),
        "voice_minutes": float(g["voice_minutes"].mean()),
        "sms_count": float(g["sms_count"].mean()),
        "roaming_data_mb": float(g["roaming_data_mb"].mean()),
        "roaming_minutes": float(g["roaming_minutes"].mean()),
    }

def simulate_bill(usage: dict, plan: dict) -> dict:
    base = plan["base_price_eur"]

    extra_data = max(usage["data_usage_mb"] - plan["data_limit_mb"], 0) * COSTS["extra_data_per_mb"]
    extra_voice = max(usage["voice_minutes"] - plan["voice_limit_min"], 0) * COSTS["extra_voice_per_min"]
    extra_sms = max(usage["sms_count"] - plan["sms_limit"], 0) * COSTS["extra_sms_per_unit"]

    extra_roam_mb = max(usage["roaming_data_mb"] - plan["roaming_limit_mb"], 0) * COSTS["extra_roaming_mb"]
    extra_roam_min = max(usage["roaming_minutes"] - plan["roaming_limit_min"], 0) * COSTS["extra_roaming_min"]

    total = base + extra_data + extra_voice + extra_sms + extra_roam_mb + extra_roam_min
    overusage = extra_data + extra_voice + extra_sms + extra_roam_mb + extra_roam_min

    return {
        "expected_bill_eur": float(round(total, 2)),
        "expected_overusage_eur": float(round(overusage, 2)),
        "base_price_eur": float(base),
    }

def recommend_plans(cust_df: pd.DataFrame, months: int = 6):
    usage = expected_usage_last_months(cust_df, months=months)

    rows = []
    for plan_name, plan in PLAN_LIMITS.items():
        sim = simulate_bill(usage, plan)
        rows.append({"plan": plan_name, **sim})

    ranked = (
        pd.DataFrame(rows)
        .sort_values(["expected_bill_eur", "expected_overusage_eur"], ascending=True)
        .reset_index(drop=True)
    )
    return ranked, usage

def compute_overusage(usage: dict, plan: dict) -> dict:
    return {
        "data_over_mb": max(usage["data_usage_mb"] - plan["data_limit_mb"], 0),
        "voice_over_min": max(usage["voice_minutes"] - plan["voice_limit_min"], 0),
        "sms_over": max(usage["sms_count"] - plan["sms_limit"], 0),
        "roam_data_over_mb": max(usage["roaming_data_mb"] - plan["roaming_limit_mb"], 0),
        "roam_min_over": max(usage["roaming_minutes"] - plan["roaming_limit_min"], 0),
    }

def compute_underuse(usage: dict, plan: dict) -> dict:
    # how much of plan is unused (only meaningful if usage is below limit)
    return {
        "data_unused_mb": max(plan["data_limit_mb"] - usage["data_usage_mb"], 0),
        "voice_unused_min": max(plan["voice_limit_min"] - usage["voice_minutes"], 0),
        "sms_unused": max(plan["sms_limit"] - usage["sms_count"], 0),
        "roam_data_unused_mb": max(plan["roaming_limit_mb"] - usage["roaming_data_mb"], 0),
        "roam_min_unused": max(plan["roaming_limit_min"] - usage["roaming_minutes"], 0),
    }

def explain_recommendation(current_plan_name: str, recommended_plan_name: str, usage: dict) -> list[str]:
    cur = PLAN_LIMITS[current_plan_name]
    rec = PLAN_LIMITS[recommended_plan_name]

    cur_bill = simulate_bill(usage, cur)["expected_bill_eur"]
    rec_bill = simulate_bill(usage, rec)["expected_bill_eur"]

    cur_over = compute_overusage(usage, cur)
    cur_under = compute_underuse(usage, cur)

    bullets = []

    #Overuse reasons (strongest)
    if cur_over["data_over_mb"] > 0:
        bullets.append(f"Data usage exceeds current plan by ~{cur_over['data_over_mb']:.0f} MB/month.")
    if cur_over["voice_over_min"] > 0:
        bullets.append(f"Voice usage exceeds current plan by ~{cur_over['voice_over_min']:.0f} min/month.")
    if cur_over["sms_over"] > 0:
        bullets.append(f"SMS usage exceeds current plan by ~{cur_over['sms_over']:.0f} messages/month.")
    if cur_over["roam_data_over_mb"] > 0:
        bullets.append(f"Roaming data exceeds current plan by ~{cur_over['roam_data_over_mb']:.0f} MB/month (expensive overusage).")
    if cur_over["roam_min_over"] > 0:
        bullets.append(f"Roaming minutes exceed current plan by ~{cur_over['roam_min_over']:.0f} min/month (expensive overusage).")

    #overpay reason (only if not oversing anything)
    if len(bullets) == 0:
        if cur_under["data_unused_mb"] > 0.6 * cur["data_limit_mb"]:
            bullets.append("Current plan data allowance is much higher than typical usage (likely overpaying).")
        if cur_under["voice_unused_min"] > 0.6 * cur["voice_limit_min"]:
            bullets.append("Current plan voice allowance is much higher than typical usage (likely overpaying).")
        if cur_under["roam_data_unused_mb"] > 0.6 * cur["roaming_limit_mb"]:
            bullets.append("Current plan roaming allowance is much higher than typical usage (likely overpaying).")

    # Bill comparison
    diff = round(cur_bill - rec_bill, 2)
    if diff > 0:
        bullets.append(f"Estimated monthly cost decreases by ~€{diff:.2f} compared to the current plan.")
    elif diff < 0:
        bullets.append(f"Estimated monthly cost increases by ~€{abs(diff):.2f}, but reduces expected overusage risk.")
    else:
        bullets.append("Estimated monthly cost is similar, but the recommended plan better matches limits to usage.")

    #What the recomended plan improves
    if cur_over["data_over_mb"] > 0 and rec["data_limit_mb"] > cur["data_limit_mb"]:
        bullets.append("Recommended plan provides higher data allowance to reduce overusage charges.")
    if cur_over["roam_data_over_mb"] > 0 and rec["roaming_limit_mb"] > cur["roaming_limit_mb"]:
        bullets.append("Recommended plan provides higher roaming data allowance to reduce roaming overusage charges.")
    if cur_over["roam_min_over"] > 0 and rec["roaming_limit_min"] > cur["roaming_limit_min"]:
        bullets.append("Recommended plan provides higher roaming minutes allowance to reduce roaming call charges.")

    return bullets

def build_mismatch_table(usage: dict, current_plan_name: str, recommended_plan_name: str) -> pd.DataFrame:
    cur = PLAN_LIMITS[current_plan_name]
    rec = PLAN_LIMITS[recommended_plan_name]

    rows = [
        ("Data (MB)", usage["data_usage_mb"], cur["data_limit_mb"], rec["data_limit_mb"]),
        ("Voice (min)", usage["voice_minutes"], cur["voice_limit_min"], rec["voice_limit_min"]),
        ("SMS", usage["sms_count"], cur["sms_limit"], rec["sms_limit"]),
        ("Roaming data (MB)", usage["roaming_data_mb"], cur["roaming_limit_mb"], rec["roaming_limit_mb"]),
        ("Roaming minutes", usage["roaming_minutes"], cur["roaming_limit_min"], rec["roaming_limit_min"]),
    ]

    out = pd.DataFrame(rows, columns=["Metric", "Expected usage", "Current limit", "Recommended limit"])

    # Add status columns
    out["Current status"] = out.apply(
        lambda r: "OVER" if r["Expected usage"] > r["Current limit"] else "OK",
        axis=1
    )
    out["Recommended status"] = out.apply(
        lambda r: "OVER" if r["Expected usage"] > r["Recommended limit"] else "OK",
        axis=1
    )

    #Round for better display
    out["Expected usage"] = out["Expected usage"].round(1)
    return out

def recommend_plans_from_usage(usage: dict) -> pd.DataFrame:
    rows = []
    for plan_name, plan in PLAN_LIMITS.items():
        sim = simulate_bill(usage, plan)
        rows.append({"plan": plan_name, **sim})

    ranked = (
        pd.DataFrame(rows)
        .sort_values(["expected_bill_eur", "expected_overusage_eur"], ascending=True)
        .reset_index(drop=True)
    )
    return ranked

def simulate_bill_from_row(row: pd.Series, plan: dict) -> float:
    usage = {
        "data_usage_mb": float(row["data_usage_mb"]),
        "voice_minutes": float(row["voice_minutes"]),
        "sms_count": float(row["sms_count"]),
        "roaming_data_mb": float(row["roaming_data_mb"]),
        "roaming_minutes": float(row["roaming_minutes"]),
    }
    return simulate_bill(usage, plan)["expected_bill_eur"]

def simulate_monthly_bills(cust_df: pd.DataFrame, plan_name: str) -> pd.Series:
    plan = PLAN_LIMITS[plan_name]
    g = cust_df.sort_values("date")
    bills = g.apply(lambda r: simulate_bill_from_row(r, plan), axis=1)
    bills.index = g["date"].values
    return bills

def unexpected_bill_increase_metrics(
    bills: pd.Series,
    increase_pct: float = 0.25,
) -> dict:
    b = bills.values
    if len(b) < 2:
        return {
            "avg_bill": float(b.mean()) if len(b) else 0.0,
            "std_bill": 0.0,
            "unexpected_increase_rate": 0.0,
            "unexpected_increase_count": 0,
        }

    prev = b[:-1]
    curr = b[1:]

    pct_increase = (curr - prev) / np.maximum(prev, 1e-6)
    unexpected = pct_increase > increase_pct

    return {
        "avg_bill": float(np.mean(b)),
        "std_bill": float(np.std(b)),
        "unexpected_increase_rate": float(np.mean(unexpected)),
        "unexpected_increase_count": int(np.sum(unexpected)),
    }

def recommend_plans_churn_rule_based(
    cust_df: pd.DataFrame,
    increase_pct: float = 0.25,
    max_unexpected_increase_rate: float = 0.10,
    min_months: int = 3,
) -> pd.DataFrame:
    rows = []

    for plan_name in PLAN_LIMITS.keys():
        bills = simulate_monthly_bills(cust_df, plan_name)

        if len(bills) < min_months:
            metrics = {
                "avg_bill": float(np.mean(bills)) if len(bills) else 0.0,
                "std_bill": 0.0,
                "unexpected_increase_rate": None,
                "unexpected_increase_count": 0,
            }
        else:
            m = unexpected_bill_increase_metrics(bills, increase_pct=increase_pct)
            metrics = m

        rows.append({
            "plan": plan_name,
            "avg_bill_eur": round(metrics["avg_bill"], 2),
            "bill_std_eur": round(metrics["std_bill"], 2),
            "unexpected_increase_rate": (
                None if metrics["unexpected_increase_rate"] is None
                else round(metrics["unexpected_increase_rate"], 3)
            ),
            "unexpected_increase_count": metrics["unexpected_increase_count"],
        })

    df = pd.DataFrame(rows)

    df["stable"] = df["unexpected_increase_rate"].apply(
        lambda x: (x is not None) and (x <= max_unexpected_increase_rate)
    )

    stable_df = df[df["stable"]].copy()

    if len(stable_df) > 0:
        ranked = stable_df.sort_values(
            ["avg_bill_eur", "bill_std_eur", "unexpected_increase_count"],
            ascending=True
        ).reset_index(drop=True)

        unstable_df = df[~df["stable"]].sort_values(
            ["unexpected_increase_rate", "avg_bill_eur"],
            ascending=True
        )

        return pd.concat([ranked, unstable_df], ignore_index=True)

    # fallback if all plans are not stable
    df["_rate_sort"] = df["unexpected_increase_rate"].apply(
        lambda x: x if x is not None else float("inf")
    )

    return (
        df.sort_values(
            ["_rate_sort", "avg_bill_eur", "bill_std_eur"],
            ascending=True
        )
        .drop(columns=["_rate_sort"])
        .reset_index(drop=True)
    )
