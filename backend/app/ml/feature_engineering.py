import numpy as np

def create_lag_features(data: list[float], n_lags: int = 5) -> list[list[float]]:
    features = []
    for i in range(n_lags, len(data)):
        features.append([data[i - j] for j in range(1, n_lags + 1)])
    return features

def create_rolling_features(data: list[float], window: int = 10) -> list[list[float]]:
    features = []
    for i in range(window, len(data)):
        window_data = data[i - window:i]
        features.append([
            np.mean(window_data),
            np.std(window_data),
            np.min(window_data),
            np.max(window_data),
        ])
    return features
