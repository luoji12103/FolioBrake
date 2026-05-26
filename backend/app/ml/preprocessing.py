import numpy as np

def normalize(data: list[float]) -> list[float]:
    min_val = min(data)
    max_val = max(data)
    range_val = max_val - min_val
    return [(x - min_val) / range_val if range_val > 0 else 0 for x in data]

def standardize(data: list[float]) -> list[float]:
    mean = np.mean(data)
    std = np.std(data)
    return [(x - mean) / std if std > 0 else 0 for x in data]

def handle_missing(data: list[float | None], strategy: str = "mean") -> list[float]:
    if strategy == "mean":
        fill_value = np.mean([x for x in data if x is not None])
    elif strategy == "median":
        fill_value = np.median([x for x in data if x is not None])
    else:
        fill_value = 0.0
    return [x if x is not None else fill_value for x in data]
