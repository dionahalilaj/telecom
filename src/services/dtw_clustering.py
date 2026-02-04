from tslearn.clustering import TimeSeriesKMeans

def dtw_cluster(time_series_data, k=6):
    model = TimeSeriesKMeans(
        n_clusters=k,
        metric="dtw",
        max_iter=10,
        random_state=42
    )
    labels = model.fit_predict(time_series_data)
    return labels, model
