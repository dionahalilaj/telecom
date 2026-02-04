import numpy as np
from tslearn.preprocessing import TimeSeriesScalerMeanVariance

def build_time_series(df):
    time_series_list = []
    customer_ids = []

    for customer_id, customer_df in df.groupby("customer_id"):
        # Ensure chronological order
        customer_df = customer_df.sort_values("date")

        customer_time_series = customer_df[[
            "data_usage_mb",
            "voice_minutes",
            "roaming_data_mb",
            "bill_amount_eur"
        ]].values

        time_series_list.append(customer_time_series)
        customer_ids.append(customer_id)

    #Shape: (customers, time_steps, features)
    time_series_data = np.array(time_series_list)

    #normalize each customers time series (mean=0, variance=1)
    time_series_data = (
        TimeSeriesScalerMeanVariance()
        .fit_transform(time_series_data)
    )

    return time_series_data, customer_ids
