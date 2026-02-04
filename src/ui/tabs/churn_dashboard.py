import pandas as pd
import numpy as np

def unexpected_bill_increase_rate_for_customer(
    cust_df: pd.DataFrame,
    increase_pct: float = 0.25
) -> float:
    g = cust_df.sort_values("date")
    bills = g["bill_amount_eur"].to_numpy()

    if len(bills) < 2:
        return 0.0

    prev = bills[:-1]
    curr = bills[1:]
    pct_increase = (curr - prev) / np.maximum(prev, 1e-6)

    unexpected = pct_increase > increase_pct
    return float(np.mean(unexpected))


def cluster_churn_dashboard(
    df: pd.DataFrame,
    cluster_col: str = "dtw_cluster",
    increase_pct: float = 0.25
) -> pd.DataFrame:
    #customer-level churn flag
    churn_by_customer = (
        df.groupby("customer_id")["churn_event"]
        .max()
        .rename("customer_churned")
        .reset_index()
    )

    # Customer -> cluster mapping
    cust_cluster = (
        df[["customer_id", cluster_col]]
        .drop_duplicates()
        .merge(churn_by_customer, on="customer_id", how="left")
    )

    # Customer level unexpected bill incrase rate (uses actual bill series)
    metrics = []
    for cid, g in df.groupby("customer_id"):
        metrics.append({
            "customer_id": cid,
            "unexpected_increase_rate": unexpected_bill_increase_rate_for_customer(
                g, increase_pct=increase_pct
            ),
            "avg_bill": float(g["bill_amount_eur"].mean()),
            "overuse_rate": float(g["overuse_flag"].mean()),
        })
    metrics = pd.DataFrame(metrics)

    cust_cluster = cust_cluster.merge(metrics, on="customer_id", how="left")

    # Aggregat to cluster level
    out = (
        cust_cluster
        .groupby(cluster_col)
        .agg(
            customers=("customer_id", "nunique"),
            churn_rate=("customer_churned", "mean"),
            avg_bill=("avg_bill", "mean"),
            avg_overuse_rate=("overuse_rate", "mean"),
            avg_unexpected_increase_rate=("unexpected_increase_rate", "mean"),
            pct_customers_with_unexpected_increase=("unexpected_increase_rate", lambda x: float(np.mean(x > 0.0))),
        )
        .reset_index()
        .rename(columns={cluster_col: "cluster"})
    )

    # formating columns
    out["churn_rate_pct"] = (out["churn_rate"] * 100).round(2)
    out["avg_overuse_pct"] = (out["avg_overuse_rate"] * 100).round(2)
    out["avg_unexpected_increase_rate"] = out["avg_unexpected_increase_rate"].round(3)
    out["pct_customers_with_unexpected_increase"] = (out["pct_customers_with_unexpected_increase"] * 100).round(2)
    out["avg_bill"] = out["avg_bill"].round(2)

    # Rank helpers: highest churn first, then most unexpected increases
    out = out.sort_values(
        ["churn_rate", "avg_unexpected_increase_rate"],
        ascending=False
    ).reset_index(drop=True)

    return out
