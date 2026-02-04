import numpy as np
import pandas as pd
import streamlit as st


def make_monthly_series(df_in: pd.DataFrame, customer_ids_set: set) -> pd.Series:
    tmp = df_in[df_in["customer_id"].isin(customer_ids_set)].copy()
    tmp["date"] = pd.to_datetime(tmp["date"])
    tmp["month"] = tmp["date"].dt.to_period("M").dt.to_timestamp()  # month start
    s = tmp.groupby("month")["data_usage_mb"].mean().sort_index()
    return s


def filter_years(s: pd.Series, years: list[int]) -> pd.Series:
    return s[s.index.year.isin(years)]


def fit_seasonal_trend_model(y: pd.Series):
    y = y.dropna()
    if len(y) < 6:
        return None

    t = np.arange(len(y), dtype=float)
    X = np.column_stack(
        [
            np.ones_like(t),
            t,
            np.sin(2 * np.pi * t / 12.0),
            np.cos(2 * np.pi * t / 12.0),
        ]
    )
    beta, *_ = np.linalg.lstsq(X, y.values, rcond=None)
    return {"beta": beta, "n": len(y)}


def predict_seasonal_trend(model, steps: int) -> np.ndarray:
    n = model["n"]
    t_future = np.arange(n, n + steps, dtype=float)
    Xf = np.column_stack(
        [
            np.ones_like(t_future),
            t_future,
            np.sin(2 * np.pi * t_future / 12.0),
            np.cos(2 * np.pi * t_future / 12.0),
        ]
    )
    return Xf @ model["beta"]


def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    err = y_true - y_pred
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err**2)))
    return {"MAE": mae, "RMSE": rmse}


def render_prediction_tab(df: pd.DataFrame, centers: np.ndarray | None) -> None:
    st.subheader("Cluster data-usage prediction (and whether clustering helps)",
                 help=("The prediction uses a regression-based time-series forecasting model. "
                        "Monthly data usage is modeled as a combination of a linear trend and a "
                        "12-month seasonal pattern using sine and cosine functions. "
                        "The model is trained on historical data (2022–2023) and used to forecast "
                        "monthly usage for 2024. "
                        "The same model is applied in two ways: using only cluster-specific data "
                        "and using all customers (global), allowing a fair comparison of whether "
                        "behavior-based clustering improves prediction accuracy."
                 )
                )

    if centers is None:
        st.info("No saved cluster centers found yet. Run DTW once to generate clusters/centers.")
        return

    if "customer_ids" not in st.session_state or "labels" not in st.session_state:
        st.error("Clustering results not found. Please run clustering first (Cluster View tab).")
        return

    customer_ids = st.session_state["customer_ids"]
    labels = st.session_state["labels"]

    cid_to_cluster = dict(zip(customer_ids, labels))

    # UI controls
    k_centers = centers.shape[0]
    selected_cluster = st.selectbox(
        "Select cluster",
        options=list(range(k_centers)),
        format_func=lambda x: f"Cluster {x}",
        key="pred_selected_cluster",
    )

    df_local = df.copy()
    df_local["date"] = pd.to_datetime(df_local["date"])
    years_available = sorted(df_local["date"].dt.year.unique().tolist())

    # Default: train 2022+2023, predict 2024
    default_train = [y for y in [2022, 2023] if y in years_available]
    if 2024 in years_available:
        default_target = 2024
    else:
        candidates = [y for y in years_available if y not in default_train]
        default_target = candidates[-1] if candidates else years_available[-1]

    train_years = st.multiselect(
        "Training years (history used to learn the pattern)",
        options=years_available,
        default=default_train if default_train else years_available[:1],
        key="pred_train_years",
    )
    target_year = st.selectbox(
        "Target year to predict (we’ll compare against real data for this year)",
        options=years_available,
        index=years_available.index(default_target) if default_target in years_available else 0,
        key="pred_target_year",
    )

    if not train_years:
        st.warning("Pick at least one training year.")
        return
    if target_year in train_years:
        st.warning("Target year should not be inside training years (otherwise you’re predicting data you trained on).")
        return

    # Build the series
    cluster_customers = {cid for cid, c in cid_to_cluster.items() if c == selected_cluster}
    if len(cluster_customers) == 0:
        st.error("No customers found for this cluster.")
        return

    all_customers = set(df_local["customer_id"].unique().tolist())

    cluster_monthly = make_monthly_series(df_local, cluster_customers)
    global_monthly = make_monthly_series(df_local, all_customers)

    cluster_train = filter_years(cluster_monthly, train_years)
    global_train = filter_years(global_monthly, train_years)

    cluster_real_target = filter_years(cluster_monthly, [target_year])
    if len(cluster_real_target) == 0:
        st.error(f"No real data found for target year {target_year} for this cluster.")
        return

    steps = len(cluster_real_target)

    # Fit and predict
    model_cluster = fit_seasonal_trend_model(cluster_train)
    model_global = fit_seasonal_trend_model(global_train)

    if model_cluster is None or model_global is None:
        st.error("Not enough training data to fit one of the models. Add more training years.")
        return

    pred_cluster = predict_seasonal_trend(model_cluster, steps=steps)
    pred_global = predict_seasonal_trend(model_global, steps=steps)

    y_true = cluster_real_target.values.astype(float)

    m_cluster = metrics(y_true, pred_cluster)
    m_global = metrics(y_true, pred_global)

    #Display
    plot_df = pd.DataFrame(
        {
            "Real (cluster)": y_true,
            "Prediction Cluster-only": pred_cluster,
            "Prediction Global (no clustering)": pred_global,
        },
        index=cluster_real_target.index,
    )
    plot_df.index.name = "Month"

    st.line_chart(plot_df)

    st.subheader(
        "Prediction Error Metrics",
        help=(
            "MAE measures the average monthly prediction error, "
            "while RMSE penalizes large errors more strongly. "
            "Lower values indicate better predictions. "
            "Comparing cluster-only and global results shows whether clustering helps."
        )
    )

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Cluster-only MAE", f"{m_cluster['MAE']:.2f}")
        st.metric("Cluster-only RMSE", f"{m_cluster['RMSE']:.2f}")
    with col2:
        st.metric("Global MAE", f"{m_global['MAE']:.2f}")
        st.metric("Global RMSE", f"{m_global['RMSE']:.2f}")

    winner = "Cluster-only" if m_cluster["RMSE"] < m_global["RMSE"] else "Global"
    st.success(f"Better (lower RMSE): **{winner}**")

    st.caption(
        "Forecast model: linear trend + 12-month seasonality (sin/cos). "
        "Cluster only method trains on the selected cluster’s monthly average usage; "
        "Global method trains on all customers’ monthly average usage (ignoring clusters)."
    )
