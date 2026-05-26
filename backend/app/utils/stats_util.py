import numpy as np

def correlation(x: list[float], y: list[float]) -> float:
    return float(np.corrcoef(x, y)[0, 1])

def covariance(x: list[float], y: list[float]) -> float:
    return float(np.cov(x, y)[0, 1])

def percentile(data: list[float], p: float) -> float:
    return float(np.percentile(data, p))
